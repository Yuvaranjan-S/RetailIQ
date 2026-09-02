"""System Health + Offline Mode API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.database.connection import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.system_health import SystemHealth
from app.services.store_state_engine import get_store_twin, all_store_twins
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/system", tags=["system"])

# Runtime state for offline simulation
_offline_stores: set = set()


@router.get("/health")
async def get_health(
    store_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    twin = get_store_twin(store_id)
    is_offline = store_id in _offline_stores

    return {
        "store_id": store_id,
        "camera_status": "simulation" if (twin and twin.simulation_mode) else "online",
        "ai_status": "running",
        "db_status": "healthy",
        "network_status": "offline" if is_offline else "online",
        "simulation_mode": twin.simulation_mode if twin else True,
        "active_connections": ws_manager.connection_count(store_id),
        "footfall": twin.current_footfall if twin else 0,
        "pending_sync_count": twin.pending_sync_count if twin else 0,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/offline")
async def simulate_offline(
    store_id: int = 1,
    current_user: User = Depends(get_current_user),
):
    """Simulate network failure — stops sync, AI continues locally"""
    _offline_stores.add(store_id)
    twin = get_store_twin(store_id)
    if twin:
        twin.network_status = "offline"
        await ws_manager.broadcast(store_id, {
            "type": "network_status_change",
            "status": "offline",
            "message": "⚠ Network disconnected. AI continues locally. Events queued for sync.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    return {"success": True, "network_status": "offline", "store_id": store_id}


@router.post("/online")
async def simulate_online(
    store_id: int = 1,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restore connectivity and trigger sync"""
    _offline_stores.discard(store_id)
    twin = get_store_twin(store_id)

    # Count pending sync events
    pending = 0
    if twin:
        pending = twin.pending_sync_count
        twin.network_status = "online"
        twin.pending_sync_count = 0

    await ws_manager.broadcast(store_id, {
        "type": "network_status_change",
        "status": "online",
        "message": f"↑ Network restored. Synchronizing {pending} events...",
        "syncing": True,
        "pending_count": pending,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Brief delay then broadcast sync complete
    import asyncio
    await asyncio.sleep(2)
    await ws_manager.broadcast(store_id, {
        "type": "sync_complete",
        "message": f"✓ Synchronized — {pending} events uploaded",
        "synced_count": pending,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    return {"success": True, "network_status": "online", "synced_events": pending}


def is_store_offline(store_id: int) -> bool:
    return store_id in _offline_stores
