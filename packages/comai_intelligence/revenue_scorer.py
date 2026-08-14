"""Revenue Opportunity Scorer — Estimates ARR and close probability.

Replaces fixed scoring with evidence-based revenue scoring.
Every score must explain WHY.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.comai_intelligence.product_profile import COMAIProductCatalog, COMAIProduct
from packages.comai_intelligence.pain_engine import PainSignal
from packages.comai_intelligence.intent_engine import IntentSignal
from packages.comai_intelligence.icp_engine import ICPScore


@dataclass
class RevenueScore:
    """Complete revenue opportunity score for a company."""

    # Core scores (all 0-100)
    icp_score: float
    technology_score: float
    growth_score: float
    pain_score: float
    intent_score: float
    traffic_score: float
    revenue_score: float
    support_maturity_score: float
    ai_readiness_score: float
    marketing_maturity_score: float
    automation_maturity_score: float
    decision_maker_score: float
    contact_quality_score: float
    competition_score: float
    estimated_roi_score: float
    buying_probability_score: float
    freshness_score: float

    # Aggregated
    total_score: float  # 0-100
    buying_probability: float  # 0-1
    estimated_arr: int  # INR
    estimated_deal_size: int  # INR
    applicable_products: list[str]
    close_probability: float  # 0-1

    # Explanations
    score_breakdown: dict[str, float] = field(default_factory=dict)
    why_scores: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "icp_score": round(self.icp_score, 2),
            "technology_score": round(self.technology_score, 2),
            "growth_score": round(self.growth_score, 2),
            "pain_score": round(self.pain_score, 2),
            "intent_score": round(self.intent_score, 2),
            "traffic_score": round(self.traffic_score, 2),
            "revenue_score": round(self.revenue_score, 2),
            "support_maturity_score": round(self.support_maturity_score, 2),
            "ai_readiness_score": round(self.ai_readiness_score, 2),
            "marketing_maturity_score": round(self.marketing_maturity_score, 2),
            "automation_maturity_score": round(self.automation_maturity_score, 2),
            "decision_maker_score": round(self.decision_maker_score, 2),
            "contact_quality_score": round(self.contact_quality_score, 2),
            "competition_score": round(self.competition_score, 2),
            "estimated_roi_score": round(self.estimated_roi_score, 2),
            "buying_probability_score": round(self.buying_probability_score, 2),
            "freshness_score": round(self.freshness_score, 2),
            "total_score": round(self.total_score, 2),
            "buying_probability": round(self.buying_probability, 3),
            "estimated_arr": self.estimated_arr,
            "estimated_deal_size": self.estimated_deal_size,
            "applicable_products": self.applicable_products,
            "close_probability": round(self.close_probability, 3),
            "score_breakdown": {k: round(v, 2) for k, v in self.score_breakdown.items()},
            "why_scores": self.why_scores,
        }


class RevenueOpportunityScorer:
    """Estimates ARR and close probability using evidence-based scoring.

    Every component scores 0-100 and explains WHY.
    """

    # Scoring weights
    WEIGHTS = {
        "icp": 0.12,
        "technology": 0.10,
        "growth": 0.08,
        "pain": 0.15,
        "intent": 0.12,
        "traffic": 0.05,
        "revenue": 0.08,
        "support_maturity": 0.05,
        "ai_readiness": 0.05,
        "marketing_maturity": 0.04,
        "automation_maturity": 0.04,
        "decision_maker": 0.06,
        "contact_quality": 0.04,
        "competition": 0.02,
    }

    def score(
        self,
        company: dict[str, Any],
        pains: list[PainSignal],
        intent_signals: list[IntentSignal],
        icp: ICPScore,
        tech_stack: dict[str, Any] | None = None,
        contact_quality: float = 0.0,
        decision_maker_count: int = 0,
    ) -> RevenueScore:
        """Calculate comprehensive revenue opportunity score.

        Args:
            company: Company data.
            pains: Detected pain signals.
            intent_signals: Detected buying intent signals.
            icp: ICP matching result.
            tech_stack: Detected technology stack.
            contact_quality: Contact quality score 0-1.
            decision_maker_count: Number of decision makers found.

        Returns:
            RevenueScore with all scores and explanations.
        """
        tech = tech_stack or {}

        # Score each dimension
        icp_sc = self._score_icp(icp)
        tech_sc = self._score_technology(tech)
        growth_sc = self._score_growth(company, intent_signals)
        pain_sc = self._score_pain(pains)
        intent_sc = self._score_intent(intent_signals)
        traffic_sc = self._score_traffic(company)
        revenue_sc = self._score_revenue(company)
        support_sc = self._score_support_maturity(tech)
        ai_sc = self._score_ai_readiness(tech)
        marketing_sc = self._score_marketing_maturity(tech)
        automation_sc = self._score_automation_maturity(tech)
        dm_sc = self._score_decision_makers(decision_maker_count)
        contact_sc = self._score_contacts(contact_quality)
        competition_sc = self._score_competition(tech)

        # Calculate ROI score
        roi_sc = self._score_estimated_roi(company, pains, tech)

        # Calculate freshness
        freshness_sc = self._score_freshness(company)

        # Calculate buying probability
        buying_prob = self._calculate_buying_probability(
            icp_sc, pain_sc, intent_sc, growth_sc, dm_sc, contact_sc
        )

        # Calculate close probability
        close_prob = self._calculate_close_probability(
            buying_prob, contact_sc, dm_sc, competition_sc, icp_sc
        )

        # Calculate applicable products and ARR
        applicable = self._get_applicable_products(company, tech)
        deal_size = COMAIProductCatalog.estimate_total_arr(
            [p for p in COMAIProductCatalog.PRODUCTS if p.name in applicable]
        )

        # Calculate total score
        score_breakdown = {
            "icp": icp_sc,
            "technology": tech_sc,
            "growth": growth_sc,
            "pain": pain_sc,
            "intent": intent_sc,
            "traffic": traffic_sc,
            "revenue": revenue_sc,
            "support_maturity": support_sc,
            "ai_readiness": ai_sc,
            "marketing_maturity": marketing_sc,
            "automation_maturity": automation_sc,
            "decision_maker": dm_sc,
            "contact_quality": contact_sc,
            "competition": competition_sc,
        }
        total_score = sum(
            score_breakdown[k] * self.WEIGHTS[k]
            for k in self.WEIGHTS
        )

        # Generate WHY explanations
        why_scores = self._explain_scores(
            company, pains, intent_signals, tech, icp,
            score_breakdown, buying_prob, close_prob
        )

        return RevenueScore(
            icp_score=icp_sc,
            technology_score=tech_sc,
            growth_score=growth_sc,
            pain_score=pain_sc,
            intent_score=intent_sc,
            traffic_score=traffic_sc,
            revenue_score=revenue_sc,
            support_maturity_score=support_sc,
            ai_readiness_score=ai_sc,
            marketing_maturity_score=marketing_sc,
            automation_maturity_score=automation_sc,
            decision_maker_score=dm_sc,
            contact_quality_score=contact_sc,
            competition_score=competition_sc,
            estimated_roi_score=roi_sc,
            buying_probability_score=buying_prob * 100,
            freshness_score=freshness_sc,
            total_score=round(total_score, 2),
            buying_probability=buying_prob,
            estimated_arr=deal_size,
            estimated_deal_size=deal_size,
            applicable_products=applicable,
            close_probability=close_prob,
            score_breakdown=score_breakdown,
            why_scores=why_scores,
        )

    def _score_icp(self, icp: ICPScore) -> float:
        return icp.score

    def _score_technology(self, tech: dict[str, Any]) -> float:
        score = 0.0
        platform = tech.get("platform", "unknown")
        if platform in ("shopify", "shopify_plus"):
            score += 30
        elif platform in ("woocommerce", "magento"):
            score += 20
        elif platform != "unknown":
            score += 10

        if not tech.get("has_chatbot"):
            score += 25
        if tech.get("has_whatsapp"):
            score += 15
        if not tech.get("has_ai"):
            score += 20
        if tech.get("automation_maturity") == "none":
            score += 10
        return min(score, 100.0)

    def _score_growth(self, company: dict[str, Any], signals: list[IntentSignal]) -> float:
        score = 0.0
        growth_signals = [s for s in signals if s.signal_type in ("hiring", "expansion", "funding")]
        score += len(growth_signals) * 20

        if company.get("traffic_growth"):
            score += 15
        if company.get("new_collections"):
            score += 10
        return min(score, 100.0)

    def _score_pain(self, pains: list[PainSignal]) -> float:
        if not pains:
            return 0.0
        severity_map = {"critical": 25, "high": 18, "medium": 10, "low": 5}
        total = sum(severity_map.get(p.severity, 5) * p.confidence for p in pains)
        return min(total, 100.0)

    def _score_intent(self, signals: list[IntentSignal]) -> float:
        if not signals:
            return 0.0
        total = sum(s.current_strength * s.weight * 100.0 for s in signals)
        return min(total, 100.0)

    def _score_traffic(self, company: dict[str, Any]) -> float:
        traffic = company.get("estimated_traffic") or 0
        if traffic >= 200_000:
            return 90.0
        if traffic >= 100_000:
            return 75.0
        if traffic >= 50_000:
            return 60.0
        if traffic >= 10_000:
            return 40.0
        return 20.0

    def _score_revenue(self, company: dict[str, Any]) -> float:
        revenue = company.get("estimated_revenue") or 0
        if revenue >= 100_00_00_000:  # ₹100 Cr
            return 90.0
        if revenue >= 50_00_00_000:  # ₹50 Cr
            return 80.0
        if revenue >= 20_00_00_000:  # ₹20 Cr
            return 70.0
        if revenue >= 10_00_00_000:  # ₹10 Cr
            return 60.0
        if revenue >= 5_00_00_000:  # ₹5 Cr
            return 50.0
        if revenue >= 2_00_00_000:  # ₹2 Cr
            return 40.0
        return 20.0

    def _score_support_maturity(self, tech: dict[str, Any]) -> float:
        score = 50.0
        if tech.get("support_tool") and tech["support_tool"] != "none":
            score -= 20
        if tech.get("has_chatbot"):
            score -= 15
        if tech.get("has_ai"):
            score -= 20
        return max(score, 0.0)

    def _score_ai_readiness(self, tech: dict[str, Any]) -> float:
        score = 30.0
        if tech.get("has_ai"):
            score += 30
        if tech.get("analytics") and tech["analytics"] != "none":
            score += 15
        if tech.get("platform") in ("shopify", "shopify_plus"):
            score += 15
        return min(score, 100.0)

    def _score_marketing_maturity(self, tech: dict[str, Any]) -> float:
        score = 20.0
        if tech.get("email_marketing") and tech["email_marketing"] != "none":
            score += 25
        if tech.get("has_whatsapp"):
            score += 20
        if tech.get("analytics") and tech["analytics"] != "none":
            score += 15
        if tech.get("crm") and tech["crm"] != "none":
            score += 15
        return min(score, 100.0)

    def _score_automation_maturity(self, tech: dict[str, Any]) -> float:
        maturity = tech.get("automation_maturity", "none")
        return {
            "none": 20.0,
            "basic": 45.0,
            "moderate": 65.0,
            "advanced": 85.0,
        }.get(maturity, 20.0)

    def _score_decision_makers(self, count: int) -> float:
        return min(count * 25, 100.0)

    def _score_contacts(self, quality: float) -> float:
        return quality * 100.0

    def _score_competition(self, tech: dict[str, Any]) -> float:
        ai_chatbot = tech.get("ai_chatbot", "none")
        if ai_chatbot and ai_chatbot != "none":
            return 30.0  # Competitor present, harder to win
        support = tech.get("support_tool", "none")
        if support and support != "none":
            return 50.0  # Has support tool, medium competition
        return 80.0  # No competition, easier to win

    def _score_estimated_roi(
        self, company: dict[str, Any], pains: list[PainSignal], tech: dict[str, Any]
    ) -> float:
        score = 30.0
        if pains:
            total_cost = sum(p.estimated_annual_cost_inr for p in pains)
            if total_cost >= 10_00_000:
                score += 30
            elif total_cost >= 5_00_000:
                score += 20
            elif total_cost >= 1_00_000:
                score += 10
        if not tech.get("has_ai"):
            score += 20
        return min(score, 100.0)

    def _score_freshness(self, company: dict[str, Any]) -> float:
        from datetime import datetime, timezone
        last_verified = company.get("last_verified")
        if not last_verified:
            return 50.0
        try:
            if isinstance(last_verified, str):
                dt = datetime.fromisoformat(last_verified)
            else:
                dt = last_verified
            days = (datetime.now(timezone.utc) - dt).days
            if days <= 7:
                return 100.0
            if days <= 30:
                return 75.0
            if days <= 90:
                return 50.0
            return 25.0
        except (ValueError, TypeError):
            return 50.0

    def _calculate_buying_probability(
        self,
        icp: float,
        pain: float,
        intent: float,
        growth: float,
        dm: float,
        contact: float,
    ) -> float:
        """Calculate probability of buying 0-1."""
        factors = [
            icp / 100.0 * 0.20,
            pain / 100.0 * 0.25,
            intent / 100.0 * 0.20,
            growth / 100.0 * 0.10,
            dm / 100.0 * 0.15,
            contact / 100.0 * 0.10,
        ]
        return min(sum(factors), 1.0)

    def _calculate_close_probability(
        self,
        buying_prob: float,
        contact_quality: float,
        dm_score: float,
        competition: float,
        icp: float,
    ) -> float:
        """Calculate probability of closing 0-1."""
        base = buying_prob * 0.5
        contact_boost = contact_quality * 0.2
        dm_boost = dm_score / 100.0 * 0.15
        competition_factor = competition / 100.0 * 0.1
        icp_factor = icp / 100.0 * 0.05
        return min(base + contact_boost + dm_boost + competition_factor + icp_factor, 1.0)

    def _get_applicable_products(
        self, company: dict[str, Any], tech: dict[str, Any]
    ) -> list[str]:
        industry = company.get("industry") or company.get("category") or ""
        platform = tech.get("platform") or company.get("platform") or ""
        revenue = company.get("estimated_revenue") or 5_00_00_000
        employees = company.get("estimated_employees") or 50

        products = COMAIProductCatalog.applicable_products(
            industry, platform, revenue, employees
        )
        return [p.name for p in products]

    def _explain_scores(
        self,
        company: dict[str, Any],
        pains: list[PainSignal],
        intent_signals: list[IntentSignal],
        tech: dict[str, Any],
        icp: ICPScore,
        breakdown: dict[str, float],
        buying_prob: float,
        close_prob: float,
    ) -> dict[str, str]:
        """Generate WHY explanations for each score."""
        explanations: dict[str, str] = {}

        if breakdown["icp"] >= 70:
            explanations["icp"] = f"Strong ICP match ({breakdown['icp']:.0f}/100)"
        elif breakdown["icp"] >= 40:
            explanations["icp"] = f"Moderate ICP match ({breakdown['icp']:.0f}/100)"
        else:
            explanations["icp"] = f"Weak ICP match ({breakdown['icp']:.0f}/100)"

        if breakdown["pain"] >= 60:
            top_pain = pains[0].pain_type if pains else "unknown"
            explanations["pain"] = f"High pain ({breakdown['pain']:.0f}/100): {top_pain}"
        elif breakdown["pain"] > 0:
            explanations["pain"] = f"Some pain detected ({breakdown['pain']:.0f}/100)"
        else:
            explanations["pain"] = "No significant pain detected"

        if breakdown["intent"] >= 50:
            explanations["intent"] = f"Strong buying intent ({breakdown['intent']:.0f}/100)"
        elif breakdown["intent"] > 0:
            explanations["intent"] = f"Some intent signals ({breakdown['intent']:.0f}/100)"
        else:
            explanations["intent"] = "No buying intent detected"

        platform = tech.get("platform", "unknown")
        if platform in ("shopify", "shopify_plus"):
            explanations["technology"] = f"Shopify detected — ideal platform for COMAI"
        else:
            explanations["technology"] = f"Platform: {platform}"

        explanations["buying_probability"] = f"{buying_prob*100:.0f}% buying probability"
        explanations["close_probability"] = f"{close_prob*100:.0f}% close probability"

        return explanations
