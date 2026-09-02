"""
Store Simulator — Dynamic Realistic Store Behavior Engine

Supports:
  - Dynamic discovery of all store zones (8 zones), checkouts (6 lanes), and inventory items (40 SKUs)
  - Realistic Poisson customer arrival & movement dynamics
  - M/M/c Erlang-C queue simulations
  - Real-time stock consumption & demand rates
  - 8 Scenario profiles (Normal, Surge, Queue, Low Stock, Stockout, Staff Shortage, Multi-Incident, Offline)
"""
import asyncio
import httpx
import random
import math
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SIMULATOR] %(levelname)s — %(message)s",
)
logger = logging.getLogger("retailiq.simulator")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
STORE_ID = int(os.getenv("SIMULATOR_STORE_ID", "1"))
TICK_SECONDS = float(os.getenv("SIMULATOR_TICK_SECONDS", "2"))


class DynamicSimulatorState:
    def __init__(self):
        self.tick = 0
        self.scenario = "normal"
        self.initialized_from_backend = False

        # Zone counts and dwell times
        self.zone_counts: Dict[int, int] = {}
        self.zone_dwell: Dict[int, float] = {}
        self.zone_caps: Dict[int, int] = {}

        # Checkout states
        self.checkout_open: Dict[int, bool] = {}
        self.checkout_queues: Dict[int, int] = {}
        self.checkout_wait: Dict[int, float] = {}
        self.arrival_rates: Dict[int, float] = {}
        self.service_rates: Dict[int, float] = {}
        self.checkout_staff: Dict[int, int] = {}

        # Inventory states
        self.stock: Dict[int, float] = {}
        self.max_stock: Dict[int, float] = {}
        self.reorder: Dict[int, float] = {}
        self.demand_rates: Dict[int, float] = {}

        # Metrics
        self.total_footfall_today = 120
        self.footfall_history: List[int] = [random.randint(30, 60) for _ in range(30)]
        self.is_offline = False
        self.offline_event_buffer: List[dict] = []

    def bootstrap_default(self):
        """Default fallback if backend state isn't fetched yet"""
        # 8 zones
        for zid in range(1, 9):
            self.zone_counts[zid] = random.randint(4, 15)
            self.zone_dwell[zid] = random.uniform(35.0, 75.0)
            self.zone_caps[zid] = 60
        self.zone_caps[1] = 40  # entrance
        self.zone_caps[5] = 90  # pantry
        self.zone_caps[7] = 65  # checkout
        self.zone_caps[8] = 25  # storage

        # 6 checkouts
        for cid in range(1, 7):
            is_op = cid <= 3
            self.checkout_open[cid] = is_op
            self.checkout_queues[cid] = random.randint(2, 4) if is_op else 0
            self.checkout_wait[cid] = 60.0 if is_op else 0.0
            self.arrival_rates[cid] = 1.2 if is_op else 0.0
            self.service_rates[cid] = 2.0 if cid == 1 else 1.8
            self.checkout_staff[cid] = 1 if is_op else 0

        # 40 items
        for iid in range(1, 41):
            self.stock[iid] = random.uniform(20.0, 60.0)
            self.max_stock[iid] = 80.0
            self.reorder[iid] = 20.0
            self.demand_rates[iid] = random.uniform(0.05, 0.25)

    def sync_from_snapshot(self, snapshot: dict):
        """Update simulator state models directly from twin snapshot"""
        if not snapshot:
            return
        # Zones
        for z in snapshot.get("zones", []):
            zid = z["id"]
            if zid not in self.zone_counts:
                self.zone_counts[zid] = z.get("people_count", 8)
                self.zone_dwell[zid] = z.get("dwell_time_avg", 45.0)
                self.zone_caps[zid] = 65

        # Checkouts
        for c in snapshot.get("checkouts", []):
            cid = c["id"]
            self.checkout_open[cid] = c.get("is_open", False)
            if cid not in self.checkout_queues:
                self.checkout_queues[cid] = c.get("queue_length", 0)
                self.checkout_wait[cid] = c.get("estimated_wait_seconds", 0.0)
                self.arrival_rates[cid] = c.get("arrival_rate", 1.0)
                self.service_rates[cid] = c.get("service_rate", 1.8)
                self.checkout_staff[cid] = c.get("staff_count", 1 if c.get("is_open") else 0)

        # Inventory
        for item in snapshot.get("inventory", []):
            iid = item["id"]
            if iid not in self.stock:
                self.stock[iid] = float(item.get("current_stock", 30))
                self.max_stock[iid] = float(item.get("max_stock", 80))
                self.reorder[iid] = float(item.get("reorder_level", 20))
                self.demand_rates[iid] = float(item.get("demand_rate", 0.15))

        self.initialized_from_backend = True

    def get_scenario_multipliers(self) -> dict:
        base = {
            "footfall": 1.0,
            "demand": 1.0,
            "arrival_rate": 1.0,
            "service_rate": 1.0,
        }
        if self.scenario == "surge":
            base["footfall"] = 2.6
            base["demand"] = 2.2
            base["arrival_rate"] = 2.8
        elif self.scenario == "low_stock":
            base["demand"] = 3.5
        elif self.scenario == "stockout":
            base["demand"] = 5.5
            base["footfall"] = 2.2
        elif self.scenario == "queue":
            base["arrival_rate"] = 3.8
            base["footfall"] = 2.0
            base["service_rate"] = 0.55
        elif self.scenario == "staff_shortage":
            base["footfall"] = 2.2
            base["service_rate"] = 0.50
        elif self.scenario == "multi":
            base["footfall"] = 2.9
            base["demand"] = 3.8
            base["arrival_rate"] = 3.6
            base["service_rate"] = 0.60
        return base


