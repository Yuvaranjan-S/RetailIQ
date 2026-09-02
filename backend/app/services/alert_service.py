"""Alert Service — creates, deduplicates, and resolves store alerts"""
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("retailiq.alerts")

# Alert dedup window — don't create same alert type for same entity within N seconds
ALERT_DEDUP_SECONDS = 300  # 5 minutes


class AlertService:
    def __init__(self, db_session_factory, ws_broadcaster):
        self._db = db_session_factory
        self._broadcaster = ws_broadcaster
        self._recent_alerts: dict = {}  # (alert_type, entity_id) → timestamp

    async def create_alert(
        self,
        store_id: int,
        alert_type: str,
        severity: str,
        title: str,
        description: str = "",
        location: str = "",
        recommended_action: str = "",
        zone_id: Optional[int] = None,
        inventory_id: Optional[int] = None,
        checkout_id: Optional[int] = None,
    ) -> Optional[dict]:
        from app.models.alert import Alert

        # Deduplication
        entity_key = inventory_id or checkout_id or zone_id or 0
        dedup_key = (alert_type, entity_key)
        last = self._recent_alerts.get(dedup_key)
        if last:
            age = (datetime.now(timezone.utc) - last).total_seconds()
            if age < ALERT_DEDUP_SECONDS:
                return None

        alert = Alert(
            store_id=store_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            location=location,
            recommended_action=recommended_action,
            status="active",
            zone_id=zone_id,
            inventory_id=inventory_id,
            checkout_id=checkout_id,
        )

        try:
            async with self._db() as session:
                session.add(alert)
                await session.commit()
                await session.refresh(alert)
                self._recent_alerts[dedup_key] = datetime.now(timezone.utc)

                alert_dict = {
                    "id": alert.id,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "title": alert.title,
                    "description": alert.description,
                    "location": alert.location,
                    "recommended_action": alert.recommended_action,
                    "status": alert.status,
                    "created_at": alert.created_at.isoformat() if alert.created_at else None,
                }

                # Broadcast alert to dashboard
                await self._broadcaster.broadcast(store_id, {
                    "type": "new_alert",
                    "alert": alert_dict,
                })

                logger.info(f"[ALERT] {severity} {alert_type}: {title}")
                return alert_dict
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return None

    async def resolve_alert(self, alert_id: int, resolved_by: int) -> bool:
        from app.models.alert import Alert
        from sqlalchemy import update
        try:
            async with self._db() as session:
                await session.execute(
                    update(Alert)
                    .where(Alert.id == alert_id)
                    .values(
                        status="resolved",
                        resolved_at=datetime.now(timezone.utc),
                        acknowledged_by=resolved_by,
                    )
                )
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
            return False
