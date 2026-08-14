"""Explainable, deterministic opportunity scoring."""

from __future__ import annotations

from opportunity_intelligence.constants import SCORING_VERSION, SCORE_WEIGHTS, SIGNAL_FACTOR_BASELINES
from opportunity_intelligence.enums import BuyingWindow, SignalCategory
from opportunity_intelligence.schemas import ScoreResult


class OpportunityScoring:
    def calculate(
        self,
        *,
        signal_category: SignalCategory,
        freshness_score: float,
        evidence_score: float,
        icp_score: float,
        buying_window: BuyingWindow,
    ) -> ScoreResult:
        category = SignalCategory(signal_category)
        window = BuyingWindow(buying_window)
        factors = dict(SIGNAL_FACTOR_BASELINES[category])
        factors["freshness"] = freshness_score
        factors["evidence"] = evidence_score
        factors["icp"] = icp_score
        factors["timing"] = self._timing_score(factors["timing"], window)

        weighted = {
            key: round(value * SCORE_WEIGHTS[key], 2)
            for key, value in factors.items()
            if key in SCORE_WEIGHTS
        }
        score = round(sum(weighted.values()), 2)
        reasons = [
            f"{key.replace('_', ' ').title()} contributed {weighted[key]} weighted points from raw score {factors[key]}."
            for key in SCORE_WEIGHTS
        ]
        return ScoreResult(
            score=score,
            breakdown={key: round(value, 2) for key, value in factors.items()},
            weighted_breakdown=weighted,
            reasons=reasons,
            version=SCORING_VERSION,
        )

    def _timing_score(self, base: float, buying_window: BuyingWindow) -> float:
        modifiers = {
            BuyingWindow.IMMEDIATE: 1.0,
            BuyingWindow.WARM: 0.88,
            BuyingWindow.FUTURE: 0.72,
            BuyingWindow.DORMANT: 0.35,
        }
        return round(min(base * modifiers[buying_window], 100.0), 2)