state = DynamicSimulatorState()
state.bootstrap_default()


def _poisson(lam: float) -> int:
    if lam <= 0:
        return 0
    return int(random.expovariate(1 / max(lam, 0.001)) + 0.5)


def tick_zones(mult: dict) -> List[dict]:
    events = []
    footfall_mult = mult["footfall"]

    for zid, count in list(state.zone_counts.items()):
        # Exclude storage zone from random arrivals
        if zid == 8:
            continue

        lam = random.uniform(1.0, 2.5) * footfall_mult * TICK_SECONDS / 60
        arrivals = _poisson(lam)
        departures = min(count, _poisson(count * 0.12 * TICK_SECONDS / 60 + 0.2))

        cap = state.zone_caps.get(zid, 60)
        new_count = max(0, min(count + arrivals - departures, cap))
        state.zone_counts[zid] = new_count

        state.zone_dwell[zid] = max(15.0, min(300.0, state.zone_dwell[zid] + random.uniform(-4, 6)))

        events.append({
            "store_id": STORE_ID,
            "event_type": "zone_update",
            "zone_id": zid,
            "payload": {
                "zone_id": zid,
                "people_count": new_count,
                "dwell_time_avg": round(state.zone_dwell[zid], 1),
                "entry_delta": max(0, arrivals),
            },
            "confidence": round(0.92 + random.uniform(-0.02, 0.04), 3),
            "source": "simulator",
        })

    # Total active footfall
    total = sum(v for k, v in state.zone_counts.items() if k != 8)
    state.total_footfall_today += max(0, int(_poisson(0.6 * footfall_mult)))
    state.footfall_history.append(total)
    if len(state.footfall_history) > 120:
        state.footfall_history = state.footfall_history[-120:]

    events.append({
        "store_id": STORE_ID,
        "event_type": "footfall_update",
        "payload": {
            "current": total,
            "delta": max(0, int(_poisson(0.6 * footfall_mult))),
            "total_today": state.total_footfall_today,
        },
        "source": "simulator",
    })

    return events


def tick_queues(mult: dict) -> List[dict]:
    events = []
    arrival_mult = mult["arrival_rate"]
    service_mult = mult["service_rate"]

    total_footfall = sum(v for k, v in state.zone_counts.items() if k != 8 and k != 7)
    checkout_arrivals = _poisson(total_footfall * 0.06 * arrival_mult * TICK_SECONDS / 60)

    open_co = [cid for cid, is_open in state.checkout_open.items() if is_open]

    for cid in list(state.checkout_open.keys()):
        is_open = state.checkout_open.get(cid, False)
        current_q = state.checkout_queues.get(cid, 0)

        if not is_open:
            state.checkout_queues[cid] = 0
            state.checkout_wait[cid] = 0
        else:
            if open_co:
                arrivals = checkout_arrivals // len(open_co)
                if cid == open_co[0]:
                    arrivals += checkout_arrivals % len(open_co)
            else:
                arrivals = checkout_arrivals

            sr = state.service_rates.get(cid, 1.8) * service_mult
            serviced = min(current_q + arrivals, max(1, int(_poisson(sr * TICK_SECONDS))))
            new_q = max(0, current_q + arrivals - serviced)
            state.checkout_queues[cid] = new_q

            state.arrival_rates[cid] = round(
                0.7 * state.arrival_rates.get(cid, 1.0) + 0.3 * (arrivals / max(TICK_SECONDS / 60, 0.01)),
                3
            )
            lam = state.arrival_rates[cid]
            mu = sr
            rho = lam / max(mu, 0.01)
            if rho < 1:
                wait_min = (rho / (mu * max(1 - rho, 0.01))) if new_q > 0 else 0
            else:
                wait_min = new_q / max(mu - lam, 0.01)
            state.checkout_wait[cid] = round(wait_min * 60, 1)

        events.append({
            "store_id": STORE_ID,
            "event_type": "queue_update",
            "payload": {
                "checkout_id": cid,
                "queue_length": state.checkout_queues.get(cid, 0),
                "estimated_wait_seconds": state.checkout_wait.get(cid, 0.0),
                "arrival_rate": state.arrival_rates.get(cid, 0.0),
                "service_rate": state.service_rates.get(cid, 1.8) * service_mult,
                "staff_count": state.checkout_staff.get(cid, 1 if is_open else 0),
                "is_open": is_open,
            },
            "source": "simulator",
        })

    return events


