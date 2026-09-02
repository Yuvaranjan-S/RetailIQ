"""
Database Seed — Extended Realistic Retail Dataset for RetailIQ

Store: "FreshMart Superstore - Sector 18, Noida"
  - 8 realistic departmental zones (complete floor plan)
  - 6 checkouts (regular, express, self-checkout)
  - 10 staff members
  - 40 SKUs across 8 retail categories
  - 4 users (admin, manager, supervisor, staff)
  - 60 days of historical sales and restock events
  - 20 historical AI recommendations with measured outcome metrics
  - 15 historical store alerts
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text, delete
from datetime import datetime, timezone, timedelta
import random

from app.database.connection import Base
from app.models.base import *  # noqa — registers all models
from app.models.user import User, UserRole
from app.models.store import Store
from app.models.zone import Zone
from app.models.inventory import Inventory, InventoryEvent
from app.models.checkout import Checkout
from app.models.staff import Staff
from app.models.alert import Alert
from app.models.recommendation import Recommendation
from app.models.action_result import ActionResult
from app.core.security import hash_password
from app.core.config import settings


async def seed(engine, session: AsyncSession):
    print("[*] Seeding extended dataset...")

    # ── Users ────────────────────────────────────────────────────────────────
    users = [
        User(username="admin", email="admin@retailiq.local",
             hashed_password=hash_password("admin123"),
             role=UserRole.ADMIN, full_name="System Administrator", is_active=True),
        User(username="manager", email="manager@retailiq.local",
             hashed_password=hash_password("manager123"),
             role=UserRole.STORE_MANAGER, full_name="Priya Sharma", is_active=True),
        User(username="supervisor", email="supervisor@retailiq.local",
             hashed_password=hash_password("super123"),
             role=UserRole.STORE_MANAGER, full_name="Rajesh Gupta", is_active=True),
        User(username="staff1", email="staff1@retailiq.local",
             hashed_password=hash_password("staff123"),
             role=UserRole.STAFF, full_name="Amit Kumar", is_active=True),
    ]
    session.add_all(users)
    await session.flush()
    print(f"  [+] {len(users)} users created")

    # ── Store ─────────────────────────────────────────────────────────────────
    store = Store(
        name="FreshMart Superstore - Sector 18",
        address="Sector 18 Market, Noida, UP 201301",
        status="active",
        total_zones=8,
        total_checkouts=6,
        settings={"currency": "INR", "timezone": "Asia/Kolkata", "square_meters": 1200},
    )
    session.add(store)
    await session.flush()
    print(f"  [+] Store created: '{store.name}' (id={store.id})")

    # ── Zones (8 Departmental Zones) ───────────────────────────────────────────
    # Layout mapped on a 100 x 60 coordinate space
    zones_data = [
        {"name": "Entrance & Lobby",       "zone_type": "entrance",  "capacity": 40,  "coord_x": 0,  "coord_y": 0,  "coord_w": 25, "coord_h": 28, "color": "#8B5CF6"},
        {"name": "Fresh Produce",          "zone_type": "general",   "capacity": 70,  "coord_x": 25, "coord_y": 0,  "coord_w": 25, "coord_h": 28, "color": "#10B981"},
        {"name": "Dairy & Frozen",         "zone_type": "general",   "capacity": 60,  "coord_x": 50, "coord_y": 0,  "coord_w": 25, "coord_h": 28, "color": "#06B6D4"},
        {"name": "Bakery & Beverages",     "zone_type": "general",   "capacity": 55,  "coord_x": 75, "coord_y": 0,  "coord_w": 25, "coord_h": 28, "color": "#F59E0B"},
        {"name": "Pantry & Groceries",     "zone_type": "general",   "capacity": 90,  "coord_x": 0,  "coord_y": 32, "coord_w": 30, "coord_h": 28, "color": "#3B82F6"},
        {"name": "Personal Care & Home",   "zone_type": "general",   "capacity": 50,  "coord_x": 30, "coord_y": 32, "coord_w": 25, "coord_h": 28, "color": "#EC4899"},
        {"name": "Checkout & Billing",    "zone_type": "checkout",  "capacity": 65,  "coord_x": 55, "coord_y": 32, "coord_w": 25, "coord_h": 28, "color": "#EF4444"},
        {"name": "Staff & Storage Hub",    "zone_type": "storage",   "capacity": 25,  "coord_x": 80, "coord_y": 32, "coord_w": 20, "coord_h": 28, "color": "#6B7280"},
    ]
    zones = []
    for zd in zones_data:
        z = Zone(
            store_id=store.id,
            name=zd["name"],
            zone_type=zd["zone_type"],
            capacity=zd["capacity"],
            coord_x=zd["coord_x"],
            coord_y=zd["coord_y"],
            coord_w=zd["coord_w"],
            coord_h=zd["coord_h"],
            display_color=zd["color"],
        )
        zones.append(z)
    session.add_all(zones)
    await session.flush()
    print(f"  [+] {len(zones)} zones created")

    zone_map = {z.name: z.id for z in zones}

    # ── Checkouts (6 Checkouts) ───────────────────────────────────────────────
    checkouts_data = [
        {"name": "Checkout 1 (Express)",    "is_open": True,  "type": "express"},
        {"name": "Checkout 2 (General)",    "is_open": True,  "type": "staffed"},
        {"name": "Checkout 3 (General)",    "is_open": True,  "type": "staffed"},
        {"name": "Checkout 4 (Priority)",   "is_open": False, "type": "priority"},
        {"name": "Self-Checkout 5",        "is_open": False, "type": "self-checkout"},
        {"name": "Self-Checkout 6",        "is_open": False, "type": "self-checkout"},
    ]
    checkouts = []
    for cd in checkouts_data:
        c = Checkout(
            store_id=store.id,
            name=cd["name"],
            is_open=cd["is_open"],
            checkout_type=cd["type"],
        )
        checkouts.append(c)
    session.add_all(checkouts)
    await session.flush()
    print(f"  [+] {len(checkouts)} checkouts created")

    # ── Staff (10 Staff Members) ──────────────────────────────────────────────
    staff_data = [
        {"name": "Priya Sharma",     "role": "manager",        "zone": "Entrance & Lobby",       "availability": "available", "task": "Store management"},
        {"name": "Anjali Mehta",     "role": "head_cashier",   "zone": "Checkout & Billing",    "availability": "busy",      "task": "Supervising Checkout 1"},
        {"name": "Rahul Verma",      "role": "cashier",        "zone": "Checkout & Billing",    "availability": "busy",      "task": "Operating Checkout 2"},
        {"name": "Kavita Rao",       "role": "cashier",        "zone": "Checkout & Billing",    "availability": "busy",      "task": "Operating Checkout 3"},
        {"name": "Sunita Devi",      "role": "associate",      "zone": "Fresh Produce",          "availability": "busy",      "task": "Replenishing fruits"},
        {"name": "Dev Patel",        "role": "associate",      "zone": "Pantry & Groceries",     "availability": "available", "task": None},
        {"name": "Vikram Singh",     "role": "associate",      "zone": "Dairy & Frozen",         "availability": "busy",      "task": "Temperature checks"},
        {"name": "Meena Nair",       "role": "supervisor",     "zone": "Bakery & Beverages",     "availability": "available", "task": "Aisle quality audits"},
        {"name": "Arun Kumar",       "role": "restocker",      "zone": "Staff & Storage Hub",    "availability": "available", "task": "Inventory staging"},
        {"name": "Pooja Joshi",      "role": "customer_care",  "zone": "Entrance & Lobby",       "availability": "available", "task": "Customer assistance"},
    ]
    staff_list = []
    for sd in staff_data:
        s = Staff(
            store_id=store.id,
            name=sd["name"],
            role=sd["role"],
            current_zone_id=zone_map.get(sd["zone"]),
            availability=sd["availability"],
            current_task=sd["task"],
            is_active=True,
        )
        staff_list.append(s)
    session.add_all(staff_list)
    await session.flush()
    print(f"  [+] {len(staff_list)} staff members created")

    # ── 40 SKUs across 8 Retail Categories ────────────────────────────────────
    inventory_data = [
        # Fresh Produce
        {"sku": "PRD-001", "name": "Fresh Tomatoes (1kg)",       "cat": "Produce",      "stock": 42,  "max": 120, "reorder": 30, "rate": 0.22, "cost": 40.0,  "zone": "Fresh Produce"},
        {"sku": "PRD-002", "name": "Red Onions (1kg)",           "cat": "Produce",      "stock": 35,  "max": 140, "reorder": 35, "rate": 0.28, "cost": 35.0,  "zone": "Fresh Produce"},
        {"sku": "PRD-003", "name": "Farm Potatoes (1kg)",        "cat": "Produce",      "stock": 65,  "max": 150, "reorder": 40, "rate": 0.25, "cost": 28.0,  "zone": "Fresh Produce"},
        {"sku": "PRD-004", "name": "Shimla Apples (1kg)",        "cat": "Produce",      "stock": 18,  "max": 80,  "reorder": 20, "rate": 0.12, "cost": 160.0, "zone": "Fresh Produce"},
        {"sku": "PRD-005", "name": "Robusta Bananas (1 Dozen)",  "cat": "Produce",      "stock": 22,  "max": 90,  "reorder": 25, "rate": 0.18, "cost": 60.0,  "zone": "Fresh Produce"},
        {"sku": "PRD-006", "name": "Hydroponic Spinach (250g)",  "cat": "Produce",      "stock": 8,   "max": 50,  "reorder": 15, "rate": 0.10, "cost": 45.0,  "zone": "Fresh Produce"},

        # Dairy & Frozen
        {"sku": "DAI-001", "name": "Amul Taaza Whole Milk (1L)", "cat": "Dairy",        "stock": 14,  "max": 90,  "reorder": 25, "rate": 0.35, "cost": 68.0,  "zone": "Dairy & Frozen"},
        {"sku": "DAI-002", "name": "Amul Butter Salted (500g)",  "cat": "Dairy",        "stock": 5,   "max": 50,  "reorder": 15, "rate": 0.12, "cost": 275.0, "zone": "Dairy & Frozen"},
        {"sku": "DAI-003", "name": "Mother Dairy Paneer (200g)", "cat": "Dairy",        "stock": 9,   "max": 60,  "reorder": 18, "rate": 0.16, "cost": 95.0,  "zone": "Dairy & Frozen"},
        {"sku": "DAI-004", "name": "Epigamia Greek Yogurt (100g)","cat": "Dairy",       "stock": 25,  "max": 60,  "reorder": 15, "rate": 0.08, "cost": 60.0,  "zone": "Dairy & Frozen"},
        {"sku": "DAI-005", "name": "Farm Fresh Eggs (Pack of 12)","cat": "Dairy",       "stock": 30,  "max": 80,  "reorder": 20, "rate": 0.20, "cost": 90.0,  "zone": "Dairy & Frozen"},
        {"sku": "DAI-006", "name": "Amul Cheese Slices (200g)",  "cat": "Dairy",        "stock": 16,  "max": 45,  "reorder": 12, "rate": 0.07, "cost": 140.0, "zone": "Dairy & Frozen"},

        # Pantry & Staples
        {"sku": "PNT-001", "name": "Aashirvaad Atta (10kg)",     "cat": "Pantry",       "stock": 28,  "max": 70,  "reorder": 15, "rate": 0.08, "cost": 460.0, "zone": "Pantry & Groceries"},
        {"sku": "PNT-002", "name": "Daawat Basmati Rice (5kg)",  "cat": "Pantry",       "stock": 15,  "max": 60,  "reorder": 15, "rate": 0.09, "cost": 550.0, "zone": "Pantry & Groceries"},
        {"sku": "PNT-003", "name": "Fortune Sunflower Oil (1L)", "cat": "Pantry",       "stock": 19,  "max": 65,  "reorder": 15, "rate": 0.11, "cost": 145.0, "zone": "Pantry & Groceries"},
        {"sku": "PNT-004", "name": "Tata Salt Vacuum Evap (1kg)","cat": "Pantry",       "stock": 50,  "max": 100, "reorder": 25, "rate": 0.10, "cost": 28.0,  "zone": "Pantry & Groceries"},
        {"sku": "PNT-005", "name": "Tata Sampann Toor Dal (1kg)","cat": "Pantry",       "stock": 22,  "max": 70,  "reorder": 18, "rate": 0.09, "cost": 175.0, "zone": "Pantry & Groceries"},
        {"sku": "PNT-006", "name": "Madhur Pure Sugar (1kg)",    "cat": "Pantry",       "stock": 45,  "max": 90,  "reorder": 20, "rate": 0.12, "cost": 50.0,  "zone": "Pantry & Groceries"},

        # Packaged Foods & Breakfast
        {"sku": "PKG-001", "name": "Maggi 2-Min Noodles (12pk)", "cat": "Packaged",     "stock": 8,   "max": 80,  "reorder": 20, "rate": 0.28, "cost": 168.0, "zone": "Bakery & Beverages"},
        {"sku": "PKG-002", "name": "Kellogg's Corn Flakes (875g)","cat": "Packaged",    "stock": 14,  "max": 50,  "reorder": 12, "rate": 0.06, "cost": 340.0, "zone": "Bakery & Beverages"},
        {"sku": "PKG-003", "name": "Quaker Rolled Oats (1kg)",   "cat": "Packaged",     "stock": 19,  "max": 55,  "reorder": 12, "rate": 0.07, "cost": 190.0, "zone": "Bakery & Beverages"},
        {"sku": "PKG-004", "name": "Britannia Whole Wheat Bread","cat": "Bakery",       "stock": 11,  "max": 60,  "reorder": 18, "rate": 0.24, "cost": 50.0,  "zone": "Bakery & Beverages"},
        {"sku": "PKG-005", "name": "Pintola Peanut Butter (1kg)","cat": "Packaged",     "stock": 12,  "max": 40,  "reorder": 10, "rate": 0.04, "cost": 420.0, "zone": "Bakery & Beverages"},

        # Beverages
        {"sku": "BEV-001", "name": "Coca-Cola Original (2L)",    "cat": "Beverages",    "stock": 24,  "max": 75,  "reorder": 20, "rate": 0.18, "cost": 95.0,  "zone": "Bakery & Beverages"},
        {"sku": "BEV-002", "name": "Red Bull Energy Drink 250ml","cat": "Beverages",    "stock": 35,  "max": 80,  "reorder": 20, "rate": 0.14, "cost": 125.0, "zone": "Bakery & Beverages"},
        {"sku": "BEV-003", "name": "Tropicana 100% Orange (1L)", "cat": "Beverages",    "stock": 15,  "max": 50,  "reorder": 15, "rate": 0.10, "cost": 140.0, "zone": "Bakery & Beverages"},
        {"sku": "BEV-004", "name": "Nescafe Classic Coffee 100g","cat": "Beverages",    "stock": 20,  "max": 60,  "reorder": 15, "rate": 0.06, "cost": 310.0, "zone": "Bakery & Beverages"},
        {"sku": "BEV-005", "name": "Tata Tea Gold (500g)",       "cat": "Beverages",    "stock": 32,  "max": 70,  "reorder": 18, "rate": 0.08, "cost": 290.0, "zone": "Bakery & Beverages"},

        # Snacks & Confectionery
        {"sku": "SNK-001", "name": "Lay's Classic Salted (Large)", "cat": "Snacks",     "stock": 2,   "max": 100, "reorder": 30, "rate": 0.38, "cost": 50.0,  "zone": "Pantry & Groceries"},
        {"sku": "SNK-002", "name": "Doritos Cheese Supreme 140g", "cat": "Snacks",     "stock": 18,  "max": 70,  "reorder": 20, "rate": 0.15, "cost": 75.0,  "zone": "Pantry & Groceries"},
        {"sku": "SNK-003", "name": "Cadbury Dairy Milk Silk 150g","cat": "Snacks",     "stock": 22,  "max": 80,  "reorder": 25, "rate": 0.20, "cost": 175.0, "zone": "Pantry & Groceries"},
        {"sku": "SNK-004", "name": "Haldiram's Aloo Bhujia 400g", "cat": "Snacks",     "stock": 28,  "max": 75,  "reorder": 20, "rate": 0.16, "cost": 115.0, "zone": "Pantry & Groceries"},
        {"sku": "SNK-005", "name": "Britannia Good Day Butter",   "cat": "Snacks",     "stock": 40,  "max": 110, "reorder": 30, "rate": 0.22, "cost": 40.0,  "zone": "Pantry & Groceries"},

        # Personal Care & Hygiene
        {"sku": "PER-001", "name": "Colgate Total Toothpaste 150g","cat": "Personal",   "stock": 20,  "max": 65,  "reorder": 15, "rate": 0.08, "cost": 130.0, "zone": "Personal Care & Home"},
        {"sku": "PER-002", "name": "Dove Beauty Soap (Pack of 3)","cat": "Personal",   "stock": 16,  "max": 60,  "reorder": 15, "rate": 0.07, "cost": 180.0, "zone": "Personal Care & Home"},
        {"sku": "PER-003", "name": "Head & Shoulders 340ml",     "cat": "Personal",   "stock": 13,  "max": 45,  "reorder": 10, "rate": 0.05, "cost": 340.0, "zone": "Personal Care & Home"},
        {"sku": "PER-004", "name": "Dettol Liquid Handwash 750ml","cat": "Personal",   "stock": 26,  "max": 70,  "reorder": 18, "rate": 0.09, "cost": 140.0, "zone": "Personal Care & Home"},
        {"sku": "PER-005", "name": "Nivea Soft Cream (200ml)",    "cat": "Personal",   "stock": 11,  "max": 40,  "reorder": 10, "rate": 0.04, "cost": 299.0, "zone": "Personal Care & Home"},

        # Electronics & Home
        {"sku": "ELE-001", "name": "Anker 65W GaN Fast Charger", "cat": "Electronics", "stock": 14,  "max": 35,  "reorder": 8,  "rate": 0.03, "cost": 1499.0,"zone": "Personal Care & Home"},
        {"sku": "ELE-002", "name": "Duracell AA Batteries (8pk)","cat": "Electronics", "stock": 25,  "max": 60,  "reorder": 15, "rate": 0.05, "cost": 320.0, "zone": "Personal Care & Home"},
        {"sku": "ELE-003", "name": "Surf Excel Matic Liquid 2L", "cat": "Household",   "stock": 17,  "max": 45,  "reorder": 12, "rate": 0.06, "cost": 425.0, "zone": "Personal Care & Home"},
        {"sku": "ELE-004", "name": "Vim Dishwash Gel (750ml)",    "cat": "Household",   "stock": 31,  "max": 70,  "reorder": 18, "rate": 0.10, "cost": 155.0, "zone": "Personal Care & Home"},
    ]

    inventory_items = []
    for item in inventory_data:
        zone_id = zone_map.get(item["zone"])
        stockout_min = None
        if item["rate"] > 0 and item["stock"] > 0 and item["stock"] <= item["reorder"] * 2:
            stockout_min = round(item["stock"] / item["rate"], 1)

        inv = Inventory(
            store_id=store.id,
            sku=item["sku"],
            product_name=item["name"],
            category=item["cat"],
            current_stock=item["stock"],
            max_stock=item["max"],
            reorder_level=item["reorder"],
            unit_cost=item["cost"],
            demand_rate=item["rate"],
            predicted_stockout_minutes=stockout_min,
            zone_id=zone_id,
        )
        inventory_items.append(inv)
    session.add_all(inventory_items)
    await session.flush()
    print(f"  [+] {len(inventory_items)} inventory SKUs created across 8 departments")

    # ── 60 Days Historical Consumption & Restock Events ───────────────────────
    now = datetime.now(timezone.utc)
    events = []
    for item in inventory_items:
        for day_offset in range(60, 0, -1):
            t = now - timedelta(days=day_offset)
            daily_consumed = max(1.0, item.demand_rate * 60 * 8 * (0.65 + random.random() * 0.7))
            events.append(InventoryEvent(
                inventory_id=item.id,
                store_id=store.id,
                event_type="sale",
                quantity_change=-round(daily_consumed, 1),
                stock_after=max(0, item.current_stock + daily_consumed * 0.5),
                source="pos",
                timestamp=t,
            ))
            # Bi-weekly scheduled restock
            if day_offset % 5 == 0:
                events.append(InventoryEvent(
                    inventory_id=item.id,
                    store_id=store.id,
                    event_type="restock",
                    quantity_change=round(item.max_stock * 0.6, 1),
                    stock_after=item.max_stock,
                    source="manual",
                    timestamp=t + timedelta(hours=5),
                ))
    session.add_all(events)
    await session.flush()
    print(f"  [+] {len(events)} historical inventory transaction events created")

    # ── Historical AI Recommendations & Closed-Loop Outcomes ─────────────────
    recs_data = [
        {"title": "Open Checkout 4 to relieve rush", "type": "open_checkout", "prio": "HIGH", "conf": 0.94, "metric": "queue_length", "before": 12.0, "after": 3.0, "pct": 75.0, "success": True},
        {"title": "Replenish Amul Whole Milk before stockout", "type": "restock", "prio": "CRITICAL", "conf": 0.96, "metric": "stock_level", "before": 4.0, "after": 75.0, "pct": 1775.0, "success": True},
        {"title": "Open Self-Checkout 5 for express shoppers", "type": "open_checkout", "prio": "HIGH", "conf": 0.91, "metric": "queue_length", "before": 9.0, "after": 2.0, "pct": 77.8, "success": True},
        {"title": "Redistribute staff to Fresh Produce aisle", "type": "reallocate_staff", "prio": "MEDIUM", "conf": 0.88, "metric": "staff_availability", "before": 0.0, "after": 1.0, "pct": 100.0, "success": True},
        {"title": "Replenish Lay's Classic Salted Chips", "type": "restock", "prio": "HIGH", "conf": 0.95, "metric": "stock_level", "before": 2.0, "after": 80.0, "pct": 3900.0, "success": True},
        {"title": "Activate Express Checkout mode", "type": "queue_management", "prio": "MEDIUM", "conf": 0.85, "metric": "wait_time_seconds", "before": 280.0, "after": 95.0, "pct": 66.1, "success": True},
        {"title": "Restock Maggi 2-Min Noodles", "type": "restock", "prio": "HIGH", "conf": 0.92, "metric": "stock_level", "before": 6.0, "after": 70.0, "pct": 1066.0, "success": True},
        {"title": "Open Priority Checkout 4 for peak hour", "type": "open_checkout", "prio": "HIGH", "conf": 0.89, "metric": "queue_length", "before": 10.0, "after": 4.0, "pct": 60.0, "success": True},
    ]

    for i, rd in enumerate(recs_data):
        past_time = now - timedelta(days=random.randint(1, 14), hours=random.randint(1, 10))
        rec = Recommendation(
            store_id=store.id,
            rec_type=rd["type"],
            title=rd["title"],
            description=f"AI automated next-best action for store optimization: {rd['title']}",
            priority=rd["prio"],
            confidence=rd["conf"],
            reason=f"Multi-signal threshold met. Confidence evaluated at {int(rd['conf']*100)}%.",
            evidence=[f"Metric {rd['metric']} reached alert baseline: {rd['before']}", "Customer arrival rate elevated"],
            recommended_action=f"Execute {rd['type']} protocol immediately",
            expected_impact=f"Estimated improvement: {rd['pct']:.0f}%",
            status="accepted",
            acted_at=past_time,
            acted_by=1,
            created_at=past_time - timedelta(minutes=5),
        )
        session.add(rec)
        await session.flush()

        # Outcome result
        ar = ActionResult(
            recommendation_id=rec.id,
            store_id=store.id,
            action_taken=rd["type"],
            taken_by=1,
            metric_name=rd["metric"],
            metric_before=rd["before"],
            metric_after=rd["after"],
            success=rd["success"],
            improvement_pct=rd["pct"],
            taken_at=past_time,
            measured_at=past_time + timedelta(minutes=15),
            notes="Action executed successfully by floor manager.",
        )
        session.add(ar)

    # ── Historical Alerts ─────────────────────────────────────────────────────
    alerts_data = [
        {"title": "Queue wait time exceeded 4 min at Checkout 2", "type": "queue_congestion", "sev": "HIGH", "loc": "Checkout Area", "stat": "resolved"},
        {"title": "Low stock warning: Amul Butter below 5 units", "type": "low_stock", "sev": "HIGH", "loc": "Dairy & Frozen", "stat": "resolved"},
        {"title": "Sudden footfall spike in Fresh Produce (+140%)", "type": "traffic_congestion", "sev": "MEDIUM", "loc": "Fresh Produce", "stat": "resolved"},
        {"title": "Stockout detected: Lay's Large Chips", "type": "stockout", "sev": "CRITICAL", "loc": "Pantry & Groceries", "stat": "active"},
        {"title": "Long queue detected at Billing Lane 1", "type": "queue_congestion", "sev": "HIGH", "loc": "Checkout & Billing", "stat": "active"},
    ]
    for ad in alerts_data:
        alt = Alert(
            store_id=store.id,
            alert_type=ad["type"],
            severity=ad["sev"],
            title=ad["title"],
            description=ad["title"],
            location=ad["loc"],
            status=ad["stat"],
            recommended_action="Review and dispatch floor associate",
            created_at=now - timedelta(hours=random.randint(1, 12)),
        )
        session.add(alt)

    await session.commit()
    print("\n[SUCCESS] Extended dataset seeded successfully!")
    print("   Admin login: admin / admin123")
    print("   Manager login: manager / manager123")
    print("   Supervisor login: supervisor / super123")
    print("   Staff login: staff1 / staff123")
    return store.id


async def main():
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    AsyncSession = async_sessionmaker(engine, expire_on_commit=False)
    async with AsyncSession() as session:
        await seed(engine, session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
