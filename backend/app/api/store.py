"""Store State API — Digital Twin snapshot and zone details"""
from fastapi import APIRouter, HTTPException
from app.services.store_state_engine import get_store_twin

router = APIRouter(prefix="/store", tags=["store"])


@router.get("/state")
async def get_store_state(store_id: int = 1):
    twin = get_store_twin(store_id)
    if not twin:
        raise HTTPException(status_code=404, detail=f"Store {store_id} not found or not initialized")
    return twin.snapshot()


@router.get("/zones")
async def get_zones(store_id: int = 1):
    twin = get_store_twin(store_id)
    if not twin:
        raise HTTPException(status_code=404, detail="Store not initialized")
    return {"zones": [z.to_dict() for z in twin.zones.values()]}


@router.get("/zones/{zone_id}")
async def get_zone(zone_id: int, store_id: int = 1):
    twin = get_store_twin(store_id)
    if not twin or zone_id not in twin.zones:
        raise HTTPException(status_code=404, detail="Zone not found")
    return twin.zones[zone_id].to_dict()


@router.get("/checkouts")
async def get_checkouts(store_id: int = 1):
    twin = get_store_twin(store_id)
    if not twin:
        raise HTTPException(status_code=404, detail="Store not initialized")
    return {"checkouts": [c.to_dict() for c in twin.checkouts.values()]}


@router.get("/staff")
async def get_staff(store_id: int = 1):
    twin = get_store_twin(store_id)
    if not twin:
        raise HTTPException(status_code=404, detail="Store not initialized")
    return {"staff": [s.to_dict() for s in twin.staff.values()]}
