from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.sql import func
from app.database.connection import Base


class QueueSnapshot(Base):
    __tablename__ = "queue_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    checkout_id = Column(Integer, ForeignKey("checkouts.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    queue_length = Column(Integer, default=0)
    estimated_wait_seconds = Column(Float, default=0.0)
    arrival_rate = Column(Float, default=0.0)    # customers per minute
    service_rate = Column(Float, default=0.0)    # customers per minute
    staff_count = Column(Integer, default=1)
    status = Column(String(20), default="normal")  # normal | busy | critical
