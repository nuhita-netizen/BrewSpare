from __future__ import annotations

from datetime import date, timedelta
from math import ceil
from statistics import mean
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Asset, SparePart, PartUsage, SensorReading

STATUS_ORDER = {"GREEN": 0, "YELLOW": 1, "ORANGE": 2, "RED": 3}


def forecast_part(db: Session, part: SparePart) -> dict:
    rows = db.scalars(select(PartUsage).where(PartUsage.part_id == part.id).order_by(PartUsage.usage_date)).all()
    monthly = [r.quantity for r in rows[-6:]]
    baseline = mean(monthly) if monthly else part.avg_monthly_usage
    if len(monthly) >= 3:
        trend = (monthly[-1] - monthly[0]) / max(1, len(monthly) - 1)
    else:
        trend = 0
    next_month = max(0.0, baseline + trend * 1.5)
    d30 = round(next_month, 1)
    d7 = round(d30 * 7 / 30, 1)
    d90 = round(d30 * 3.05, 1)
    low = round(max(0, d30 * 0.82), 1)
    high = round(d30 * 1.18, 1)
    return {"d7": d7, "d30": d30, "d90": d90, "confidence_low": low, "confidence_high": high}


def availability_for(db: Session, part: SparePart) -> dict:
    fc = forecast_part(db, part)
    usable = part.usable_stock
    monthly_rate = max(fc["d30"], 0.1)
    days_cover = usable / monthly_rate * 30
    predicted_need_days = max(1, int(days_cover))
    safety_buffer = 7 if part.supplier_reliability >= 0.9 else 14
    effective_lead = int(round(part.lead_time_days * (1.0 + max(0, 0.95 - part.supplier_reliability))))
    gap = effective_lead + safety_buffer - predicted_need_days
    months_cover = usable / max(part.avg_monthly_usage, 0.01)
    carrying_cost = part.current_stock * part.unit_cost * 0.22

    if part.shelf_life_months and part.inventory_age_months >= part.shelf_life_months * 0.9:
        state = "SHELF_LIFE_RISK"
    elif months_cover > 24 and part.avg_monthly_usage < max(1, part.current_stock / 18):
        state = "EXCESS_INVENTORY"
    elif gap > 14:
        state = "AVAILABILITY_RISK"
    elif gap > 0:
        state = "ORDER_SOON"
    elif days_cover < 60:
        state = "MONITOR"
    else:
        state = "AVAILABLE"

    order_qty = max(0, ceil(fc["d30"] + part.safety_stock - usable))
    recommended_order_in_days = max(0, predicted_need_days - effective_lead - safety_buffer)
    return {
        "part_code": part.part_code,
        "part_name": part.name,
        "usable_stock": round(usable, 1),
        "current_stock": part.current_stock,
        "reserved_stock": part.reserved_stock,
        "safety_stock": part.safety_stock,
        "lead_time_days": part.lead_time_days,
        "effective_lead_days": effective_lead,
        "supplier_reliability": part.supplier_reliability,
        "supplier_name": part.supplier_name,
        "forecast": fc,
        "days_of_cover": round(days_cover, 1),
        "predicted_need_days": predicted_need_days,
        "availability_gap_days": max(0, gap),
        "state": state,
        "recommended_order_qty": order_qty,
        "recommended_order_in_days": recommended_order_in_days,
        "inventory_value": round(part.current_stock * part.unit_cost, 2),
        "annual_carrying_cost": round(carrying_cost, 2),
        "months_cover": round(months_cover, 1),
        "inventory_age_months": part.inventory_age_months,
        "shelf_life_months": part.shelf_life_months,
    }


def asset_detail(db: Session, asset: Asset) -> dict:
    readings = db.scalars(select(SensorReading).where(SensorReading.asset_id == asset.id).order_by(SensorReading.ts.desc()).limit(24)).all()
    latest = readings[0] if readings else None
    linked = []
    for link in asset.spare_links:
        av = availability_for(db, link.part)
        linked.append({**av, "importance": link.importance})
    return {
        "asset_code": asset.asset_code,
        "name": asset.name,
        "area": asset.area,
        "criticality": asset.criticality,
        "health_score": asset.health_score,
        "risk_score": asset.risk_score,
        "status": asset.status,
        "next_maintenance_days": asset.next_maintenance_days,
        "downtime_cost_per_hour": asset.downtime_cost_per_hour,
        "position": {"x": asset.x, "y": asset.y},
        "latest_sensor": None if latest is None else {
            "temperature": latest.temperature,
            "vibration": latest.vibration,
            "pressure": latest.pressure,
            "output_rate": latest.output_rate,
            "ts": latest.ts.isoformat(),
        },
        "parts": linked,
        "maintenance_history": [
            {
                "date": e.event_date.isoformat(),
                "type": e.event_type,
                "problem": e.problem,
                "part_code": e.part_code,
                "downtime_hours": e.downtime_hours,
                "maintenance_cost": e.maintenance_cost,
            }
            for e in sorted(asset.maintenance_events, key=lambda e: e.event_date, reverse=True)[:12]
        ],
    }
