"""
Queue Predictor — M/M/c Queueing Theory Model

Uses the Erlang C formula to predict:
- Expected wait time given arrival rate, service rate, and number of servers
- Probability queue will exceed a threshold
- Recommended number of checkouts to open

This is deterministic mathematics, not ML — always explainable.
"""
import math
from typing import Optional


def erlang_c(lam: float, mu: float, c: int) -> float:
    """
    Compute Erlang C formula — probability a customer has to wait.
    
    Args:
        lam: arrival rate (customers per minute)
        mu:  service rate per server (customers per minute)
        c:   number of servers (open checkouts)
    
    Returns:
        P(wait) — probability between 0 and 1
        Returns 1.0 if system is overloaded (rho >= 1)
    """
    if c <= 0 or mu <= 0:
        return 1.0

    rho = lam / (c * mu)  # server utilization
    if rho >= 1.0:
        return 1.0  # overloaded system

    a = lam / mu  # traffic intensity

    # Compute sum for denominator: Σ(k=0 to c-1) [a^k / k!]
    sum_terms = sum((a ** k) / math.factorial(k) for k in range(c))

    # Add Erlang C numerator term: a^c / (c! * (1 - rho))
    erlang_term = (a ** c) / (math.factorial(c) * (1 - rho))

    # Erlang C = erlang_term / (sum_terms + erlang_term)
    return erlang_term / (sum_terms + erlang_term)


def expected_wait_time(lam: float, mu: float, c: int) -> float:
    """
    Expected wait time in queue (minutes), not including service time.
    E[W] = C(c, lam/mu) / (c * mu - lam)
    """
    if lam <= 0:
        return 0.0
    if c <= 0 or mu <= 0:
        return float("inf")

    rho = lam / (c * mu)
    if rho >= 1.0:
        return float("inf")  # system overloaded

    c_w = erlang_c(lam, mu, c)
    wait = c_w / (c * mu - lam)  # in minutes
    return max(0.0, wait)


def predict_queue(
    current_queue: int,
    arrival_rate: float,
    service_rate: float,
    open_checkouts: int,
    window_minutes: float = 5.0,
) -> dict:
    """
    Full queue prediction given current state.
    
    Returns dict with:
      - predicted_wait_minutes: expected wait right now
      - predicted_queue_in_N_min: estimated queue length in window_minutes
      - overloaded: bool — whether system cannot keep up
      - recommended_checkouts: minimum servers to bring wait < 5min
      - confidence: 0.0-1.0
    """
    if open_checkouts <= 0 or arrival_rate <= 0:
        return {
            "predicted_wait_minutes": 0.0,
            "predicted_queue_in_N_min": current_queue,
            "overloaded": False,
            "recommended_checkouts": open_checkouts,
            "trend": "stable",
            "confidence": 0.85,
        }

    rho = arrival_rate / (open_checkouts * service_rate)
    wait_min = expected_wait_time(arrival_rate, service_rate, open_checkouts)

    # Project queue change over window
    if rho >= 1.0:
        projected_queue = current_queue + int(
            (arrival_rate - open_checkouts * service_rate) * window_minutes
        )
        trend = "increasing_rapidly"
    elif rho > 0.8:
        projected_queue = current_queue + max(0, int(arrival_rate * window_minutes * 0.2))
        trend = "increasing"
    elif rho < 0.5:
        projected_queue = max(0, current_queue - int(service_rate * open_checkouts * window_minutes * 0.3))
        trend = "decreasing"
    else:
        projected_queue = current_queue
        trend = "stable"

    # Find minimum checkouts to keep wait < 5 min
    recommended_c = open_checkouts
    if wait_min > 5.0:
        for c_test in range(open_checkouts + 1, open_checkouts + 6):
            test_wait = expected_wait_time(arrival_rate, service_rate, c_test)
            if test_wait <= 5.0:
                recommended_c = c_test
                break

    # Confidence degrades with very high arrival rate or extreme queue
    confidence = max(0.6, min(0.97, 1.0 - abs(rho - 0.7) * 0.3))

    return {
        "predicted_wait_minutes": min(round(wait_min, 1), 99.0),
        "predicted_wait_seconds": min(round(wait_min * 60, 0), 5940.0),
        "predicted_queue_in_N_min": max(0, projected_queue),
        "overloaded": rho >= 1.0,
        "server_utilization": round(rho, 3),
        "recommended_checkouts": recommended_c,
        "trend": trend,
        "confidence": round(confidence, 3),
        "inputs": {
            "arrival_rate": round(arrival_rate, 3),
            "service_rate": round(service_rate, 3),
            "open_checkouts": open_checkouts,
            "current_queue": current_queue,
        },
    }
