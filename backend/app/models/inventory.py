from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.database.connection import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    sku = Column(String(50), nullable=False, index=True)
    product_name = Column(String(200), nullable=False)
    category = Column(String(100), default="General")
    current_stock = Column(Float, nullable=False, default=0)
    max_stock = Column(Float, default=100)
    reorder_level = Column(Float, default=20)   # trigger reorder below this
    unit_cost = Column(Float, default=0.0)
    # AI-computed fields (updated by decision engine)
    demand_rate = Column(Float, default=0.0)    # units per minute
    predicted_stockout_minutes = Column(Float)  # null = no imminent stockout
    last_restock_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    zone_id = Column(Integer, ForeignKey("zones.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class InventoryEvent(Base):
    """Records every stock change: sale, restock, adjustment"""
    __tablename__ = "inventory_events"

    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    event_type = Column(String(30), nullable=False)  # sale | restock | adjustment | waste
    quantity_change = Column(Float, nullable=False)  # negative = consumed, positive = added
    stock_after = Column(Float, nullable=False)
    source = Column(String(30), default="simulator")  # simulator | pos | manual | edge
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    notes = Column(String(500))
