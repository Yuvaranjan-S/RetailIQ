"""Inventory API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone
from typing import Optional

from app.database.connection import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.inventory import Inventory, InventoryEvent
from app.services.store_state_engine import get_store_twin

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("")
async def get_inventory(
    store_id: int = 1,
    status: Optional[str] = None,   # ok | low | critical | out
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    twin = get_store_twin(store_id)
    if twin:
        items = [i.to_dict() for i in twin.inventory.values()]
        if status:
            items = [i for i in items if i["stock_status"] == status]
        return {"inventory": items, "count": len(items)}

    # Fallback to DB
    result = await db.execute(
        select(Inventory).where(Inventory.store_id == store_id, Inventory.is_active == True)
    )
    items = result.scalars().all()
    return {"inventory": [{"sku": i.sku, "product_name": i.product_name,
                           "current_stock": i.current_stock} for i in items]}


@router.get("/alerts")
async def get_inventory_alerts(
    store_id: int = 1,
    current_user: User = Depends(get_current_user),
):
    twin = get_store_twin(store_id)
    if not twin:
        raise HTTPException(404, "Store not initialized")
    alerts = [
        i.to_dict() for i in twin.inventory.values()
        if i.stock_status in ("low", "critical", "out")
    ]
    return {"alerts": alerts, "count": len(alerts)}


@router.get("/{sku}")
async def get_inventory_item(
    sku: str,
    store_id: int = 1,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    twin = get_store_twin(store_id)
    if twin:
        item = next((i for i in twin.inventory.values() if i.sku == sku), None)
        if item:
            return item.to_dict()

    result = await db.execute(
        select(Inventory).where(Inventory.sku == sku, Inventory.store_id == store_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, f"SKU {sku} not found")
    return {"sku": item.sku, "product_name": item.product_name, "current_stock": item.current_stock}


@router.post("/{sku}/restock")
async def restock_item(
    sku: str,
    quantity: float,
    store_id: int = 1,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a manual restock event"""
    result = await db.execute(
        select(Inventory).where(Inventory.sku == sku, Inventory.store_id == store_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, f"SKU {sku} not found")

    new_stock = min(item.current_stock + quantity, item.max_stock)
    await db.execute(
        update(Inventory).where(Inventory.id == item.id).values(
            current_stock=new_stock,
            last_restock_at=datetime.now(timezone.utc),
        )
    )

    event = InventoryEvent(
        inventory_id=item.id,
        store_id=store_id,
        event_type="restock",
        quantity_change=quantity,
        stock_after=new_stock,
        source="manual",
    )
    db.add(event)
    await db.commit()

    # Update twin
    twin = get_store_twin(store_id)
    if twin and item.id in twin.inventory:
        twin.inventory[item.id].current_stock = new_stock
        twin.inventory[item.id].predicted_stockout_minutes = None

    return {"sku": sku, "restocked_by": quantity, "new_stock": new_stock, "success": True}
