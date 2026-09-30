from __future__ import annotations

from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Plant(Base):
    __tablename__ = "plants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    carrying_rate: Mapped[float] = mapped_column(Float, default=0.22)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assets = relationship("Asset", back_populates="plant")


class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"))
    asset_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    area: Mapped[str] = mapped_column(String(80))
    asset_type: Mapped[str] = mapped_column(String(80))
    criticality: Mapped[str] = mapped_column(String(20), default="Medium")
    health_score: Mapped[float] = mapped_column(Float, default=80)
    risk_score: Mapped[float] = mapped_column(Float, default=20)
    downtime_cost_per_hour: Mapped[float] = mapped_column(Float, default=50000)
    next_maintenance_days: Mapped[int] = mapped_column(Integer, default=30)
    status: Mapped[str] = mapped_column(String(20), default="GREEN")
    x: Mapped[float] = mapped_column(Float, default=0)
    y: Mapped[float] = mapped_column(Float, default=0)
    plant = relationship("Plant", back_populates="assets")
    spare_links = relationship("AssetSparePart", back_populates="asset")
    sensor_readings = relationship("SensorReading", back_populates="asset")
    maintenance_events = relationship("MaintenanceEvent", back_populates="asset")


class SparePart(Base):
    __tablename__ = "spare_parts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    part_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(80), default="General")
    current_stock: Mapped[float] = mapped_column(Float, default=0)
    reserved_stock: Mapped[float] = mapped_column(Float, default=0)
    safety_stock: Mapped[float] = mapped_column(Float, default=0)
    unit_cost: Mapped[float] = mapped_column(Float, default=0)
    avg_monthly_usage: Mapped[float] = mapped_column(Float, default=0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=14)
    supplier_reliability: Mapped[float] = mapped_column(Float, default=0.9)
    shelf_life_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inventory_age_months: Mapped[float] = mapped_column(Float, default=0)
    supplier_name: Mapped[str] = mapped_column(String(120), default="Primary Supplier")
    supplier_status: Mapped[str] = mapped_column(String(40), default="Available")
    last_used_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    asset_links = relationship("AssetSparePart", back_populates="part")
    usage = relationship("PartUsage", back_populates="part")

    @property
    def usable_stock(self) -> float:
        return max(0.0, self.current_stock - self.reserved_stock)


class AssetSparePart(Base):
    __tablename__ = "asset_spare_parts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    part_id: Mapped[int] = mapped_column(ForeignKey("spare_parts.id"))
    importance: Mapped[str] = mapped_column(String(20), default="Medium")
    qty_per_service: Mapped[float] = mapped_column(Float, default=1)
    asset = relationship("Asset", back_populates="spare_links")
    part = relationship("SparePart", back_populates="asset_links")


class PartUsage(Base):
    __tablename__ = "part_usage"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    part_id: Mapped[int] = mapped_column(ForeignKey("spare_parts.id"))
    usage_date: Mapped[date] = mapped_column(Date)
    quantity: Mapped[float] = mapped_column(Float)
    part = relationship("SparePart", back_populates="usage")


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    vibration: Mapped[float | None] = mapped_column(Float, nullable=True)
    pressure: Mapped[float | None] = mapped_column(Float, nullable=True)
    output_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    asset = relationship("Asset", back_populates="sensor_readings")


class MaintenanceEvent(Base):
    __tablename__ = "maintenance_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    event_date: Mapped[date] = mapped_column(Date)
    event_type: Mapped[str] = mapped_column(String(50))
    problem: Mapped[str] = mapped_column(String(180))
    part_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    quantity_used: Mapped[float] = mapped_column(Float, default=0)
    downtime_hours: Mapped[float] = mapped_column(Float, default=0)
    maintenance_cost: Mapped[float] = mapped_column(Float, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset = relationship("Asset", back_populates="maintenance_events")


class ProcurementPlan(Base):
    __tablename__ = "procurement_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    part_code: Mapped[str] = mapped_column(String(32), index=True)
    suggested_qty: Mapped[float] = mapped_column(Float)
    approved_qty: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
