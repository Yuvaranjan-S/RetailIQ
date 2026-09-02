"""
Demand Predictor — Inventory consumption rate estimation and stockout prediction.

Uses a simple exponential moving average on recent InventoryEvent history
to estimate demand rate (units/minute), then predicts stockout ETA.

For hackathon: the simulator feeds realistic demand data;
for production: replace with a trained sklearn model.
"""
from typing import Optional, List
from datetime import datetime, timezone


def compute_demand_rate_ema(
    consumption_events: List[dict],
    alpha: float = 0.3,
    default_rate: float = 0.1,
) -> float:
    """
    Compute exponential moving average demand rate from recent events.
    
    Args:
        consumption_events: list of {quantity_change, timestamp} dicts,
                            sorted oldest→newest, quantity_change < 0 for sales
        alpha: EMA smoothing factor (0.3 = moderate smoothing)
        default_rate: fallback rate if no events
    
    Returns:
        demand_rate in units/minute
    """
    if not consumption_events:
        return default_rate

    # Convert to (minutes_ago, units_consumed) pairs
    now = datetime.now(timezone.utc)
    rates = []
    for i in range(1, len(consumption_events)):
        prev = consumption_events[i - 1]
        curr = consumption_events[i]
        qty_consumed = abs(min(curr["quantity_change"], 0))  # only sales
        if qty_consumed <= 0:
            continue
        try:
            t1 = datetime.fromisoformat(str(prev["timestamp"])).replace(tzinfo=timezone.utc)
            t2 = datetime.fromisoformat(str(curr["timestamp"])).replace(tzinfo=timezone.utc)
        except Exception:
            continue
        dt_minutes = max((t2 - t1).total_seconds() / 60, 0.01)
        rates.append(qty_consumed / dt_minutes)

    if not rates:
        return default_rate

    # Exponential moving average
    ema = rates[0]
    for r in rates[1:]:
        ema = alpha * r + (1 - alpha) * ema

    return max(ema, 0.001)  # always positive


def predict_stockout(
    current_stock: float,
    demand_rate: float,  # units/minute
    reorder_level: float = 0.0,
) -> Optional[float]:
    """
    Predict minutes until stockout (or until reorder level is hit).
    
    Returns:
        Minutes until stockout, or None if not imminent (> 120 min)
    """
    if demand_rate <= 0 or current_stock <= 0:
        if current_stock <= 0:
            return 0.0
        return None

    # Time to hit reorder level
    stock_above_reorder = max(0, current_stock - reorder_level)
    minutes_to_reorder = stock_above_reorder / demand_rate

    # Time to stockout
    minutes_to_out = current_stock / demand_rate

    # Return stockout time if within monitoring window
    if minutes_to_out <= 120:
        return round(minutes_to_out, 1)
    return None


def compute_inventory_urgency(
    current_stock: float,
    max_stock: float,
    reorder_level: float,
    demand_rate: float,
    predicted_stockout_minutes: Optional[float],
    footfall: int = 0,
) -> float:
    """
    Compute a 0.0-1.0 urgency score for inventory replenishment.
    Used by the signal fusion engine.
    """
    score = 0.0

    # Stock ratio component
    stock_ratio = current_stock / max(max_stock, 1)
    if stock_ratio <= 0:
        score += 0.5
    elif stock_ratio <= reorder_level / max(max_stock, 1):
        score += 0.3
    else:
        score += max(0, 0.3 * (1 - stock_ratio))

    # Stockout imminence
    if predicted_stockout_minutes is not None:
        if predicted_stockout_minutes <= 15:
            score += 0.4
        elif predicted_stockout_minutes <= 30:
            score += 0.25
        elif predicted_stockout_minutes <= 60:
            score += 0.1

    # Footfall modifier (high footfall = higher urgency)
    if footfall > 40:
        score = min(1.0, score * 1.2)

    return round(min(score, 1.0), 3)
