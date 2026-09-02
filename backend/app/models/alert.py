from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.sql import func
from app.database.connection import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False, index=True)
    # Types: stockout | low_stock | queue_critical | congestion_predicted |
    #         staff_shortage | camera_offline | sync_error | system_health
    severity = Column(String(10), nullable=False)  # CRITICAL | HIGH | MEDIUM | LOW
    title = Column(String(200), nullable=False)
    description = Column(Text)
    location = Column(String(200))  # zone name or "Store-wide"
    recommended_action = Column(Text)
    status = Column(String(20), default="active")  # active | acknowledged | resolved | dismissed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at = Column(DateTime(timezone=True))
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    # Link to what triggered the alert
    zone_id = Column(Integer, ForeignKey("zones.id"))
    inventory_id = Column(Integer, ForeignKey("inventory.id"))
    checkout_id = Column(Integer, ForeignKey("checkouts.id"))
