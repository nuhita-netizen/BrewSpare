from __future__ import annotations

from datetime import date, datetime, timedelta
import math
import random
from sqlalchemy import select
from .database import Base, engine, SessionLocal
from .models import Plant, Asset, SparePart, AssetSparePart, PartUsage, SensorReading, MaintenanceEvent

random.seed(42)

ASSETS = [
    ("RM-01","Raw Material Handling","Raw Material","Material Handling","High",86,28,65000,25,"YELLOW",80,220),
    ("MX-01","Mash Mixer","Brewing","Mixer","High",93,18,85000,38,"GREEN",220,220),
    ("BK-01","Boiling Kettle","Brewing","Kettle","High",82,34,95000,20,"YELLOW",370,220),
    ("PM-02","Wort Transfer Pump","Brewing","Pump","Critical",72,58,140000,16,"YELLOW",515,220),
    ("HX-01","Plate Heat Exchanger","Brewing","Heat Exchanger","Critical",90,22,160000,32,"GREEN",660,220),
    ("FV-04","Fermentation Vessel 04","Fermentation","Vessel","High",94,15,90000,45,"GREEN",805,220),
    ("GC-01","Glycol Chiller","Utilities","Chiller","Critical",63,68,200000,12,"ORANGE",950,220),
    ("CIP-01","CIP Skid","Sanitation","CIP","Critical",69,62,120000,14,"ORANGE",1095,220),
    ("FLT-01","Filtration Unit","Filtration","Filter","High",76,49,110000,22,"ORANGE",1240,220),
    ("FL-01","Bottle Filler","Packaging","Filler","Critical",32,86,240000,18,"RED",1385,220),
    ("CP-01","Bottle Capper","Packaging","Capper","High",71,55,130000,24,"YELLOW",1530,220),
    ("CV-01","Packaging Conveyor","Packaging","Conveyor","High",88,26,110000,38,"GREEN",1675,220),
    ("AC-01","Air Compressor","Utilities","Compressor","Critical",61,64,180000,15,"ORANGE",950,390),
    ("PKG-01","Packaging Robot","Packaging","Robot","High",91,20,150000,40,"GREEN",1820,220),
]

PARTS = [
    ("SP-001","Mechanical Pump Seal","Pump",3,0,2,7500,2.5,35,0.91,24,10,"BrewTech Components","Limited"),
    ("SP-002","Pump Bearing","Bearing",6,0,2,4200,1.2,21,0.94,60,8,"BrewTech Components","Available"),
    ("SP-003","Food Grade EPDM Gasket","Seal",20,2,6,850,7,14,0.95,24,11,"HygienicFlow Systems","Available"),
    ("SP-004","Temperature Sensor","Sensor",2,0,2,9500,0.8,45,0.82,60,14,"SensorPro Industrial","Limited"),
    ("SP-005","Pressure Transmitter","Sensor",4,1,1,18500,0.3,60,0.81,60,16,"SensorPro Industrial","Limited"),
    ("SP-006","Solenoid Valve","Valve",5,0,2,6200,1.5,30,0.91,48,9,"HygienicFlow Systems","Available"),
    ("SP-007","Filter Cartridge","Filter",42,4,12,1100,18,10,0.96,18,7,"BrewFilter","Available"),
    ("SP-008","Conveyor Belt","Belt",1,0,1,24000,0.6,50,0.78,36,12,"MotionDrive India","Limited"),
    ("SP-009","Filler Nozzle","Filling",8,1,3,5500,3,30,0.91,48,8,"PackLine Spares","Available"),
    ("SP-010","Filler Valve Seal Kit","Filling",4,0,4,3800,4.5,40,0.84,18,10,"PackLine Spares","Limited"),
    ("SP-011","Capper Chuck","Capping",3,0,1,14500,1,35,0.90,60,12,"PackLine Spares","Available"),
    ("SP-012","VFD Module","Electrical",1,0,1,38000,0.2,75,0.76,72,18,"MotionDrive India","Backorder Risk"),
    ("SP-013","Glycol Pump Motor","Motor",1,0,1,62000,0.25,60,0.79,72,14,"CoolingTech","Limited"),
    ("SP-014","Compressor Air Filter","Filter",12,1,4,2800,2,15,0.96,36,7,"AirServe","Available"),
    ("SP-015","CIP Spray Nozzle","CIP",18,0,2,4600,0.4,20,0.95,60,22,"HygienicFlow Systems","Available"),
]

