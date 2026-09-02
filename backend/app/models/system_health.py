from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.database.connection import Base


class SystemHealth(Base):
    __tablename__ = "system_health"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    camera_status = Column(String(20), default="offline")   # online | offline | error
    ai_status = Column(String(20), default="idle")          # running | idle | error
    db_status = Column(String(20), default="healthy")       # healthy | degraded | offline
    network_status = Column(String(20), default="online")   # online | offline | degraded
    edge_fps = Column(Float, default=0.0)
    events_per_minute = Column(Float, default=0.0)
    sync_lag_seconds = Column(Float, default=0.0)
    pending_sync_count = Column(Integer, default=0)
    active_alerts_count = Column(Integer, default=0)
    uptime_seconds = Column(Float, default=0.0)
    checked_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
