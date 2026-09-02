"""Recommendations API — ACCEPT / REJECT / MODIFY + outcome recording"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from datetime import datetime, timezone
from typing import Optional

from app.database.connection import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.recommendation import Recommendation
from app.models.action_result import ActionResult
from app.schemas.schemas import RecommendationOut, RecommendationAction
from app.services.store_state_engine import get_store_twin

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("")
async def get_recommendations(
    store_id: int = 1,
    status: Optional[str] = Query("pending"),
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Recommendation)
        .where(Recommendation.store_id == store_id)
        .order_by(desc(Recommendation.created_at))
        .limit(limit)
    )
    if status and status != "all":
        query = query.where(Recommendation.status == status)
    result = await db.execute(query)
    recs = result.scalars().all()
    return {
        "recommendations": [RecommendationOut.model_validate(r).model_dump() for r in recs],
        "count": len(recs),
    }


@router.post("/{rec_id}/accept")
async def accept_recommendation(
    rec_id: int,
    body: RecommendationAction = RecommendationAction(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rec = await _get_rec(rec_id, db)
    await db.execute(
        update(Recommendation).where(Recommendation.id == rec_id).values(
            status="accepted",
            acted_at=datetime.now(timezone.utc),
            acted_by=current_user.id,
        )
    )

    # Capture before-metric from twin
    metric_before = _capture_metric(rec)

    action_result = ActionResult(
        recommendation_id=rec_id,
        store_id=rec.store_id,
        action_taken=rec.rec_type,
        taken_by=current_user.id,
        metric_name=_metric_name(rec.rec_type),
        metric_before=metric_before,
        notes=body.notes,
    )
    db.add(action_result)
    await db.commit()

    # Simulate the action on the twin
    await _simulate_action(rec, db)

    return {
        "success": True,
        "rec_id": rec_id,
        "status": "accepted",
        "message": f"Recommendation accepted by {current_user.username}",
    }


@router.post("/{rec_id}/reject")
async def reject_recommendation(
    rec_id: int,
    body: RecommendationAction = RecommendationAction(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_rec(rec_id, db)
    await db.execute(
        update(Recommendation).where(Recommendation.id == rec_id).values(
            status="rejected",
            acted_at=datetime.now(timezone.utc),
            acted_by=current_user.id,
        )
    )
    await db.commit()
    return {"success": True, "rec_id": rec_id, "status": "rejected"}


@router.get("/{rec_id}/result")
async def get_recommendation_result(
    rec_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ActionResult).where(ActionResult.recommendation_id == rec_id)
    )
    ar = result.scalar_one_or_none()
    if not ar:
        raise HTTPException(404, "No result recorded yet")
    return {
        "recommendation_id": rec_id,
        "action_taken": ar.action_taken,
        "metric_name": ar.metric_name,
        "metric_before": ar.metric_before,
        "metric_after": ar.metric_after,
        "success": ar.success,
        "improvement_pct": ar.improvement_pct,
        "taken_at": ar.taken_at.isoformat() if ar.taken_at else None,
    }


@router.get("/history/outcomes")
async def get_outcomes(
    store_id: int = 1,
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all completed action results for AI performance analytics"""
    result = await db.execute(
        select(ActionResult, Recommendation.title, Recommendation.rec_type)
        .join(Recommendation, ActionResult.recommendation_id == Recommendation.id)
        .where(Recommendation.store_id == store_id)
        .order_by(desc(ActionResult.taken_at))
        .limit(limit)
    )
    rows = result.all()
    outcomes = []
    for ar, title, rec_type in rows:
        outcomes.append({
            "recommendation_id": ar.recommendation_id,
            "title": title,
            "rec_type": rec_type,
            "action_taken": ar.action_taken,
            "metric_name": ar.metric_name,
            "metric_before": ar.metric_before,
            "metric_after": ar.metric_after,
            "success": ar.success,
            "improvement_pct": ar.improvement_pct,
            "taken_at": ar.taken_at.isoformat() if ar.taken_at else None,
        })
    return {"outcomes": outcomes, "count": len(outcomes)}


# ─── Helpers ─────────────────────────────────────────────────────────────────
async def _get_rec(rec_id: int, db: AsyncSession) -> Recommendation:
    result = await db.execute(select(Recommendation).where(Recommendation.id == rec_id))
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(404, f"Recommendation {rec_id} not found")
    return rec


def _metric_name(rec_type: str) -> str:
    mapping = {
        "open_checkout": "queue_length",
        "restock": "stock_level",
        "reallocate_staff": "staff_availability",
        "queue_management": "wait_time_seconds",
    }
    return mapping.get(rec_type, "generic_metric")


def _capture_metric(rec: Recommendation) -> Optional[float]:
    """Read current metric value from the twin before action"""
    twin = get_store_twin(rec.store_id)
    if not twin:
        return None
    if rec.rec_type == "open_checkout":
        return float(sum(c.queue_length for c in twin.checkouts.values()))
    if rec.rec_type == "restock" and rec.inventory_id and rec.inventory_id in twin.inventory:
        return twin.inventory[rec.inventory_id].current_stock
    return None


async def _simulate_action(rec: Recommendation, db: AsyncSession) -> None:
    """
    Simulate the effect of an accepted recommendation on the digital twin.
    This makes the demo feel real — accepting 'Open Checkout 4' actually opens it.
    """
    from sqlalchemy import update as sql_update
    from app.models.checkout import Checkout

    twin = get_store_twin(rec.store_id)
    if not twin:
        return

    if rec.rec_type == "open_checkout" and rec.checkout_id:
        # Open the checkout in the twin
        if rec.checkout_id in twin.checkouts:
            twin.checkouts[rec.checkout_id].is_open = True
            twin.checkouts[rec.checkout_id].staff_count = 1
        # Persist to DB
        await db.execute(
            sql_update(Checkout).where(Checkout.id == rec.checkout_id).values(is_open=True)
        )
        await db.commit()

    elif rec.rec_type == "restock" and rec.inventory_id:
        if rec.inventory_id in twin.inventory:
            item = twin.inventory[rec.inventory_id]
            restock_qty = item.max_stock * 0.6  # restock to 60% capacity
            item.current_stock = min(item.max_stock, item.current_stock + restock_qty)
            item.predicted_stockout_minutes = None