def tick_inventory(mult: dict) -> List[dict]:
    events = []
    demand_mult = mult["demand"]

    for inv_id in list(state.stock.keys()):
        current = state.stock[inv_id]
        if current <= 0:
            events.append({
                "store_id": STORE_ID,
                "event_type": "inventory_update",
                "payload": {
                    "inventory_id": inv_id,
                    "current_stock": 0.0,
                    "demand_rate": state.demand_rates.get(inv_id, 0.1) * demand_mult,
                    "predicted_stockout_minutes": 0.0,
                },
                "source": "simulator",
            })
            continue

        rate = state.demand_rates.get(inv_id, 0.1) * demand_mult
        consumed = rate * TICK_SECONDS * (0.8 + random.random() * 0.4)
        consumed = min(current, consumed)
        new_stock = max(0.0, current - consumed)
        state.stock[inv_id] = new_stock

        stockout_min = None
        if rate > 0 and new_stock > 0:
            stockout_min = round(new_stock / rate / 60, 1)
            if stockout_min > 120:
                stockout_min = None

        events.append({
            "store_id": STORE_ID,
            "event_type": "inventory_update",
            "payload": {
                "inventory_id": inv_id,
                "current_stock": round(new_stock, 2),
                "demand_rate": round(rate, 4),
                "predicted_stockout_minutes": stockout_min,
            },
            "source": "simulator",
        })

    return events


async def send_events(client: httpx.AsyncClient, events: List[dict]) -> None:
    if state.is_offline:
        state.offline_event_buffer.extend(events)
        return
    try:
        await client.post(
            f"{BACKEND_URL}/api/events/batch",
            json={"events": events},
            timeout=5.0,
        )
    except Exception as e:
        logger.warning(f"Failed to send events ({e}). Buffering {len(events)} events.")
        state.offline_event_buffer.extend(events)


async def check_scenario_and_twin(client: httpx.AsyncClient) -> None:
    try:
        # Check scenario
        resp = await client.get(f"{BACKEND_URL}/api/simulation/status", timeout=3.0)
        if resp.status_code == 200:
            data = resp.json()
            new_scenario = data.get("active_scenario", "normal")
            if new_scenario != state.scenario:
                logger.info(f"🎬 Scenario changed: {state.scenario} -> {new_scenario}")
                state.scenario = new_scenario

        # Sync state from twin if needed
        if not state.initialized_from_backend:
            snap_resp = await client.get(f"{BACKEND_URL}/api/store/state?store_id={STORE_ID}", timeout=3.0)
            if snap_resp.status_code == 200:
                state.sync_from_snapshot(snap_resp.json())
                logger.info("Synchronized simulator state from store twin")
    except Exception:
        pass


async def simulator_loop():
    logger.info(f"🏪 Store simulator starting — STORE_ID={STORE_ID}, TICK={TICK_SECONDS}s")
    logger.info(f"📡 Backend URL: {BACKEND_URL}")

    async with httpx.AsyncClient() as client:
        # Wait for backend
        for attempt in range(30):
            try:
                resp = await client.get(f"{BACKEND_URL}/health", timeout=3.0)
                if resp.status_code == 200:
                    logger.info("Backend is ready")
                    break
            except Exception:
                pass
            await asyncio.sleep(2)

        # Initial sync
        await check_scenario_and_twin(client)

        tick_count = 0
        while True:
            tick_count += 1
            state.tick = tick_count

            if tick_count % 8 == 0:
                await check_scenario_and_twin(client)

            mult = state.get_scenario_multipliers()
            all_events = []

            all_events.extend(tick_zones(mult))
            all_events.extend(tick_queues(mult))
            all_events.extend(tick_inventory(mult))

            await send_events(client, all_events)

            if tick_count % 30 == 0:
                total_q = sum(state.checkout_queues.values())
                footfall = sum(v for k, v in state.zone_counts.items() if k != 8)
                logger.info(
                    f"Tick {tick_count} | Scenario: {state.scenario} | "
                    f"Footfall: {footfall} | Queue: {total_q} | "
                    f"Active SKUs: {len(state.stock)}"
                )

            await asyncio.sleep(TICK_SECONDS)


if __name__ == "__main__":
    asyncio.run(simulator_loop())
