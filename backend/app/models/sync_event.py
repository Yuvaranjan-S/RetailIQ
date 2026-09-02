from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.database.connection import Base


class SyncEvent(Base):
    __tablename__ = "sync_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    synced_at = Column(DateTime(timezone=True))
    sync_status = Column(String(20), default="pending")  # pending | synced | conflict | failed
    conflict_resolved = Column(Boolean, default=False)
    resolution_strategy = Column(String(50))  # last_write_wins | manual | append
    created_at = Column(DateTime(timezone=True), server_default=func.now())
