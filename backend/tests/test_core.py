"""
RetailIQ — Comprehensive Test Suite
Tests:
1. Mathematical AI Queue Predictor (M/M/c Erlang-C model)
2. EMA Demand Predictor & Stockout ETA
3. Rule Engine & Signal Fusion
4. Store State Twin (Digital Twin Engine)
"""
import pytest
from app.ai.queue_predictor import (
    erlang_c,
    expected_wait_time,
    predict_queue,
)
from app.ai.demand_predictor import (
    compute_demand_rate_ema,
    predict_stockout,
    compute_inventory_urgency,
)
from app.decision_engine.rule_engine import evaluate_rules
from app.decision_engine.signal_fusion import fuse_signals, boost_confidence_from_fusion
from app.services.store_state_engine import StoreStateTwin


def test_erlang_c_and_queue_predictor():
    # 2 servers, lam=3.0 cust/min, mu=2.0 cust/min/server -> rho = 3 / (2*2) = 0.75
    c = 2
    lam = 3.0
    mu = 2.0
    prob_wait = erlang_c(lam, mu, c)
    assert 0.0 < prob_wait < 1.0

    wait_time = expected_wait_time(lam, mu, c)
    assert wait_time > 0

    # Full predictor test
    pred = predict_queue(
        current_queue=6,
        arrival_rate=2.5,
        service_rate=1.5,
        open_checkouts=2,
    )
    assert pred["predicted_wait_seconds"] > 0
    assert pred["recommended_checkouts"] >= 2
    assert "trend" in pred
    assert pred["confidence"] > 0.5


def test_ema_demand_and_stockout():
    current_stock = 15.0
    demand_rate = 0.5  # 0.5 units/min
    minutes = predict_stockout(current_stock, demand_rate)
    assert minutes == 30.0

    urgency = compute_inventory_urgency(
        current_stock=current_stock,
        max_stock=60.0,
        reorder_level=20.0,
        demand_rate=demand_rate,
        predicted_stockout_minutes=minutes,
        footfall=50,
    )
    assert 0.0 <= urgency <= 1.0


def test_rule_engine_and_signal_fusion():
    ctx = {
        "current_footfall": 55,
        "total_queue_length": 10,
        "max_wait_seconds": 320,
        "closed_checkout_list": [{"id": 3, "name": "Checkout 3"}],
        "available_staff_list": [{"id": 4, "name": "Dev Patel"}],
        "critical_inventory": [{"id": 10, "product_name": "Lay's Chips", "sku": "PRD-010", "stock_status": "out", "category": "Snacks", "demand_rate": 0.25}],
        "imminent_stockouts": [{"id": 3, "product_name": "Whole Milk", "sku": "PRD-003", "stock_status": "low", "predicted_stockout_minutes": 12, "demand_rate": 0.2, "current_stock": 2.4, "reorder_level": 15, "max_stock": 60}],
        "low_inventory": [],
        "staff": {1: {}, 2: {}},
        "inventory": {1: {}, 2: {}, 3: {}, 10: {}},
        "closed_checkouts": 2,
    }

    fusion = fuse_signals(ctx)
    assert fusion["compound_score"] > 0
    assert fusion["store_stress_level"] in ("HIGH", "CRITICAL", "MEDIUM")

    rules = evaluate_rules(ctx)
    assert len(rules) >= 2  # Stockout + Checkout needed + imminent stockout
    rule_ids = [r.rule_id for r in rules]
    assert "STOCKOUT" in rule_ids
    assert "CHECKOUT_NEEDED" in rule_ids


def test_store_state_twin():
    twin = StoreStateTwin(store_id=1, store_name="Test Store")
    twin.initialize_zones([
        {"id": 1, "name": "Entrance", "zone_type": "entrance", "coord_x": 0, "coord_y": 0, "coord_w": 30, "coord_h": 25, "display_color": "#8B5CF6"},
        {"id": 5, "name": "Checkout Area", "zone_type": "checkout", "coord_x": 40, "coord_y": 35, "coord_w": 35, "coord_h": 25, "display_color": "#EF4444"},
    ])
    twin.initialize_checkouts([
        {"id": 1, "name": "Checkout 1", "is_open": True, "checkout_type": "staffed"},
        {"id": 2, "name": "Checkout 2", "is_open": False, "checkout_type": "staffed"},
    ])
    twin.initialize_inventory([
        {"id": 1, "sku": "PRD-001", "product_name": "Tomatoes", "category": "Produce", "current_stock": 20, "max_stock": 100, "reorder_level": 25, "demand_rate": 0.2},
    ])
    twin.initialize_staff([
        {"id": 1, "name": "Alice", "role": "cashier", "current_zone_id": 5, "availability": "available"},
    ])

    snapshot = twin.snapshot()
    assert snapshot["store_id"] == 1
    assert len(snapshot["zones"]) == 2
    assert len(snapshot["checkouts"]) == 2
    assert snapshot["low_stock_count"] >= 1
