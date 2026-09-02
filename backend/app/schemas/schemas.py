"""Pydantic schemas for request/response validation"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum


# ─── Auth ───────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    full_name: Optional[str] = None
    model_config = {"from_attributes": True}


# ─── Store / Zone ────────────────────────────────────────────────────────────
class ZoneState(BaseModel):
    id: int
    name: str
    zone_type: str
    people_count: int = 0
    dwell_time_avg: float = 0.0
    traffic_level: str = "low"
    heat_score: float = 0.0
    coord_x: float = 0.0
    coord_y: float = 0.0
    coord_w: float = 20.0
    coord_h: float = 20.0
    display_color: str = "#3B82F6"
    model_config = {"from_attributes": True}

class CheckoutState(BaseModel):
    id: int
    name: str
    is_open: bool
    checkout_type: str
    queue_length: int = 0
    estimated_wait_seconds: float = 0.0
    staff_count: int = 0
    model_config = {"from_attributes": True}

class StaffState(BaseModel):
    id: int
    name: str
    role: str
    current_zone_id: Optional[int] = None
    current_zone_name: Optional[str] = None
    availability: str
    current_task: Optional[str] = None
    model_config = {"from_attributes": True}

class InventoryState(BaseModel):
    id: int
    sku: str
    product_name: str
    category: str
    current_stock: float
    max_stock: float
    reorder_level: float
    demand_rate: float
    predicted_stockout_minutes: Optional[float] = None
    stock_status: str = "ok"  # ok | low | critical | out
    stock_percentage: float = 100.0
    model_config = {"from_attributes": True}

class StoreState(BaseModel):
    """Full digital twin snapshot"""
    store_id: int
    store_name: str
    status: str
    timestamp: str
    # Aggregates
    current_footfall: int
    total_customers_today: int
    active_alerts_count: int
    # Sub-states
    zones: List[ZoneState]
    checkouts: List[CheckoutState]
    staff: List[StaffState]
    inventory_summary: Dict[str, Any]  # summary stats
    network_status: str = "online"
    simulation_mode: bool = True


# ─── Alerts ──────────────────────────────────────────────────────────────────
class AlertOut(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    recommended_action: Optional[str] = None
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ─── Recommendations ─────────────────────────────────────────────────────────
class RecommendationOut(BaseModel):
    id: int
    rec_type: str
    title: str
    description: Optional[str] = None
    priority: str
    confidence: float
    reason: Optional[str] = None
    evidence: List[str] = []
    recommended_action: Optional[str] = None
    expected_impact: Optional[str] = None
    status: str
    created_at: datetime
    checkout_id: Optional[int] = None
    zone_id: Optional[int] = None
    inventory_id: Optional[int] = None
    model_config = {"from_attributes": True}

class RecommendationAction(BaseModel):
    notes: Optional[str] = None


# ─── Events ──────────────────────────────────────────────────────────────────
class EventIn(BaseModel):
    store_id: int
    event_type: str
    source: str = "edge"
    zone_id: Optional[int] = None
    payload: Dict[str, Any]
    confidence: float = 1.0
    timestamp: Optional[datetime] = None

class EventBatchIn(BaseModel):
    events: List[EventIn]


# ─── Simulation ──────────────────────────────────────────────────────────────
class ScenarioRequest(BaseModel):
    scenario: str  # normal | surge | low_stock | stockout | queue | staff_shortage | multi | offline
    store_id: int = 1
    duration_seconds: Optional[int] = None


# ─── Sync ────────────────────────────────────────────────────────────────────
class SyncStatusOut(BaseModel):
    network_status: str
    pending_events: int
    last_synced_at: Optional[datetime] = None
    total_synced_today: int = 0


# ─── Analytics ───────────────────────────────────────────────────────────────
class FootfallDataPoint(BaseModel):
    timestamp: datetime
    count: int
    zone_id: Optional[int] = None

class HeatmapZone(BaseModel):
    zone_id: int
    zone_name: str
    heat_score: float
    coord_x: float
    coord_y: float
    coord_w: float
    coord_h: float
