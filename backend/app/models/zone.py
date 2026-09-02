from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database.connection import Base


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    zone_type = Column(String(50), default="general")  # general | checkout | entrance | storage
    capacity = Column(Integer, default=50)
    # Layout coords for heatmap rendering (0-100 percentage of floor plan)
    coord_x = Column(Float, default=0.0)
    coord_y = Column(Float, default=0.0)
    coord_w = Column(Float, default=20.0)
    coord_h = Column(Float, default=20.0)
    display_color = Column(String(7), default="#3B82F6")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ZoneSnapshot(Base):
    """Periodic snapshots of zone state for historical analytics"""
    __tablename__ = "zone_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    people_count = Column(Integer, default=0)
    dwell_time_avg = Column(Float, default=0.0)  # seconds
    traffic_level = Column(String(10), default="low")  # low | medium | high | critical
    heat_score = Column(Float, default=0.0)  # 0.0 - 1.0
    entry_count = Column(Integer, default=0)
    exit_count = Column(Integer, default=0)
