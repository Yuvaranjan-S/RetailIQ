"""Events API — Edge/Simulator event ingestion endpoint"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import List

from app.database.connection import get_db
from app.models.event import Event
from app.schemas.schemas import EventIn, EventBatchIn
from app.services.store_state_engine import get_store_twin
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/events", tags=["events"])


async def _process_event(event_in: EventIn, db: AsyncSession) -> None:
    """Save event to DB and update the store digital twin"""
    # Save to DB
    db_event = Event(
        store_id=event_in.store_id,
        event_type=event_in.event_type,
        source=event_in.source,
        zone_id=event_in.zone_id,
        payload=event_in.payload,
        confidence=event_in.confidence,
        timestamp=event_in.timestamp or datetime.now(timezone.utc),
        is_synced=True,
    )
    db.add(db_event)

    # Update twin (in-memory)
    twin = get_store_twin(event_in.store_id)
    if twin:
        await twin.update_from_event({
            "event_type": event_in.event_type,
            "zone_id": event_in.zone_id,
            "payload": event_in.payload,
        })


@router.post("")
async def ingest_event(
    event: EventIn,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Single event ingestion (edge pipeline)"""
    await _process_event(event, db)
    await db.commit()
    return {"accepted": True, "event_type": event.event_type}


@router.post("/batch")
async def ingest_events_batch(
    batch: EventBatchIn,
    db: AsyncSession = Depends(get_db),
):
    """Batch event ingestion (offline sync or bulk edge upload)"""
    accepted = 0
    for event_in in batch.events:
        try:
            await _process_event(event_in, db)
            accepted += 1
        except Exception as e:
            pass  # log and continue
    await db.commit()
    return {"accepted": accepted, "total": len(batch.events)}
