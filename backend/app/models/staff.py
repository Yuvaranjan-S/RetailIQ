from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.database.connection import Base


class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    role = Column(String(50), default="associate")  # associate | cashier | supervisor | manager
    current_zone_id = Column(Integer, ForeignKey("zones.id"))
    availability = Column(String(20), default="available")  # available | busy | break | offline
    current_task = Column(String(200))
    shift_start = Column(DateTime(timezone=True))
    shift_end = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
