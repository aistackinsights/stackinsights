# confidence.py — Bayesian-inspired confidence scoring with time decay
import math
from datetime import datetime, UTC

def compute_confidence(
    base_confidence: float,
    confirmations: int,
    contradictions: int,
    last_confirmed_at: datetime,
    decay_rate: float = 0.02
) -> float:
    days_since = (datetime.now(UTC) - last_confirmed_at).days
    confirmation_boost = 0.05 * math.sqrt(confirmations)
    contradiction_penalty = 0.15 * contradictions
    time_decay = decay_rate * days_since
    raw = base_confidence + confirmation_boost - contradiction_penalty - time_decay
    return max(0.01, min(0.99, raw))
