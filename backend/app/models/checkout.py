from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.connection import Base


class Checkout(Base):
    __tablename__ = "checkouts"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False)   # e.g. "Checkout 1"
    is_open = Column(Boolean, default=False)
    checkout_type = Column(String(20), default="staffed")  # staffed | self-checkout | express
    opened_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
