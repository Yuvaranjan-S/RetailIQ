"""
Rule Engine — Deterministic Thresholds for Store Operations

Rules are evaluated on every decision cycle.
Each rule returns a RuleTrigger if its conditions are met.
Rules are always explainable — no black-box reasoning.

RULE PRIORITY ORDER:
  1. STOCKOUT (out of stock) — CRITICAL
  2. CHECKOUT_NEEDED (queue + closed checkout + staff available) — HIGH
  3. IMMINENT_STOCKOUT (< 30 min) — HIGH
  4. LOW_STOCK — MEDIUM
  5. QUEUE_CONGESTION (long queue, no available checkout to open) — HIGH
  6. STAFF_SHORTAGE — MEDIUM
  7. CONGESTION_PREDICTED (footfall spike) — MEDIUM
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# ─── Thresholds (tune for demo) ─────────────────────────────────────────────
QUEUE_CRITICAL_LENGTH = 8          # people
QUEUE_HIGH_LENGTH = 5
WAIT_TIME_CRITICAL_SECONDS = 300   # 5 minutes
WAIT_TIME_HIGH_SECONDS = 180       # 3 minutes
STOCKOUT_IMMINENT_MINUTES = 30
STOCKOUT_URGENT_MINUTES = 15
FOOTFALL_HIGH = 40
FOOTFALL_SURGE_RATIO = 1.5         # 50% increase = surge
STAFF_CUSTOMER_RATIO_LOW = 15      # > 15 customers per staff = shortage


@dataclass
class RuleTrigger:
    rule_id: str
    priority: str          # CRITICAL | HIGH | MEDIUM | LOW
    rec_type: str          # maps to Recommendation.rec_type
    title: str
    reason: str
    evidence: List[str]
    recommended_action: str
    expected_impact: str
    confidence: float
    # Optional entity references
    checkout_id: Optional[int] = None
    zone_id: Optional[int] = None
    inventory_id: Optional[int] = None
    staff_id: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)


def evaluate_rules(ctx: dict) -> List[RuleTrigger]:
    """
    Evaluate all rules against the current store decision context.
    Returns a list of triggered rules, sorted by priority.
    """
    triggers: List[RuleTrigger] = []

    # ── Rule 1: STOCKOUT ────────────────────────────────────────────────────
    for item in ctx.get("critical_inventory", []):
        if item["stock_status"] == "out":
            triggers.append(RuleTrigger(
                rule_id="STOCKOUT",
                priority="CRITICAL",
                rec_type="restock",
                title=f"⚠ Stockout: {item['product_name']}",
                reason=(
                    f"{item['product_name']} (SKU {item['sku']}) is completely out of stock. "
                    f"Customers cannot purchase this product."
                ),
                evidence=[
                    f"Current stock: 0 units",
                    f"SKU: {item['sku']}",
                    f"Category: {item['category']}",
                    f"Demand rate: {item['demand_rate']:.2f} units/min",
                ],
                recommended_action=(
                    f"Immediately replenish {item['product_name']} from backroom or emergency stock."
                ),
                expected_impact="Restore product availability. Prevent lost sales.",
                confidence=0.99,
                inventory_id=item["id"],
            ))

    # ── Rule 2: CHECKOUT_NEEDED ──────────────────────────────────────────────
    total_queue = ctx.get("total_queue_length", 0)
    max_wait = ctx.get("max_wait_seconds", 0)
    closed_checkouts = ctx.get("closed_checkout_list", [])
    available_staff = ctx.get("available_staff_list", [])

    if (total_queue >= QUEUE_CRITICAL_LENGTH
            and max_wait >= WAIT_TIME_HIGH_SECONDS
            and closed_checkouts
            and available_staff):
        checkout = closed_checkouts[0]
        staff = available_staff[0]
        triggers.append(RuleTrigger(
            rule_id="CHECKOUT_NEEDED",
            priority="HIGH",
            rec_type="open_checkout",
            title=f"Open {checkout['name']} to reduce queue",
            reason=(
                f"Queue length ({total_queue}) exceeds critical threshold ({QUEUE_CRITICAL_LENGTH}). "
                f"Wait time is {max_wait/60:.1f} min. "
                f"{checkout['name']} is closed but {staff['name']} is available."
            ),
            evidence=[
                f"Total queue: {total_queue} customers",
                f"Max wait time: {max_wait/60:.1f} minutes",
                f"Closed checkout available: {checkout['name']}",
                f"Available staff: {staff['name']}",
                f"Threshold: {QUEUE_CRITICAL_LENGTH} customers",
            ],
            recommended_action=(
                f"Open {checkout['name']}. "
                f"Move {staff['name']} to {checkout['name']}."
            ),
            expected_impact=(
                f"Estimated queue reduction from {total_queue} to "
                f"{max(0, total_queue - 5)} in 5 minutes."
            ),
            confidence=_queue_confidence(total_queue, max_wait),
            checkout_id=checkout["id"],
            staff_id=staff.get("id"),
            extra={"staff_name": staff["name"], "checkout_name": checkout["name"]},
        ))

    # ── Rule 3: IMMINENT_STOCKOUT ────────────────────────────────────────────
    for item in ctx.get("imminent_stockouts", []):
        if item["stock_status"] == "out":
            continue  # already handled by Rule 1
        minutes = item.get("predicted_stockout_minutes", 99)
        prio = "HIGH" if minutes <= STOCKOUT_URGENT_MINUTES else "MEDIUM"
        triggers.append(RuleTrigger(
            rule_id="IMMINENT_STOCKOUT",
            priority=prio,
            rec_type="restock",
            title=f"Restock {item['product_name']} — {minutes:.0f} min until stockout",
            reason=(
                f"{item['product_name']} will stock out in approximately {minutes:.0f} minutes "
                f"at current demand rate of {item['demand_rate']:.2f} units/min."
            ),
            evidence=[
                f"Current stock: {item['current_stock']:.0f} units",
                f"Demand rate: {item['demand_rate']:.2f} units/min",
                f"Predicted stockout: {minutes:.0f} minutes",
                f"Reorder level: {item['reorder_level']:.0f} units",
            ],
            recommended_action=(
                f"Replenish {item['product_name']} (SKU {item['sku']}) within "
                f"{max(5, int(minutes * 0.5))} minutes."
            ),
            expected_impact=f"Prevent stockout. Maintain {int(item['max_stock'] * 0.5)} units target.",
            confidence=_stockout_confidence(minutes, item["demand_rate"]),
            inventory_id=item["id"],
        ))

    # ── Rule 4: LOW_STOCK (below reorder level, no imminent stockout) ────────
    for item in ctx.get("low_inventory", []):
        # Skip if already covered by imminent stockout
        if any(t.inventory_id == item["id"] for t in triggers):
            continue
        triggers.append(RuleTrigger(
            rule_id="LOW_STOCK",
            priority="MEDIUM",
            rec_type="restock",
            title=f"Low stock: {item['product_name']}",
            reason=(
                f"{item['product_name']} stock ({item['current_stock']:.0f} units) "
                f"is below reorder level ({item['reorder_level']:.0f} units)."
            ),
            evidence=[
                f"Current stock: {item['current_stock']:.0f} units",
                f"Reorder level: {item['reorder_level']:.0f} units",
                f"Stock level: {item['stock_percentage']:.0f}%",
                f"Demand rate: {item['demand_rate']:.3f} units/min",
            ],
            recommended_action=f"Schedule replenishment for {item['product_name']}.",
            expected_impact="Prevent future stockout. Maintain sales continuity.",
            confidence=0.90,
            inventory_id=item["id"],
        ))

    # ── Rule 5: QUEUE_CONGESTION (queue high but no checkout to open) ────────
    if (total_queue >= QUEUE_HIGH_LENGTH
            and max_wait >= WAIT_TIME_CRITICAL_SECONDS
            and not closed_checkouts
            and not any(t.rule_id == "CHECKOUT_NEEDED" for t in triggers)):
        triggers.append(RuleTrigger(
            rule_id="QUEUE_CONGESTION",
            priority="HIGH",
            rec_type="queue_management",
            title=f"Queue congestion — all checkouts open",
            reason=(
                f"All checkouts are open but queue ({total_queue}) is still critical. "
                f"Wait time: {max_wait/60:.1f} min."
            ),
            evidence=[
                f"Total queue: {total_queue}",
                f"Max wait: {max_wait/60:.1f} min",
                f"All checkouts open",
                f"Available staff: {ctx.get('available_staff_count', 0)}",
            ],
            recommended_action=(
                "Activate express checkout policy. "
                "Consider items-limit lanes or mobile payment assistance."
            ),
            expected_impact="Reduce perceived wait time through process optimization.",
            confidence=0.80,
        ))

    # ── Rule 6: STAFF_SHORTAGE ───────────────────────────────────────────────
    footfall = ctx.get("current_footfall", 0)
    total_staff = len(ctx.get("staff", {}))
    if total_staff > 0:
        ratio = footfall / total_staff
        if ratio > STAFF_CUSTOMER_RATIO_LOW and footfall > 20:
            triggers.append(RuleTrigger(
                rule_id="STAFF_SHORTAGE",
                priority="MEDIUM",
                rec_type="increase_staffing",
                title=f"Staff-to-customer ratio critical ({ratio:.0f}:1)",
                reason=(
                    f"Current footfall ({footfall}) vs available staff ({total_staff}) "
                    f"ratio exceeds recommended {STAFF_CUSTOMER_RATIO_LOW}:1."
                ),
                evidence=[
                    f"Current footfall: {footfall}",
                    f"Total staff: {total_staff}",
                    f"Ratio: {ratio:.1f} customers per staff",
                    f"Threshold: {STAFF_CUSTOMER_RATIO_LOW}:1",
                ],
                recommended_action="Call in additional staff or redistribute from low-activity zones.",
                expected_impact="Improve customer service levels and reduce unassisted customer time.",
                confidence=0.75,
            ))

    # De-duplicate: one rule per checkout_id / inventory_id
    seen_checkout_ids = set()
    seen_inventory_ids = set()
    deduplicated = []
    for t in triggers:
        if t.checkout_id and t.checkout_id in seen_checkout_ids:
            continue
        if t.inventory_id and t.inventory_id in seen_inventory_ids:
            continue
        if t.checkout_id:
            seen_checkout_ids.add(t.checkout_id)
        if t.inventory_id:
            seen_inventory_ids.add(t.inventory_id)
        deduplicated.append(t)

    # Sort by priority
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    return sorted(deduplicated, key=lambda x: priority_order.get(x.priority, 9))


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _queue_confidence(queue_len: int, wait_seconds: float) -> float:
    """Confidence increases with more extreme queue/wait evidence"""
    base = 0.75
    if queue_len >= 12:
        base += 0.10
    if wait_seconds >= 360:  # 6 min
        base += 0.10
    return round(min(base, 0.97), 2)


def _stockout_confidence(minutes: float, demand_rate: float) -> float:
    """Confidence higher when stockout is imminent and demand rate is stable"""
    base = 0.80
    if minutes <= 15:
        base += 0.12
    if demand_rate > 0.3:
        base += 0.05  # high and consistent demand
    return round(min(base, 0.97), 2)
