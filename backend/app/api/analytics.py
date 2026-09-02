"""Analytics API — footfall, heatmap, queue trends, AI performance"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.database.connection import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.zone import ZoneSnapshot, Zone
from app.models.queue import QueueSnapshot
from app.models.recommendation import Recommendation
from app.models.action_result import ActionResult
from app.services.store_state_engine import get_store_twin

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _time_filter(range_str: str) -> datetime:
    now = datetime.now(timezone.utc)
    if range_str == "1h":
        return now - timedelta(hours=1)
    if range_str == "24h":
        return now - timedelta(hours=24)
    if range_str == "7d":
        return now - timedelta(days=7)
    if range_str == "30d":
        return now - timedelta(days=30)
    return now - timedelta(hours=24)


@router.get("/footfall")
async def get_footfall(
    store_id: int = 1,
    range: str = Query("24h"),
    current_user: User = Depends(get_current_user),
):
    """Return footfall sparkline from twin history"""
    twin = get_store_twin(store_id)
    if twin:
        history = twin.footfall_history[-120:]
        return {
            "range": range,
            "data": history,
            "current": twin.current_footfall,
            "total_today": twin.total_customers_today,
        }
    return {"range": range, "data": [], "current": 0, "total_today": 0}


@router.get("/heatmap")
async def get_heatmap(
    store_id: int = 1,
    current_user: User = Depends(get_current_user),
):
    """Zone heatmap data for the store map"""
    twin = get_store_twin(store_id)
    if twin:
        heatmap = [
            {
                "zone_id": z.zone_id,
                "zone_name": z.name,
                "heat_score": z.heat_score,
                "people_count": z.people_count,
                "traffic_level": z.traffic_level,
                "coord_x": z.coord_x,
                "coord_y": z.coord_y,
                "coord_w": z.coord_w,
                "coord_h": z.coord_h,
                "display_color": z.display_color,
            }
            for z in twin.zones.values()
        ]
        return {"heatmap": heatmap, "timestamp": datetime.now(timezone.utc).isoformat()}
    return {"heatmap": [], "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/queue-trends")
async def get_queue_trends(
    store_id: int = 1,
    current_user: User = Depends(get_current_user),
):
    twin = get_store_twin(store_id)
    if twin:
        return {
            "history": twin.queue_history[-60:],
            "current_total": sum(c.queue_length for c in twin.checkouts.values()),
            "checkouts": [c.to_dict() for c in twin.checkouts.values()],
        }
    return {"history": [], "current_total": 0, "checkouts": []}


@router.get("/ai-performance")
async def get_ai_performance(
    store_id: int = 1,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI recommendation success rate and breakdown"""
    # Count by status
    result = await db.execute(
        select(Recommendation.status, func.count().label("cnt"))
        .where(Recommendation.store_id == store_id)
        .group_by(Recommendation.status)
    )
    status_counts = {row.status: row.cnt for row in result.all()}

    total = sum(status_counts.values())
    accepted = status_counts.get("accepted", 0)
    rejected = status_counts.get("rejected", 0)

    # Action results success rate
    result2 = await db.execute(
        select(ActionResult.success, func.count().label("cnt"))
        .join(Recommendation, ActionResult.recommendation_id == Recommendation.id)
        .where(Recommendation.store_id == store_id)
        .group_by(ActionResult.success)
    )
    outcome_counts = {str(row.success): row.cnt for row in result2.all()}
    successful = outcome_counts.get("True", 0)
    total_outcomes = sum(outcome_counts.values())
    success_rate = (successful / max(total_outcomes, 1)) * 100

    # Recent outcomes
    result3 = await db.execute(
        select(ActionResult, Recommendation.title, Recommendation.rec_type)
        .join(Recommendation, ActionResult.recommendation_id == Recommendation.id)
        .where(Recommendation.store_id == store_id)
        .order_by(desc(ActionResult.taken_at))
        .limit(10)
    )
    recent = []
    for ar, title, rec_type in result3.all():
        recent.append({
            "title": title,
            "rec_type": rec_type,
            "success": ar.success,
            "improvement_pct": ar.improvement_pct,
            "taken_at": ar.taken_at.isoformat() if ar.taken_at else None,
        })

    return {
        "total_recommendations": total,
        "accepted": accepted,
        "rejected": rejected,
        "pending": status_counts.get("pending", 0),
        "acceptance_rate": round((accepted / max(total, 1)) * 100, 1),
        "total_outcomes_measured": total_outcomes,
        "successful_outcomes": successful,
        "success_rate": round(success_rate, 1),
        "recent_outcomes": recent,
    }


@router.get("/store-overview")
async def get_store_overview(
    store_id: int = 1,
    current_user: User = Depends(get_current_user),
):
    twin = get_store_twin(store_id)
    if not twin:
        return {}
    snapshot = twin.snapshot()
    return {
        "footfall": snapshot["current_footfall"],
        "total_today": snapshot["total_customers_today"],
        "active_alerts": snapshot["active_alerts_count"],
        "open_checkouts": snapshot["open_checkouts"],
        "total_queue": snapshot["total_queue_length"],
        "low_stock_items": snapshot["low_stock_count"],
        "out_of_stock_items": snapshot["out_of_stock_count"],
        "available_staff": snapshot["available_staff"],
        "network_status": snapshot["network_status"],
    }
