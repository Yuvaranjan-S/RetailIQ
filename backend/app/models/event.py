from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON, Boolean
from sqlalchemy.sql import func
from app.database.connection import Base


class Event(Base):
    """
    Raw anonymized events from edge pipeline or simulator.
    This is the INPUT stream to the Store State Engine.
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    # Types: zone_update | queue_update | inventory_update | staff_update |
    #         checkout_update | system_event | footfall_update
    source = Column(String(30), default="simulator")  # simulator | edge | manual | pos
    zone_id = Column(Integer, ForeignKey("zones.id"))
    payload = Column(JSON, nullable=False)
    confidence = Column(Float, default=1.0)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    is_synced = Column(Boolean, default=True)  # False = generated offline, not yet in central DB
    processed = Column(Boolean, default=False)
