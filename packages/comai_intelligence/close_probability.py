"""Close Probability Calculator — Estimates likelihood of closing a deal.

Uses evidence-based scoring across multiple factors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CloseProbabilityResult:
    """Result of close probability calculation."""

    probability: float  # 0-1
    confidence: float  # 0-1, confidence in the probability estimate
    factors: dict[str, float]
    recommendation: str
    expected_sales_cycle_days: int
    risk_level: str  # "low", "medium", "high"

    def to_dict(self) -> dict[str, Any]:
        return {
            "probability": round(self.probability, 3),
            "confidence": round(self.confidence, 3),
            "factors": {k: round(v, 3) for k, v in self.factors.items()},
            "recommendation": self.recommendation,
            "expected_sales_cycle_days": self.expected_sales_cycle_days,
            "risk_level": self.risk_level,
        }


class CloseProbabilityCalculator:
    """Estimates close probability using multiple evidence-based factors.

    Factors:
    1. ICP Fit (0-1)
    2. Pain Intensity (0-1)
    3. Buying Intent (0-1)
    4. Decision Maker Quality (0-1)
    5. Contact Verification (0-1)
    6. Budget Fit (0-1)
    7. Competition Level (0-1, higher = less competition = higher probability)
    8. Timing (0-1)
    """

    FACTOR_WEIGHTS = {
        "icp_fit": 0.20,
        "pain_intensity": 0.20,
        "buying_intent": 0.20,
        "decision_maker_quality": 0.15,
        "contact_verification": 0.10,
        "budget_fit": 0.05,
        "competition": 0.05,
        "timing": 0.05,
    }

    def calculate(
        self,
        icp_score: float,  # 0-100
        pain_score: float,  # 0-100
        intent_score: float,  # 0-100
        decision_maker_count: int,
        decision_maker_quality: float,  # 0-1
        contact_verified: bool,
        contact_quality: float,  # 0-1
        estimated_revenue: int,  # INR
        competition_level: float,  # 0-1, higher = more competition
        recent_funding: bool = False,
        hiring_active: bool = False,
        is_urgently_looking: bool = False,
    ) -> CloseProbabilityResult:
        """Calculate close probability.

        Returns:
            CloseProbabilityResult with probability, factors, and recommendation.
        """
        factors: dict[str, float] = {}

        # Factor 1: ICP Fit
        factors["icp_fit"] = min(icp_score / 100.0, 1.0)

        # Factor 2: Pain Intensity
        factors["pain_intensity"] = min(pain_score / 100.0, 1.0)

        # Factor 3: Buying Intent
        factors["buying_intent"] = min(intent_score / 100.0, 1.0)

        # Factor 4: Decision Maker Quality
        dm_score = 0.0
        if decision_maker_count >= 3:
            dm_score = 1.0
        elif decision_maker_count >= 2:
            dm_score = 0.8
        elif decision_maker_count >= 1:
            dm_score = 0.6
        dm_score = max(dm_score, decision_maker_quality)
        factors["decision_maker_quality"] = dm_score

        # Factor 5: Contact Verification
        factors["contact_verification"] = contact_quality if contact_verified else contact_quality * 0.5

        # Factor 6: Budget Fit
        budget_score = 0.5
        if estimated_revenue >= 50_00_00_000:  # ₹50 Cr
            budget_score = 0.9
        elif estimated_revenue >= 20_00_00_000:  # ₹20 Cr
            budget_score = 0.8
        elif estimated_revenue >= 10_00_00_000:  # ₹10 Cr
            budget_score = 0.7
        elif estimated_revenue >= 5_00_00_000:  # ₹5 Cr
            budget_score = 0.6
        factors["budget_fit"] = budget_score

        # Factor 7: Competition
        factors["competition"] = 1.0 - competition_level

        # Factor 8: Timing
        timing_score = 0.5
        if recent_funding:
            timing_score += 0.2
        if hiring_active:
            timing_score += 0.15
        if is_urgently_looking:
            timing_score += 0.15
        factors["timing"] = min(timing_score, 1.0)

        # Calculate weighted probability
        probability = sum(
            factors[k] * self.FACTOR_WEIGHTS[k]
            for k in self.FACTOR_WEIGHTS
        )

        # Calculate confidence in the estimate
        known_factors = sum(1 for v in factors.values() if v > 0)
        confidence = known_factors / len(factors)

        # Determine risk level
        if probability >= 0.6:
            risk_level = "low"
        elif probability >= 0.3:
            risk_level = "medium"
        else:
            risk_level = "high"

        # Expected sales cycle
        cycle_days = 60
        if probability >= 0.7:
            cycle_days = 30
        elif probability >= 0.5:
            cycle_days = 45
        elif probability >= 0.3:
            cycle_days = 60
        else:
            cycle_days = 90

        # Generate recommendation
        recommendation = self._generate_recommendation(
            probability, factors, risk_level
        )

        return CloseProbabilityResult(
            probability=probability,
            confidence=confidence,
            factors=factors,
            recommendation=recommendation,
            expected_sales_cycle_days=cycle_days,
            risk_level=risk_level,
        )

    def _generate_recommendation(
        self, probability: float, factors: dict[str, float], risk_level: str
    ) -> str:
        """Generate sales recommendation based on probability and factors."""
        if probability >= 0.7:
            return (
                "HIGH PRIORITY — Contact immediately. Strong fit with high intent. "
                "Recommend founder-to-founder outreach or warm introduction."
            )
        if probability >= 0.5:
            return (
                "MEDIUM-HIGH — Contact within 7 days. Good fit with moderate intent. "
                "Recommend LinkedIn + Email sequence."
            )
        if probability >= 0.3:
            return (
                "MEDIUM — Nurture with content. Some fit but intent unclear. "
                "Recommend educational outreach about COMAI benefits."
            )
        return (
            "LOW — Monitor for changes. Weak signals currently. "
            "Add to nurture sequence for long-term tracking."
        )
