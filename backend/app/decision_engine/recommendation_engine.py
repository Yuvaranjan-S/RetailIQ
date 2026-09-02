"""
Recommendation Engine — Orchestrates Rule Engine + Signal Fusion

This is the main entry point for AI decision-making.
Called every N seconds by the decision cycle loop.

Flow:
  1. Get decision context from Store Digital Twin
  2. Run signal fusion to get compound stress score
  3. Run rule engine to get triggered rules
  4. Boost confidence using fusion agreement
  5. Filter out duplicate/expired recommendations
  6. Persist new recommendations to DB
  7. Broadcast via WebSocket
"""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, TYPE_CHECKING

from app.decision_engine.rule_engine import evaluate_rules, RuleTrigger
from app.decision_engine.signal_fusion import fuse_signals, boost_confidence_from_fusion

if TYPE_CHECKING:
    from app.services.store_state_engine import StoreStateTwin

logger = logging.getLogger("retailiq.decision_engine")

# How long before a recommendation expires (if not acted on)
RECOMMENDATION_TTL_MINUTES = 15
# Minimum seconds between same-type recommendations for same entity
DEDUP_WINDOW_SECONDS = 120


class RecommendationEngine:
    """
    Runs the full AI decision cycle for a store twin.
    Stateless — reads from twin, writes to DB, broadcasts via WS.
    """

    def __init__(self, db_session_factory, ws_broadcaster):
        self._db_factory = db_session_factory
        self._broadcaster = ws_broadcaster
        self._recent_recs: dict = {}  # rule_id+entity_id → last_created timestamp

    async def run_cycle(self, twin: "StoreStateTwin") -> List[dict]:
        """
        Main decision cycle — call this every N seconds.
        Returns list of newly created recommendation dicts.
        """
        ctx = twin.get_decision_context()
        fusion = fuse_signals(ctx, twin.footfall_history)

        # Evaluate all rules
        triggers = evaluate_rules(ctx)

        new_recs = []
        for trigger in triggers:
            # Boost confidence based on multi-signal agreement
            trigger.confidence = boost_confidence_from_fusion(
                trigger.confidence, fusion, trigger.rule_id
            )

            # Skip low-confidence triggers
            if trigger.confidence < 0.55:
                logger.debug(f"Skipping low-confidence trigger: {trigger.rule_id} ({trigger.confidence})")
                continue

            # Deduplication — don't create same-type recommendation within window
            dedup_key = f"{trigger.rule_id}_{trigger.inventory_id}_{trigger.checkout_id}"
            last_created = self._recent_recs.get(dedup_key)
            if last_created:
                age = (datetime.now(timezone.utc) - last_created).total_seconds()
                if age < DEDUP_WINDOW_SECONDS:
                    continue

            # Persist recommendation to DB
            rec_dict = await self._persist_recommendation(twin.store_id, trigger, fusion)
            if rec_dict:
                new_recs.append(rec_dict)
                self._recent_recs[dedup_key] = datetime.now(timezone.utc)

        # Update active alerts count in twin
        if new_recs:
            twin.active_recommendations_count = await self._count_active_recs(twin.store_id)

        # Broadcast fusion state regardless
        await self._broadcaster.broadcast(twin.store_id, {
            "type": "fusion_update",
            "store_id": twin.store_id,
            "fusion": fusion,
            "new_recommendations": new_recs,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return new_recs

    async def _persist_recommendation(
        self, store_id: int, trigger: RuleTrigger, fusion: dict
    ) -> Optional[dict]:
        """Save recommendation to PostgreSQL"""
        from app.models.recommendation import Recommendation
        expires = datetime.now(timezone.utc) + timedelta(minutes=RECOMMENDATION_TTL_MINUTES)

        rec = Recommendation(
            store_id=store_id,
            rec_type=trigger.rec_type,
            title=trigger.title,
            description=trigger.reason,
            priority=trigger.priority,
            confidence=trigger.confidence,
            reason=trigger.reason,
            evidence=trigger.evidence,
            recommended_action=trigger.recommended_action,
            expected_impact=trigger.expected_impact,
            status="pending",
            expires_at=expires,
            checkout_id=trigger.checkout_id,
            zone_id=trigger.zone_id,
            inventory_id=trigger.inventory_id,
            staff_id=trigger.staff_id,
        )

        try:
            async with self._db_factory() as session:
                session.add(rec)
                await session.commit()
                await session.refresh(rec)
                logger.info(
                    f"[REC] {trigger.priority} {trigger.rule_id} → "
                    f"'{trigger.title}' conf={trigger.confidence:.2f}"
                )
                return {
                    "id": rec.id,
                    "rec_type": rec.rec_type,
                    "title": rec.title,
                    "priority": rec.priority,
                    "confidence": rec.confidence,
                    "reason": rec.reason,
                    "evidence": rec.evidence,
                    "recommended_action": rec.recommended_action,
                    "expected_impact": rec.expected_impact,
                    "status": rec.status,
                    "created_at": rec.created_at.isoformat() if rec.created_at else None,
                    "checkout_id": rec.checkout_id,
                    "inventory_id": rec.inventory_id,
                    "zone_id": rec.zone_id,
                }
        except Exception as e:
            logger.error(f"Failed to persist recommendation: {e}")
            return None

    async def _count_active_recs(self, store_id: int) -> int:
        from sqlalchemy import select, func
        from app.models.recommendation import Recommendation
        try:
            async with self._db_factory() as session:
                result = await session.execute(
                    select(func.count()).where(
                        Recommendation.store_id == store_id,
                        Recommendation.status == "pending",
                    )
                )
                return result.scalar() or 0
        except Exception:
            return 0
