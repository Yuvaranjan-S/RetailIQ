"""
Store State Engine — The Real-Time Digital Twin

This is the core of RetailIQ. It maintains a continuously updated in-memory
representation of the entire store state. Every edge event or simulator tick
flows through here, updating the twin and triggering the decision engine.

Architecture:
  Events → update_from_event() → twin state updated → decision engine triggered
  → recommendations generated → broadcasted via WebSocket
"""
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("retailiq.store_engine")


@dataclass
class ZoneState:
    zone_id: int
    name: str
    zone_type: str
    people_count: int = 0
    dwell_time_avg: float = 0.0
    traffic_level: str = "low"
    heat_score: float = 0.0
    entry_count_session: int = 0
    coord_x: float = 0.0
    coord_y: float = 0.0
    coord_w: float = 20.0
    coord_h: float = 20.0
    display_color: str = "#3B82F6"
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def compute_traffic_level(self, capacity: int = 50) -> None:
        ratio = self.people_count / max(capacity, 1)
        if ratio >= 0.8:
            self.traffic_level = "critical"
        elif ratio >= 0.6:
            self.traffic_level = "high"
        elif ratio >= 0.3:
            self.traffic_level = "medium"
        else:
            self.traffic_level = "low"
        self.heat_score = min(ratio, 1.0)

    def to_dict(self) -> dict:
        return {
            "id": self.zone_id,
            "name": self.name,
            "zone_type": self.zone_type,
            "people_count": self.people_count,
            "dwell_time_avg": round(self.dwell_time_avg, 1),
            "traffic_level": self.traffic_level,
            "heat_score": round(self.heat_score, 3),
            "coord_x": self.coord_x,
            "coord_y": self.coord_y,
            "coord_w": self.coord_w,
            "coord_h": self.coord_h,
            "display_color": self.display_color,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class CheckoutState:
    checkout_id: int
    name: str
    is_open: bool = False
    checkout_type: str = "staffed"
    queue_length: int = 0
    estimated_wait_seconds: float = 0.0
    arrival_rate: float = 0.0    # customers/min
    service_rate: float = 1.8    # customers/min (default)
    staff_count: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def status(self) -> str:
        if not self.is_open:
            return "closed"
        if self.queue_length >= 10:
            return "critical"
        if self.queue_length >= 6:
            return "busy"
        return "normal"

    def to_dict(self) -> dict:
        return {
            "id": self.checkout_id,
            "name": self.name,
            "is_open": self.is_open,
            "checkout_type": self.checkout_type,
            "queue_length": self.queue_length,
            "estimated_wait_seconds": round(self.estimated_wait_seconds, 1),
            "estimated_wait_minutes": round(self.estimated_wait_seconds / 60, 1),
            "arrival_rate": round(self.arrival_rate, 2),
            "service_rate": round(self.service_rate, 2),
            "staff_count": self.staff_count,
            "status": self.status,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class InventoryState:
    inventory_id: int
    sku: str
    product_name: str
    category: str
    current_stock: float
    max_stock: float
    reorder_level: float
    demand_rate: float = 0.0      # units/minute
    predicted_stockout_minutes: Optional[float] = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def stock_percentage(self) -> float:
        return min(100.0, (self.current_stock / max(self.max_stock, 1)) * 100)

    @property
    def stock_status(self) -> str:
        if self.current_stock <= 0:
            return "out"
        if self.current_stock <= self.reorder_level * 0.5:
            return "critical"
        if self.current_stock <= self.reorder_level:
            return "low"
        return "ok"

    def to_dict(self) -> dict:
        return {
            "id": self.inventory_id,
            "sku": self.sku,
            "product_name": self.product_name,
            "category": self.category,
            "current_stock": round(self.current_stock, 1),
            "max_stock": self.max_stock,
            "reorder_level": self.reorder_level,
            "demand_rate": round(self.demand_rate, 3),
            "predicted_stockout_minutes": (
                round(self.predicted_stockout_minutes, 1)
                if self.predicted_stockout_minutes is not None else None
            ),
            "stock_percentage": round(self.stock_percentage, 1),
            "stock_status": self.stock_status,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class StaffState:
    staff_id: int
    name: str
    role: str
    current_zone_id: Optional[int] = None
    current_zone_name: Optional[str] = None
    availability: str = "available"
    current_task: Optional[str] = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.staff_id,
            "name": self.name,
            "role": self.role,
            "current_zone_id": self.current_zone_id,
            "current_zone_name": self.current_zone_name,
            "availability": self.availability,
            "current_task": self.current_task,
            "last_updated": self.last_updated.isoformat(),
        }


class StoreStateTwin:
    """
    The Live Store Digital Twin.

    Single source of truth for the store's current operational state.
    All events update this object. The decision engine reads from it.
    The WebSocket broadcaster publishes its snapshot every tick.
    """

    def __init__(self, store_id: int, store_name: str):
        self.store_id = store_id
        self.store_name = store_name
        self.status = "active"
        self.started_at = datetime.now(timezone.utc)

        # Core state maps
        self.zones: Dict[int, ZoneState] = {}
        self.checkouts: Dict[int, CheckoutState] = {}
        self.inventory: Dict[int, InventoryState] = {}
        self.staff: Dict[int, StaffState] = {}

        # Aggregate metrics
        self.current_footfall: int = 0
        self.total_customers_today: int = 0
        self.active_alerts_count: int = 0
        self.active_recommendations_count: int = 0

        # Footfall history (last 60 data points for sparklines)
        self.footfall_history: List[Dict] = []
        self.queue_history: List[Dict] = []  # aggregate queue length over time

        # System state
        self.network_status: str = "online"
        self.simulation_mode: bool = True
        self.pending_sync_count: int = 0

        self._lock = asyncio.Lock()

    # ─── Event Handlers ────────────────────────────────────────────────────

    async def update_from_event(self, event: dict) -> None:
        """
        Main entry point — processes any incoming event and updates twin state.
        Called by: simulator, edge pipeline, API event ingestion endpoint.
        """
        async with self._lock:
            event_type = event.get("event_type", "")
            payload = event.get("payload", {})

            if event_type == "zone_update":
                await self._handle_zone_update(event.get("zone_id"), payload)
            elif event_type == "queue_update":
                await self._handle_queue_update(payload)
            elif event_type == "inventory_update":
                await self._handle_inventory_update(payload)
            elif event_type == "staff_update":
                await self._handle_staff_update(payload)
            elif event_type == "checkout_update":
                await self._handle_checkout_update(payload)
            elif event_type == "footfall_update":
                await self._handle_footfall_update(payload)
            elif event_type == "system_event":
                await self._handle_system_event(payload)

            # Recompute aggregate footfall from zone counts
            self._recompute_footfall()

    async def _handle_zone_update(self, zone_id: Optional[int], payload: dict) -> None:
        zid = zone_id or payload.get("zone_id")
        if zid is None:
            return
        if zid not in self.zones:
            logger.warning(f"Unknown zone_id {zid}, skipping zone update")
            return
        z = self.zones[zid]
        z.people_count = payload.get("people_count", z.people_count)
        z.dwell_time_avg = payload.get("dwell_time_avg", z.dwell_time_avg)
        z.entry_count_session += payload.get("entry_delta", 0)
        z.compute_traffic_level()
        z.last_updated = datetime.now(timezone.utc)

    async def _handle_queue_update(self, payload: dict) -> None:
        checkout_id = payload.get("checkout_id")
        if checkout_id is None or checkout_id not in self.checkouts:
            return
        c = self.checkouts[checkout_id]
        c.queue_length = payload.get("queue_length", c.queue_length)
        c.estimated_wait_seconds = payload.get("estimated_wait_seconds", c.estimated_wait_seconds)
        c.arrival_rate = payload.get("arrival_rate", c.arrival_rate)
        c.service_rate = payload.get("service_rate", c.service_rate)
        c.staff_count = payload.get("staff_count", c.staff_count)
        if "is_open" in payload:
            c.is_open = payload["is_open"]
        c.last_updated = datetime.now(timezone.utc)

        # Append to queue history for sparklines
        total_q = sum(ch.queue_length for ch in self.checkouts.values())
        self.queue_history.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "total_queue": total_q,
        })
        if len(self.queue_history) > 120:
            self.queue_history = self.queue_history[-120:]

    async def _handle_inventory_update(self, payload: dict) -> None:
        inv_id = payload.get("inventory_id")
        if inv_id is None or inv_id not in self.inventory:
            return
        item = self.inventory[inv_id]
        if "current_stock" in payload:
            item.current_stock = max(0.0, payload["current_stock"])
        if "demand_rate" in payload:
            item.demand_rate = payload["demand_rate"]
        if "predicted_stockout_minutes" in payload:
            item.predicted_stockout_minutes = payload["predicted_stockout_minutes"]
        item.last_updated = datetime.now(timezone.utc)

    async def _handle_staff_update(self, payload: dict) -> None:
        staff_id = payload.get("staff_id")
        if staff_id is None or staff_id not in self.staff:
            return
        s = self.staff[staff_id]
        if "current_zone_id" in payload:
            s.current_zone_id = payload["current_zone_id"]
            # Resolve zone name
            if s.current_zone_id and s.current_zone_id in self.zones:
                s.current_zone_name = self.zones[s.current_zone_id].name
        if "availability" in payload:
            s.availability = payload["availability"]
        if "current_task" in payload:
            s.current_task = payload["current_task"]
        s.last_updated = datetime.now(timezone.utc)

    async def _handle_checkout_update(self, payload: dict) -> None:
        checkout_id = payload.get("checkout_id")
        if checkout_id is None or checkout_id not in self.checkouts:
            return
        c = self.checkouts[checkout_id]
        if "is_open" in payload:
            c.is_open = payload["is_open"]
        if "staff_count" in payload:
            c.staff_count = payload["staff_count"]
        c.last_updated = datetime.now(timezone.utc)

    async def _handle_footfall_update(self, payload: dict) -> None:
        delta = payload.get("delta", 0)
        self.total_customers_today += max(0, delta)
        ts = datetime.now(timezone.utc).isoformat()
        self.footfall_history.append({"ts": ts, "count": self.current_footfall})
        if len(self.footfall_history) > 120:
            self.footfall_history = self.footfall_history[-120:]

    async def _handle_system_event(self, payload: dict) -> None:
        if "network_status" in payload:
            self.network_status = payload["network_status"]
        if "active_alerts_count" in payload:
            self.active_alerts_count = payload["active_alerts_count"]
        if "active_recommendations_count" in payload:
            self.active_recommendations_count = payload["active_recommendations_count"]
        if "pending_sync_count" in payload:
            self.pending_sync_count = payload["pending_sync_count"]

    def _recompute_footfall(self) -> None:
        """Current footfall = sum of people across all non-storage zones"""
        self.current_footfall = sum(
            z.people_count for z in self.zones.values()
            if z.zone_type != "storage"
        )

    # ─── Initialization ─────────────────────────────────────────────────────

    def initialize_zones(self, zones: List[dict]) -> None:
        for z in zones:
            self.zones[z["id"]] = ZoneState(
                zone_id=z["id"],
                name=z["name"],
                zone_type=z.get("zone_type", "general"),
                coord_x=z.get("coord_x", 0),
                coord_y=z.get("coord_y", 0),
                coord_w=z.get("coord_w", 20),
                coord_h=z.get("coord_h", 20),
                display_color=z.get("display_color", "#3B82F6"),
            )

    def initialize_checkouts(self, checkouts: List[dict]) -> None:
        for c in checkouts:
            self.checkouts[c["id"]] = CheckoutState(
                checkout_id=c["id"],
                name=c["name"],
                is_open=c.get("is_open", False),
                checkout_type=c.get("checkout_type", "staffed"),
            )

    def initialize_inventory(self, items: List[dict]) -> None:
        for item in items:
            self.inventory[item["id"]] = InventoryState(
                inventory_id=item["id"],
                sku=item["sku"],
                product_name=item["product_name"],
                category=item.get("category", "General"),
                current_stock=item["current_stock"],
                max_stock=item["max_stock"],
                reorder_level=item["reorder_level"],
                demand_rate=item.get("demand_rate", 0.0),
            )

    def initialize_staff(self, staff_list: List[dict]) -> None:
        for s in staff_list:
            self.staff[s["id"]] = StaffState(
                staff_id=s["id"],
                name=s["name"],
                role=s.get("role", "associate"),
                current_zone_id=s.get("current_zone_id"),
                availability=s.get("availability", "available"),
            )

    # ─── Snapshot ───────────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        """Returns full twin state as a serializable dict for WebSocket broadcast"""
        total_open = sum(1 for c in self.checkouts.values() if c.is_open)
        total_queue = sum(c.queue_length for c in self.checkouts.values())
        avg_wait = (
            sum(c.estimated_wait_seconds for c in self.checkouts.values() if c.is_open)
            / max(total_open, 1)
        )

        low_stock_count = sum(
            1 for i in self.inventory.values()
            if i.stock_status in ("low", "critical", "out")
        )
        out_of_stock_count = sum(
            1 for i in self.inventory.values() if i.stock_status == "out"
        )
        available_staff = sum(
            1 for s in self.staff.values() if s.availability == "available"
        )

        return {
            "type": "store_state",
            "store_id": self.store_id,
            "store_name": self.store_name,
            "status": self.status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            # KPIs
            "current_footfall": self.current_footfall,
            "total_customers_today": self.total_customers_today,
            "active_alerts_count": self.active_alerts_count,
            "active_recommendations_count": self.active_recommendations_count,
            # Zone summary
            "zones": [z.to_dict() for z in self.zones.values()],
            # Checkout summary
            "checkouts": [c.to_dict() for c in self.checkouts.values()],
            "open_checkouts": total_open,
            "total_queue_length": total_queue,
            "avg_wait_seconds": round(avg_wait, 1),
            # Inventory summary
            "inventory": [i.to_dict() for i in self.inventory.values()],
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            # Staff summary
            "staff": [s.to_dict() for s in self.staff.values()],
            "available_staff": available_staff,
            # System
            "network_status": self.network_status,
            "simulation_mode": self.simulation_mode,
            "pending_sync_count": self.pending_sync_count,
            # Sparkline history
            "footfall_history": self.footfall_history[-30:],
            "queue_history": self.queue_history[-30:],
        }

    def get_decision_context(self) -> dict:
        """
        Returns the context dict that the AI Decision Engine reads.
        Contains all signals needed for rule evaluation and fusion scoring.
        """
        total_queue = sum(c.queue_length for c in self.checkouts.values())
        max_wait = max((c.estimated_wait_seconds for c in self.checkouts.values()), default=0)
        open_checkouts = [c for c in self.checkouts.values() if c.is_open]
        closed_checkouts = [c for c in self.checkouts.values() if not c.is_open]
        available_staff = [s for s in self.staff.values() if s.availability == "available"]

        critical_inventory = [
            i for i in self.inventory.values()
            if i.stock_status in ("critical", "out")
        ]
        low_inventory = [
            i for i in self.inventory.values() if i.stock_status == "low"
        ]
        imminent_stockouts = [
            i for i in self.inventory.values()
            if i.predicted_stockout_minutes is not None and i.predicted_stockout_minutes < 30
        ]

        high_traffic_zones = [
            z for z in self.zones.values()
            if z.traffic_level in ("high", "critical")
        ]

        return {
            "store_id": self.store_id,
            "current_footfall": self.current_footfall,
            "total_queue_length": total_queue,
            "max_wait_seconds": max_wait,
            "open_checkouts": len(open_checkouts),
            "closed_checkouts": len(closed_checkouts),
            "closed_checkout_list": [{"id": c.checkout_id, "name": c.name} for c in closed_checkouts],
            "available_staff_count": len(available_staff),
            "available_staff_list": [{"id": s.staff_id, "name": s.name} for s in available_staff],
            "critical_inventory": [i.to_dict() for i in critical_inventory],
            "low_inventory": [i.to_dict() for i in low_inventory],
            "imminent_stockouts": [i.to_dict() for i in imminent_stockouts],
            "high_traffic_zones": [z.to_dict() for z in high_traffic_zones],
            "zones": {zid: z.to_dict() for zid, z in self.zones.items()},
            "checkouts": {cid: c.to_dict() for cid, c in self.checkouts.items()},
            "staff": {sid: s.to_dict() for sid, s in self.staff.items()},
            "inventory": {iid: i.to_dict() for iid, i in self.inventory.items()},
        }


# ─── Singleton store registry ────────────────────────────────────────────────
# Holds one twin per store_id.  For hackathon, typically one store.
_store_registry: Dict[int, StoreStateTwin] = {}


def get_store_twin(store_id: int) -> Optional[StoreStateTwin]:
    return _store_registry.get(store_id)


def register_store_twin(twin: StoreStateTwin) -> None:
    _store_registry[twin.store_id] = twin
    logger.info(f"Store twin registered: store_id={twin.store_id} '{twin.store_name}'")


def all_store_twins() -> List[StoreStateTwin]:
    return list(_store_registry.values())
