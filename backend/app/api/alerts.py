"""Alerts API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from typing import Optional
from datetime import datetime, timezone

from app.database.connection import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.alert import Alert
from app.schemas.schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=dict)
async def get_alerts(
    store_id: int = 1,
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Alert).where(Alert.store_id == store_id).order_by(desc(Alert.created_at)).limit(limit)
    if status:
        query = query.where(Alert.status == status)
    if severity:
        query = query.where(Alert.severity == severity)
    result = await db.execute(query)
    alerts = result.scalars().all()
    return {
        "alerts": [AlertOut.model_validate(a).model_dump() for a in alerts],
        "count": len(alerts),
    }


@router.put("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(404, "Alert not found")
    await db.execute(
        update(Alert).where(Alert.id == alert_id).values(
            status="resolved",
            resolved_at=datetime.now(timezone.utc),
            acknowledged_by=current_user.id,
        )
    )
    await db.commit()
    return {"success": True, "alert_id": alert_id}


@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Alert).where(Alert.id == alert_id).values(
            status="acknowledged",
            acknowledged_by=current_user.id,
        )
    )
    await db.commit()
    return {"success": True, "alert_id": alert_id}
