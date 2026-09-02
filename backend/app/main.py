"""
RetailIQ — Main FastAPI Application

Startup sequence:
  1. Create DB tables
  2. Seed if empty
  3. Load store state into digital twin
  4. Start decision engine background loop
  5. Start WebSocket broadcaster loop
"""
import asyncio
import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.database.connection import engine, Base, AsyncSessionLocal, init_db
from app.websocket.manager import ws_manager
from app.services.store_state_engine import StoreStateTwin, register_store_twin, get_store_twin
from app.decision_engine.recommendation_engine import RecommendationEngine

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
)
logger = logging.getLogger("retailiq.main")

# ─── Global instances ─────────────────────────────────────────────────────────
decision_engine: RecommendationEngine = None
_bg_tasks: list = []


async def _init_store_twin() -> StoreStateTwin:
    """Load store data from DB and initialize the digital twin"""
    from sqlalchemy import select
    from app.models.store import Store
    from app.models.zone import Zone
    from app.models.checkout import Checkout
    from app.models.inventory import Inventory
    from app.models.staff import Staff

    async with AsyncSessionLocal() as db:
        # Get first active store
        result = await db.execute(select(Store).where(Store.status == "active").limit(1))
        store = result.scalar_one_or_none()
        if not store:
            logger.warning("No store found in DB — twin not initialized")
            return None

        twin = StoreStateTwin(store_id=store.id, store_name=store.name)
        twin.simulation_mode = settings.SIMULATION_MODE

        # Load zones
        result = await db.execute(select(Zone).where(Zone.store_id == store.id))
        zones = result.scalars().all()
        twin.initialize_zones([{
            "id": z.id, "name": z.name, "zone_type": z.zone_type,
            "coord_x": z.coord_x, "coord_y": z.coord_y,
            "coord_w": z.coord_w, "coord_h": z.coord_h,
            "display_color": z.display_color,
        } for z in zones])

        # Load checkouts
        result = await db.execute(select(Checkout).where(Checkout.store_id == store.id))
        checkouts = result.scalars().all()
        twin.initialize_checkouts([{
            "id": c.id, "name": c.name, "is_open": c.is_open,
            "checkout_type": c.checkout_type,
        } for c in checkouts])

        # Load inventory
        result = await db.execute(
            select(Inventory).where(Inventory.store_id == store.id, Inventory.is_active == True)
        )
        items = result.scalars().all()
        twin.initialize_inventory([{
            "id": i.id, "sku": i.sku, "product_name": i.product_name,
            "category": i.category, "current_stock": i.current_stock,
            "max_stock": i.max_stock, "reorder_level": i.reorder_level,
            "demand_rate": i.demand_rate or 0.0,
        } for i in items])

        # Load staff
        result = await db.execute(
            select(Staff).where(Staff.store_id == store.id, Staff.is_active == True)
        )
        staff = result.scalars().all()
        twin.initialize_staff([{
            "id": s.id, "name": s.name, "role": s.role,
            "current_zone_id": s.current_zone_id,
            "availability": s.availability,
        } for s in staff])

        register_store_twin(twin)
        logger.info(
            f"✅ Store twin initialized: '{store.name}' — "
            f"{len(zones)} zones, {len(checkouts)} checkouts, "
            f"{len(items)} SKUs, {len(staff)} staff"
        )
        return twin


async def _decision_engine_loop(twin: StoreStateTwin):
    """Background task: run decision engine every 10 seconds"""
    global decision_engine
    logger.info("🧠 Decision engine loop started")
    while True:
        try:
            await asyncio.sleep(10)
            await decision_engine.run_cycle(twin)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Decision engine error: {e}", exc_info=True)


async def _store_broadcast_loop(twin: StoreStateTwin):
    """Background task: broadcast twin snapshot via WebSocket every 3 seconds"""
    logger.info("📡 Store broadcast loop started")
    while True:
        try:
            await asyncio.sleep(3)
            snapshot = twin.snapshot()
            await ws_manager.broadcast(twin.store_id, snapshot)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Broadcast error: {e}")


# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global decision_engine

    # 1. Create DB tables
    logger.info("🗄 Initializing database tables...")
    await init_db()

    # 2. Seed if empty
    try:
        from app.database.seed import seed
        from sqlalchemy import text
        async with AsyncSessionLocal() as db:
            result = await db.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            if count == 0:
                logger.info("🌱 Seeding database with demo data...")
                await seed(engine, db)
    except Exception as e:
        logger.warning(f"Seeding skipped or failed: {e}")

    # 3. Initialize store twin
    twin = await _init_store_twin()

    if twin:
        # 4. Start decision engine
        decision_engine = RecommendationEngine(
            db_session_factory=AsyncSessionLocal,
            ws_broadcaster=ws_manager,
        )

        # 5. Start background loops
        t1 = asyncio.create_task(_decision_engine_loop(twin))
        t2 = asyncio.create_task(_store_broadcast_loop(twin))
        _bg_tasks.extend([t1, t2])
        logger.info("🚀 RetailIQ backend started successfully")
    else:
        logger.error("⚠ Store twin not initialized — run seed first")

    yield  # App is running

    # Shutdown
    for task in _bg_tasks:
        task.cancel()
    logger.info("🛑 RetailIQ backend shutting down")


# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="RetailIQ API",
    description="Edge-First AI Retail Operating & Decision System — SIH 2026",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Include Routers ──────────────────────────────────────────────────────────
from app.api import auth, store, inventory, alerts, recommendations, events, analytics, simulation, system

app.include_router(auth.router, prefix="/api")
app.include_router(store.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(simulation.router, prefix="/api")
app.include_router(system.router, prefix="/api")


# ─── WebSocket Endpoint ───────────────────────────────────────────────────────
@app.websocket("/ws/store")
async def websocket_store(websocket: WebSocket, store_id: int = 1):
    await ws_manager.connect(websocket, store_id)
    try:
        # Send immediate snapshot on connect
        twin = get_store_twin(store_id)
        if twin:
            await websocket.send_text(json.dumps(twin.snapshot()))

        # Keep alive — receive pings
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WS error: {e}")
    finally:
        await ws_manager.disconnect(websocket, store_id)


# ─── Root ─────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "name": "RetailIQ API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
        "ws": "/ws/store",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
