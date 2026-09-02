"""
Signal Fusion Engine — Multi-Signal Weighted Scoring

Combines multiple store signals into a unified urgency score.
Used to:
  1. Prioritize competing recommendations
  2. Amplify confidence when multiple signals agree
  3. Detect compound scenarios (e.g., surge + low stock + queue)

Signals and weights:
  - footfall_surge_score     (0-1): how much above baseline is current footfall
  - queue_urgency_score      (0-1): based on queue length and wait time
  - inventory_urgency_score  (0-1): based on stock levels across all SKUs
  - staff_stress_score       (0-1): customers per staff member
  - time_context_score       (0-1): peak hours amplify all signals

Output: compound_score (0-1) + signal breakdown
"""
from typing import Dict, Any
from datetime import datetime, timezone


# Signal weights (must sum to 1.0)
WEIGHTS = {
    "footfall_surge": 0.25,
    "queue_urgency": 0.30,
    "inventory_urgency": 0.25,
    "staff_stress": 0.10,
    "time_context": 0.10,
}

# Peak hours (0-23): higher weight during busy periods
PEAK_HOURS = {10, 11, 12, 13, 14, 17, 18, 19, 20}


def fuse_signals(ctx: dict, footfall_history: list = None) -> dict:
    """
    Run signal fusion on the current store decision context.
    
    Returns:
        {
          compound_score: float,  # 0-1 overall store stress
          signals: { name: score },
          dominant_signal: str,
          scenario_tags: [str],  # e.g. ["surge", "low_stock", "queue_critical"]
        }
    """
    signals = {}

    # ── Footfall surge score ──────────────────────────────────────────────
    footfall = ctx.get("current_footfall", 0)
    if footfall_history and len(footfall_history) >= 5:
        recent_avg = sum(p.get("count", 0) for p in footfall_history[-5:]) / 5
        baseline = sum(p.get("count", 0) for p in footfall_history[-20:-5]) / max(len(footfall_history[-20:-5]), 1)
        surge_ratio = recent_avg / max(baseline, 1)
        signals["footfall_surge"] = min(1.0, max(0.0, (surge_ratio - 0.8) / 1.2))
    else:
        # Without history, use raw footfall
        signals["footfall_surge"] = min(1.0, footfall / 60.0)

    # ── Queue urgency score ───────────────────────────────────────────────
    total_queue = ctx.get("total_queue_length", 0)
    max_wait_sec = ctx.get("max_wait_seconds", 0)
    queue_score = min(1.0, total_queue / 15.0) * 0.6 + min(1.0, max_wait_sec / 600.0) * 0.4
    signals["queue_urgency"] = round(queue_score, 3)

    # ── Inventory urgency score ───────────────────────────────────────────
    critical_inv = ctx.get("critical_inventory", [])
    low_inv = ctx.get("low_inventory", [])
    imminent = ctx.get("imminent_stockouts", [])
    all_inv = ctx.get("inventory", {})
    total_items = max(len(all_inv), 1)

    inv_score = (
        (len(critical_inv) * 0.5 + len(low_inv) * 0.2 + len(imminent) * 0.3)
        / total_items
    )
    signals["inventory_urgency"] = round(min(inv_score, 1.0), 3)

    # ── Staff stress score ────────────────────────────────────────────────
    staff_count = max(len(ctx.get("staff", {})), 1)
    staff_ratio = footfall / staff_count
    signals["staff_stress"] = round(min(1.0, staff_ratio / 20.0), 3)

    # ── Time context score (peak hours) ──────────────────────────────────
    hour = datetime.now(timezone.utc).hour
    signals["time_context"] = 0.8 if hour in PEAK_HOURS else 0.3

    # ── Compound score ────────────────────────────────────────────────────
    compound = sum(WEIGHTS[k] * signals[k] for k in WEIGHTS)
    compound = round(compound, 3)

    # ── Dominant signal ───────────────────────────────────────────────────
    dominant = max(signals, key=lambda k: WEIGHTS.get(k, 0) * signals[k])

    # ── Scenario tags ─────────────────────────────────────────────────────
    tags = []
    if signals["footfall_surge"] > 0.6:
        tags.append("customer_surge")
    if signals["queue_urgency"] > 0.6:
        tags.append("queue_critical")
    if signals["inventory_urgency"] > 0.5:
        tags.append("inventory_risk")
    if signals["staff_stress"] > 0.7:
        tags.append("staff_stressed")
    if len(tags) >= 2:
        tags.append("compound_incident")

    return {
        "compound_score": compound,
        "signals": signals,
        "weights": WEIGHTS,
        "dominant_signal": dominant,
        "scenario_tags": tags,
        "store_stress_level": _stress_level(compound),
    }


def _stress_level(score: float) -> str:
    if score >= 0.75:
        return "CRITICAL"
    if score >= 0.50:
        return "HIGH"
    if score >= 0.25:
        return "MEDIUM"
    return "LOW"


def boost_confidence_from_fusion(base_confidence: float, fusion: dict, rule_id: str) -> float:
    """
    If multiple signals agree with a rule trigger, boost its confidence.
    E.g., CHECKOUT_NEEDED rule gets a boost if footfall_surge AND queue_urgency are both high.
    """
    compound = fusion.get("compound_score", 0)
    tags = fusion.get("scenario_tags", [])

    boost = 0.0
    if "compound_incident" in tags:
        boost += 0.04
    if compound > 0.7:
        boost += 0.03

    if rule_id == "CHECKOUT_NEEDED" and "queue_critical" in tags and "customer_surge" in tags:
        boost += 0.05
    if rule_id in ("IMMINENT_STOCKOUT", "STOCKOUT") and "inventory_risk" in tags:
        boost += 0.03

    return round(min(base_confidence + boost, 0.99), 3)
