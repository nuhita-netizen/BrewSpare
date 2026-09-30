from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Asset, SparePart, Plant, SensorReading, ProcurementPlan
from .analytics import asset_detail, availability_for
from .seed import seed

app = FastAPI(title="BrewSpare API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    seed()

@app.get("/health")
def health():
    return {"status":"ok","service":"BrewSpare API"}

@app.get("/api/plant-summary")
def plant_summary(db: Session = Depends(get_db)):
    plant = db.scalar(select(Plant).limit(1))
    assets = db.scalars(select(Asset).order_by(Asset.x)).all()
    parts = db.scalars(select(SparePart)).all()
    av = [availability_for(db,p) for p in parts]
    counts = {s: sum(1 for a in assets if a.status == s) for s in ["GREEN","YELLOW","ORANGE","RED"]}
    inventory_value = sum(x["inventory_value"] for x in av)
    carrying = sum(x["annual_carrying_cost"] for x in av)
    avoidable = sum(x["inventory_value"] for x in av if x["state"] in {"EXCESS_INVENTORY","SHELF_LIFE_RISK"})
    downtime_exposure = sum(a.downtime_cost_per_hour * 2 for a in assets if a.status in {"ORANGE","RED"})
    return {
        "plant": {"name": plant.name, "code": plant.code},
        "counts": counts,
        "plant_availability": round(100 - sum(a.risk_score for a in assets)/(len(assets)*12),1),
        "potential_downtime_exposure": round(downtime_exposure,0),
        "inventory_value": round(inventory_value,0),
        "annual_carrying_cost": round(carrying,0),
        "avoidable_inventory_value": round(avoidable,0),
        "assets": [{"asset_code":a.asset_code,"name":a.name,"area":a.area,"status":a.status,"risk_score":a.risk_score,"health_score":a.health_score,"x":a.x,"y":a.y} for a in assets],
        "critical_assets": [{"asset_code":a.asset_code,"name":a.name,"status":a.status,"risk_score":a.risk_score,"health_score":a.health_score} for a in sorted(assets,key=lambda x:x.risk_score,reverse=True)[:4]],
        "parts_to_order": sorted([x for x in av if x["state"] in {"AVAILABILITY_RISK","ORDER_SOON"}], key=lambda x:(x["state"]!="AVAILABILITY_RISK",-x["availability_gap_days"]))[:5]
    }

@app.get("/api/assets")
def assets(db: Session = Depends(get_db)):
    rows = db.scalars(select(Asset).order_by(Asset.asset_code)).all()
    return [asset_detail(db,a) for a in rows]

@app.get("/api/assets/{asset_code}")
def asset(asset_code: str, db: Session = Depends(get_db)):
    row = db.scalar(select(Asset).where(Asset.asset_code == asset_code))
    if not row: raise HTTPException(404,"Asset not found")
    detail = asset_detail(db,row)
    readings = db.scalars(select(SensorReading).where(SensorReading.asset_id==row.id).order_by(SensorReading.ts.asc()).limit(120)).all()
    detail["sensor_series"] = [{"ts":r.ts.isoformat(),"temperature":r.temperature,"vibration":r.vibration,"pressure":r.pressure,"output_rate":r.output_rate} for r in readings]
    return detail

@app.get("/api/parts")
def parts(db: Session = Depends(get_db)):
    rows = db.scalars(select(SparePart).order_by(SparePart.part_code)).all()
    return [availability_for(db,p) for p in rows]

@app.get("/api/parts/{part_code}")
def part(part_code: str, db: Session = Depends(get_db)):
    p = db.scalar(select(SparePart).where(SparePart.part_code == part_code))
    if not p: raise HTTPException(404,"Part not found")
    out = availability_for(db,p)
    out["category"] = p.category
    out["unit_cost"] = p.unit_cost
    out["supplier_status"] = p.supplier_status
    out["dependencies"] = [{"asset_code":l.asset.asset_code,"asset_name":l.asset.name,"importance":l.importance,"asset_status":l.asset.status} for l in p.asset_links]
    out["usage_history"] = [{"date":u.usage_date.isoformat(),"quantity":u.quantity} for u in sorted(p.usage,key=lambda x:x.usage_date)]
    return out

@app.get("/api/availability")
def availability(db: Session = Depends(get_db)):
    parts = db.scalars(select(SparePart)).all()
    return sorted([availability_for(db,p) for p in parts], key=lambda x:(x["state"] not in {"AVAILABILITY_RISK","ORDER_SOON"}, -x["availability_gap_days"]))

@app.get("/api/maintenance-priorities")
def maintenance_priorities(db: Session = Depends(get_db)):
    assets = db.scalars(select(Asset)).all()
    rows=[]
    for a in assets:
        detail=asset_detail(db,a)
        part_risks=[p for p in detail["parts"] if p["state"] in {"AVAILABILITY_RISK","ORDER_SOON"}]
        score=min(100,round(a.risk_score + (8 if part_risks else 0) + (5 if a.criticality=="Critical" else 0)))
        rows.append({"asset_code":a.asset_code,"name":a.name,"priority_score":score,"status":a.status,"risk_score":a.risk_score,"next_maintenance_days":a.next_maintenance_days,"required_parts":part_risks})
    return sorted(rows,key=lambda x:x["priority_score"],reverse=True)

class ProcureIn(BaseModel):
    part_code: str
    quantity: float
    action: str = "APPROVE"

@app.post("/api/procurement")
def create_procurement(payload: ProcureIn, db: Session = Depends(get_db)):
    p = db.scalar(select(SparePart).where(SparePart.part_code == payload.part_code))
    if not p: raise HTTPException(404,"Part not found")
    av=availability_for(db,p)
    plan=ProcurementPlan(part_code=p.part_code,suggested_qty=av["recommended_order_qty"],approved_qty=payload.quantity,status=payload.action.upper(),reason=f"{av['state']} with {av['availability_gap_days']} day availability gap")
    db.add(plan); db.commit(); db.refresh(plan)
    return {"id":plan.id,"status":plan.status,"part_code":plan.part_code,"approved_qty":plan.approved_qty,"reason":plan.reason}

@app.get("/api/scenario")
def scenario(supplier_delay_days: int = 0, production_increase_pct: int = 0, db: Session = Depends(get_db)):
    parts = db.scalars(select(SparePart)).all()
    base=[availability_for(db,p) for p in parts]
    current=sum(1 for x in base if x["state"]=="AVAILABILITY_RISK")
    affected=[]
    projected=0
    for p,x in zip(parts,base):
        effective_need=max(1,int(x["predicted_need_days"]/(1+production_increase_pct/100)))
        gap=(x["effective_lead_days"]+supplier_delay_days+7)-effective_need
        if gap>0:
            projected+=1
            affected.append({"part_code":p.part_code,"part_name":p.name,"projected_gap_days":gap})
    return {"current_availability_risks":current,"scenario_availability_risks":projected,"supplier_delay_days":supplier_delay_days,"production_increase_pct":production_increase_pct,"affected":sorted(affected,key=lambda a:a["projected_gap_days"],reverse=True)[:10]}

@app.get("/api/ai/brief")
def ai_brief(db: Session = Depends(get_db)):
    summary=plant_summary(db)
    top=summary["critical_assets"][0]
    parts=summary["parts_to_order"]
    return {
        "headline": f"{top['asset_code']} {top['name']} needs attention",
        "summary": f"Risk score is {top['risk_score']} with health at {top['health_score']}%. {len(parts)} spare parts currently need procurement review.",
        "evidence": [f"{p['part_code']} has {p['usable_stock']} usable units vs {p['forecast']['d30']} forecast 30-day demand" for p in parts[:3]],
        "suggested_actions": ["Review FL-01 maintenance history","Review SP-010 procurement window","Check high-risk supplier lead times"],
    }
