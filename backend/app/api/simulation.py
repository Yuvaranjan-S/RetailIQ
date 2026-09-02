"""Simulation control API"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.api.auth import get_current_user
from app.models.user import User
from app.schemas.schemas import ScenarioRequest
from app.websocket.manager import ws_manager
from datetime import datetime, timezone
from typing import Optional

router = APIRouter(prefix="/simulation", tags=["simulation"])

# Runtime scenario state
_active_scenario: dict = {"name": "normal", "store_id": 1}


@router.get("/status")
async def get_simulation_status():
    """Public status endpoint for edge simulator polling"""
    return {
        "active_scenario": _active_scenario["name"],
        "store_id": _active_scenario["store_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/scenario")
async def set_scenario(
    body: ScenarioRequest,
):
    valid_scenarios = ["normal", "surge", "low_stock", "stockout", "queue", "staff_shortage", "multi", "offline"]
    if body.scenario not in valid_scenarios:
        raise HTTPException(400, f"Unknown scenario. Valid: {valid_scenarios}")

    _active_scenario["name"] = body.scenario
    _active_scenario["store_id"] = body.store_id

    await ws_manager.broadcast(body.store_id, {
        "type": "scenario_changed",
        "scenario": body.scenario,
        "message": f"🎬 Scenario activated: {body.scenario.upper().replace('_', ' ')}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "success": True,
        "scenario": body.scenario,
        "message": f"Scenario '{body.scenario}' activated",
    }


def get_active_scenario() -> str:
    return _active_scenario.get("name", "normal")
