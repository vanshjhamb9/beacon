from __future__ import annotations

from target_account_engine.models.types import SCORING_VERSION

# Deterministic weighted revenue opportunity score. Versioned — never silent change.
DEFAULT_WEIGHTS: dict[str, float] = {
    "fit": 0.25,
    "intent": 0.20,
    "budget": 0.15,
    "urgency": 0.15,
    "accessibility": 0.15,
    "competition": 0.10,
}

assert abs(sum(DEFAULT_WEIGHTS.values()) - 1.0) < 1e-9
assert SCORING_VERSION.startswith("tai-")
