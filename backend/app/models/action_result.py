from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.sql import func
from app.database.connection import Base


class ActionResult(Base):
    """Records the actual outcome after a recommendation is acted upon — the FEEDBACK LOOP"""
    __tablename__ = "action_results"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    action_taken = Column(String(100))   # e.g. "open_checkout", "restock", "reallocate_staff"
    taken_by = Column(Integer, ForeignKey("users.id"))
    taken_at = Column(DateTime(timezone=True), server_default=func.now())
    # Before/after metrics for success measurement
    metric_name = Column(String(100))    # e.g. "queue_length", "stock_level"
    metric_before = Column(Float)
    metric_after = Column(Float)
    measured_at = Column(DateTime(timezone=True))  # when outcome was measured
    success = Column(Boolean)           # True = metric improved as expected
    improvement_pct = Column(Float)     # (before - after) / before * 100
    notes = Column(Text)
