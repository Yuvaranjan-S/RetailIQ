from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, JSON
from sqlalchemy.sql import func
from app.database.connection import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    rec_type = Column(String(50), nullable=False)
    # Types: open_checkout | close_checkout | restock | reallocate_staff |
    #         increase_staffing | reduce_zone_congestion | price_promotion
    title = Column(String(200), nullable=False)
    description = Column(Text)
    priority = Column(String(10), nullable=False, default="MEDIUM")  # CRITICAL|HIGH|MEDIUM|LOW
    confidence = Column(Float, nullable=False)       # 0.0 - 1.0
    reason = Column(Text)
    evidence = Column(JSON, default=[])              # list of evidence strings
    recommended_action = Column(Text)
    expected_impact = Column(Text)
    status = Column(String(20), default="pending")   # pending | accepted | rejected | modified | expired
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True))
    acted_at = Column(DateTime(timezone=True))
    acted_by = Column(Integer, ForeignKey("users.id"))
    # Related entities
    checkout_id = Column(Integer, ForeignKey("checkouts.id"))
    zone_id = Column(Integer, ForeignKey("zones.id"))
    staff_id = Column(Integer, ForeignKey("staff.id"))
    inventory_id = Column(Integer, ForeignKey("inventory.id"))
    alert_id = Column(Integer, ForeignKey("alerts.id"))
    generated_offline = Column(Integer, default=0)  # 1 if created while offline