LINKS = {
    "PM-02":[("SP-001","Critical",1),("SP-002","High",1),("SP-012","High",1)],
    "HX-01":[("SP-003","High",2),("SP-004","High",1)],
    "FV-04":[("SP-003","Medium",1),("SP-005","High",1)],
    "GC-01":[("SP-013","Critical",1),("SP-004","Medium",1)],
    "CIP-01":[("SP-006","High",1),("SP-015","Medium",2),("SP-003","High",2)],
    "FLT-01":[("SP-007","Critical",4),("SP-004","Medium",1)],
    "FL-01":[("SP-010","Critical",2),("SP-009","High",2),("SP-006","High",1)],
    "CP-01":[("SP-011","Critical",1),("SP-006","Medium",1)],
    "CV-01":[("SP-008","Critical",1),("SP-012","High",1)],
    "AC-01":[("SP-014","Critical",2),("SP-012","Medium",1)],
}


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.scalar(select(Plant).where(Plant.code == "RSB-01"))
        if existing:
            return
        plant = Plant(name="RiverStone Brewery - Plant 01", code="RSB-01", carrying_rate=0.22)
        db.add(plant); db.flush()
        assets = {}
        for a in ASSETS:
            obj = Asset(plant_id=plant.id, asset_code=a[0], name=a[1], area=a[2], asset_type=a[3], criticality=a[4], health_score=a[5], risk_score=a[6], downtime_cost_per_hour=a[7], next_maintenance_days=a[8], status=a[9], x=a[10], y=a[11])
            db.add(obj); db.flush(); assets[a[0]]=obj
        parts = {}
        for p in PARTS:
            obj = SparePart(part_code=p[0], name=p[1], category=p[2], current_stock=p[3], reserved_stock=p[4], safety_stock=p[5], unit_cost=p[6], avg_monthly_usage=p[7], lead_time_days=p[8], supplier_reliability=p[9], shelf_life_months=p[10], inventory_age_months=p[11], supplier_name=p[12], supplier_status=p[13], last_used_date=date.today()-timedelta(days=random.randint(10,220)))
            db.add(obj); db.flush(); parts[p[0]]=obj
        for acode, links in LINKS.items():
            for pcode, importance, qty in links:
                db.add(AssetSparePart(asset_id=assets[acode].id, part_id=parts[pcode].id, importance=importance, qty_per_service=qty))
        # 12 months usage; emphasize rising SP-010 demand
        sp010 = [3,3,4,4,4,5,5,6,6,6,7,7]
        for idx, p in enumerate(PARTS):
            part = parts[p[0]]
            for m in range(12):
                usage_date = (date.today().replace(day=1) - timedelta(days=30*(11-m)))
                if p[0] == "SP-010": qty = sp010[m]
                elif p[0] == "SP-015": qty = 1 if m in (2,8,11) else 0
                else:
                    base = max(0, p[7])
                    qty = max(0, round(random.gauss(base, max(.4, base*.2)), 1))
                db.add(PartUsage(part_id=part.id, usage_date=usage_date, quantity=qty))
        # Sensor history (14 days, 6-hourly), FL-01 rising anomaly
        now = datetime.utcnow()
        for asset in assets.values():
            for i in range(56):
                ts = now - timedelta(hours=6*(55-i))
                frac = i/55
                vib_base = 3.0 + asset.risk_score/40
                temp_base = 52 + asset.risk_score/4
                pressure = 4.6 + random.gauss(0,0.2)
                out = 17000 + random.gauss(0,650)
                if asset.asset_code == "FL-01":
                    vib = 4.8 + 3.3*frac + random.gauss(0,0.22)
                    temp = 61 + 6*frac + random.gauss(0,0.8)
                    pressure = 5.0 + .6*frac + random.gauss(0,.12)
                    out = 18100 - 700*frac + random.gauss(0,250)
                else:
                    vib = vib_base + random.gauss(0,.35)
                    temp = temp_base + random.gauss(0,1.3)
                db.add(SensorReading(asset_id=asset.id, ts=ts, temperature=round(temp,1), vibration=round(vib,2), pressure=round(pressure,2), output_rate=round(out,0)))
        # Maintenance events
        events = [
            ("PM-02",110,"Corrective","Seal leakage","SP-001",1,2.0,18500),
            ("GC-01",210,"Corrective","Pump overheating","SP-013",1,5.0,88000),
            ("CV-01",150,"Corrective","Belt tracking failure","SP-008",1,2.0,36000),
            ("AC-01",72,"Corrective","Restricted airflow","SP-014",2,2.5,17000),
        ]
        for offset in [330,280,235,185,145,100,55]:
            events.append(("FL-01",offset,"Corrective","Filler valve seal leakage","SP-010",2,1.4+random.random(),21000+random.randint(0,10000)))
        for acode, offset, etype, problem, pcode, qty, downtime, cost in events:
            db.add(MaintenanceEvent(asset_id=assets[acode].id, event_date=date.today()-timedelta(days=offset), event_type=etype, problem=problem, part_code=pcode, quantity_used=qty, downtime_hours=downtime, maintenance_cost=cost))
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
    print("BrewSpare demo data ready.")
