from __future__ import annotations

from target_account_engine.models.types import AccountTier, ScoreComponent
from target_account_engine.scoring.weights import DEFAULT_WEIGHTS


class RevenueOpportunityScorer:
    def __init__(
        self,
        weights: dict[str, float] | None = None,
        *,
        top_tier_threshold: float = 70.0,
        mid_tier_threshold: float = 50.0,
    ) -> None:
        self.weights = weights or dict(DEFAULT_WEIGHTS)
        self.top_tier_threshold = top_tier_threshold
        self.mid_tier_threshold = mid_tier_threshold

    def combine(self, scores: dict[str, float], *, explanations: dict[str, str], evidence: dict[str, list[str]]) -> tuple[float, list[ScoreComponent], AccountTier]:
        components: list[ScoreComponent] = []
        total = 0.0
        for name, weight in self.weights.items():
            value = float(scores.get(name) or 0.0)
            total += value * weight
            components.append(
                ScoreComponent(
                    name=name,
                    value=round(value, 2),
                    weight=weight,
                    explanation=explanations.get(name) or f"{name} contribution",
                    evidence=list(evidence.get(name) or []),
                )
            )
        revenue_score = round(max(0.0, min(100.0, total)), 2)
        if revenue_score >= self.top_tier_threshold:
            tier = AccountTier.TOP
        elif revenue_score >= self.mid_tier_threshold:
            tier = AccountTier.MID
        elif revenue_score < 25:
            tier = AccountTier.EXCLUDED
        else:
            tier = AccountTier.LOW
        return revenue_score, components, tier
