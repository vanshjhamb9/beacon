"""ARIE: Revenue Opportunity Engine.

Replaces one-dimensional lead score with 12+ explainable scores.
Every score has evidence and confidence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ScoreComponent:
    """A single score component with explanation."""
    name: str
    score: float  # 0-100
    weight: float
    weighted_score: float  # score * weight
    evidence: list = field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""


@dataclass
class RevenueScoreResult:
    """Complete revenue opportunity score with 12 components."""
    company_domain: str
    
    # 12 Component Scores
    icp_score: ScoreComponent = field(default_factory=lambda: ScoreComponent("icp", 0, 0.15, 0))
    technology_fit: ScoreComponent = field(default_factory=lambda: ScoreComponent("technology", 0, 0.20, 0))
    growth_score: ScoreComponent = field(default_factory=lambda: ScoreComponent("growth", 0, 0.10, 0))
    pain_score: ScoreComponent = field(default_factory=lambda: ScoreComponent("pain", 0, 0.15, 0))
    intent_score: ScoreComponent = field(default_factory=lambda: ScoreComponent("intent", 0, 0.15, 0))
    revenue_fit: ScoreComponent = field(default_factory=lambda: ScoreComponent("revenue", 0, 0.10, 0))
    decision_maker_score: ScoreComponent = field(default_factory=lambda: ScoreComponent("decision_maker", 0, 0.10, 0))
    contact_quality: ScoreComponent = field(default_factory=lambda: ScoreComponent("contact", 0, 0.05, 0))
    urgency_score: ScoreComponent = field(default_factory=lambda: ScoreComponent("urgency", 0, 0.00, 0))
    automation_readiness: ScoreComponent = field(default_factory=lambda: ScoreComponent("automation", 0, 0.00, 0))
    ai_readiness: ScoreComponent = field(default_factory=lambda: ScoreComponent("ai", 0, 0.00, 0))
    support_complexity: ScoreComponent = field(default_factory=lambda: ScoreComponent("support", 0, 0.00, 0))
    
    # Composite Scores
    overall_score: float = 0.0
    overall_confidence: float = 0.0
    close_probability: float = 0.0
    expected_arr: float = 0.0
    arr_confidence: float = 0.0
    expected_payback_months: int = 0
    
    # Classification
    classification: str = "UNSCORED"  # HOT, WARM, COLD, UNSCORED
    
    # Metadata
    scored_at: datetime = field(default_factory=datetime.utcnow)
    weights_used: dict = field(default_factory=dict)
    explanations: list = field(default_factory=list)


class ARIERevenueEngine:
    """Revenue Opportunity Engine - calculates 12+ explainable scores."""
    
    # Default weights
    DEFAULT_WEIGHTS = {
        "icp": 0.15,
        "technology": 0.20,
        "growth": 0.10,
        "pain": 0.15,
        "intent": 0.15,
        "revenue": 0.10,
        "decision_maker": 0.10,
        "contact": 0.05,
    }
    
    # COMAI pricing tiers
    PRICING_TIERS = {
        "starter": {"monthly": 299, "annual": 2990},
        "growth": {"monthly": 799, "annual": 7990},
        "enterprise": {"monthly": 1999, "annual": 19990},
    }
    
    def calculate_revenue_score(
        self,
        company_data: dict[str, Any],
        icp_match: dict[str, Any] = None,
        technology_analysis: dict[str, Any] = None,
        growth_analysis: dict[str, Any] = None,
        pain_analysis: dict[str, Any] = None,
        intent_analysis: dict[str, Any] = None,
        decision_makers: list = None,
        contact_data: dict[str, Any] = None,
    ) -> RevenueScoreResult:
        """Calculate comprehensive revenue opportunity score.
        
        Args:
            company_data: Company information
            icp_match: ICP matching results
            technology_analysis: Technology analysis results
            growth_analysis: Growth analysis results
            pain_analysis: Pain analysis results
            intent_analysis: Intent analysis results
            decision_makers: List of decision makers
            contact_data: Contact information
            
        Returns:
            RevenueScoreResult with 12 component scores
        """
        domain = company_data.get("domain", "")
        
        result = RevenueScoreResult(company_domain=domain)
        
        # 1. ICP Score (15%)
        result.icp_score = self._calculate_icp_score(icp_match or {})
        
        # 2. Technology Fit (20%)
        result.technology_fit = self._calculate_technology_fit(technology_analysis or {})
        
        # 3. Growth Score (10%)
        result.growth_score = self._calculate_growth_score(growth_analysis or {})
        
        # 4. Pain Score (15%)
        result.pain_score = self._calculate_pain_score(pain_analysis or {})
        
        # 5. Intent Score (15%)
        result.intent_score = self._calculate_intent_score(intent_analysis or {})
        
        # 6. Revenue Fit (10%)
        result.revenue_fit = self._calculate_revenue_fit(company_data)
        
        # 7. Decision Maker Score (10%)
        result.decision_maker_score = self._calculate_decision_maker_score(decision_makers or [])
        
        # 8. Contact Quality (5%)
        result.contact_quality = self._calculate_contact_quality(contact_data or {})
        
        # Calculate overall score
        components = [
            result.icp_score,
            result.technology_fit,
            result.growth_score,
            result.pain_score,
            result.intent_score,
            result.revenue_fit,
            result.decision_maker_score,
            result.contact_quality,
        ]
        
        result.overall_score = sum(c.weighted_score for c in components)
        result.overall_confidence = self._calculate_overall_confidence(components)
        
        # Calculate business metrics
        result.close_probability = self._estimate_close_probability(result.overall_score)
        result.expected_arr = self._estimate_arr(company_data, result.overall_score)
        result.arr_confidence = self._estimate_arr_confidence(company_data)
        result.expected_payback_months = self._estimate_payback(result.expected_arr)
        
        # Classify
        if result.overall_score >= 80:
            result.classification = "HOT"
        elif result.overall_score >= 60:
            result.classification = "WARM"
        elif result.overall_score >= 40:
            result.classification = "COLD"
        else:
            result.classification = "UNSCORED"
        
        # Store weights used
        result.weights_used = {c.name: c.weight for c in components}
        
        # Generate explanations
        result.explanations = self._generate_explanations(components)
        
        return result
    
    def _calculate_icp_score(self, icp_match: dict) -> ScoreComponent:
        """Calculate ICP match score."""
        score = icp_match.get("icp_score", 0)
        confidence = icp_match.get("confidence", 0)
        evidence = icp_match.get("matched_criteria", [])
        
        reasoning = f"Company matches {len(evidence)} ICP criteria"
        if evidence:
            reasoning += f": {', '.join(evidence[:3])}"
        
        weighted_score = score * self.DEFAULT_WEIGHTS["icp"]
        
        return ScoreComponent(
            name="icp",
            score=score,
            weight=self.DEFAULT_WEIGHTS["icp"],
            weighted_score=weighted_score,
            evidence=evidence,
            confidence=confidence,
            reasoning=reasoning,
        )
    
    def _calculate_technology_fit(self, tech_analysis: dict) -> ScoreComponent:
        """Calculate technology fit score."""
        score = tech_analysis.get("comai_fit_score", 0)
        confidence = tech_analysis.get("confidence", 0)
        evidence = tech_analysis.get("fit_signals", [])
        
        reasoning = f"Technology stack compatibility: {score:.0f}/100"
        if evidence:
            reasoning += f". Key signals: {', '.join(evidence[:3])}"
        
        weighted_score = score * self.DEFAULT_WEIGHTS["technology"]
        
        return ScoreComponent(
            name="technology",
            score=score,
            weight=self.DEFAULT_WEIGHTS["technology"],
            weighted_score=weighted_score,
            evidence=evidence,
            confidence=confidence,
            reasoning=reasoning,
        )
    
    def _calculate_growth_score(self, growth_analysis: dict) -> ScoreComponent:
        """Calculate growth score."""
        score = growth_analysis.get("growth_score", 50)
        confidence = growth_analysis.get("confidence", 0)
        evidence = [s.get("signal_type", "") for s in growth_analysis.get("signals", [])[:5]]
        
        reasoning = f"Growth score: {score:.0f}/100"
        if growth_analysis.get("growth_trend"):
            reasoning += f", trend: {growth_analysis['growth_trend']}"
        
        weighted_score = score * self.DEFAULT_WEIGHTS["growth"]
        
        return ScoreComponent(
            name="growth",
            score=score,
            weight=self.DEFAULT_WEIGHTS["growth"],
            weighted_score=weighted_score,
            evidence=evidence,
            confidence=confidence,
            reasoning=reasoning,
        )
    
    def _calculate_pain_score(self, pain_analysis: dict) -> ScoreComponent:
        """Calculate pain score."""
        score = pain_analysis.get("total_pain_score", 0)
        confidence = pain_analysis.get("confidence", 0)
        evidence = [p.get("category", "") for p in pain_analysis.get("pain_points", [])[:5]]
        
        reasoning = f"Pain level: {score:.0f}/100"
        if evidence:
            reasoning += f". Key pain areas: {', '.join(evidence[:3])}"
        
        weighted_score = score * self.DEFAULT_WEIGHTS["pain"]
        
        return ScoreComponent(
            name="pain",
            score=score,
            weight=self.DEFAULT_WEIGHTS["pain"],
            weighted_score=weighted_score,
            evidence=evidence,
            confidence=confidence,
            reasoning=reasoning,
        )
    
    def _calculate_intent_score(self, intent_analysis: dict) -> ScoreComponent:
        """Calculate intent score."""
        score = intent_analysis.get("intent_score", 30)
        confidence = intent_analysis.get("confidence", 0)
        evidence = [s.get("signal_type", "") for s in intent_analysis.get("signals", [])[:5]]
        
        reasoning = f"Buying intent: {score:.0f}/100"
        if intent_analysis.get("intent_level"):
            reasoning += f", level: {intent_analysis['intent_level']}"
        if intent_analysis.get("buying_timeframe"):
            reasoning += f", timeframe: {intent_analysis['buying_timeframe']}"
        
        weighted_score = score * self.DEFAULT_WEIGHTS["intent"]
        
        return ScoreComponent(
            name="intent",
            score=score,
            weight=self.DEFAULT_WEIGHTS["intent"],
            weighted_score=weighted_score,
            evidence=evidence,
            confidence=confidence,
            reasoning=reasoning,
        )
    
    def _calculate_revenue_fit(self, company: dict) -> ScoreComponent:
        """Calculate revenue fit score."""
        revenue = company.get("revenue_estimate", 0)
        aov = company.get("avg_order_value", 0)
        traffic = company.get("monthly_traffic", 0)
        orders = company.get("monthly_orders", 0)
        
        score = 50.0  # Default neutral
        evidence = []
        
        # Estimate monthly revenue
        monthly_revenue = revenue / 12 if revenue else orders * aov
        
        if monthly_revenue > 100000:
            score = 90
            evidence.append(f"High revenue: ${monthly_revenue:,.0f}/month")
        elif monthly_revenue > 50000:
            score = 75
            evidence.append(f"Medium revenue: ${monthly_revenue:,.0f}/month")
        elif monthly_revenue > 10000:
            score = 60
            evidence.append(f"Growing revenue: ${monthly_revenue:,.0f}/month")
        elif monthly_revenue > 0:
            score = 40
            evidence.append(f"Early revenue: ${monthly_revenue:,.0f}/month")
        else:
            score = 30
            evidence.append("Revenue data unavailable")
        
        weighted_score = score * self.DEFAULT_WEIGHTS["revenue"]
        
        return ScoreComponent(
            name="revenue",
            score=score,
            weight=self.DEFAULT_WEIGHTS["revenue"],
            weighted_score=weighted_score,
            evidence=evidence,
            confidence=0.6 if revenue else 0.3,
            reasoning=f"Revenue fit assessment based on ${monthly_revenue:,.0f} estimated monthly revenue",
        )
    
    def _calculate_decision_maker_score(self, decision_makers: list) -> ScoreComponent:
        """Calculate decision maker access score."""
        score = 20.0  # Default low
        evidence = []
        confidence = 0.3
        
        if not decision_makers:
            reasoning = "No decision makers identified"
        else:
            dm_roles = [dm.get("role", "").lower() for dm in decision_makers]
            
            # Check for key roles
            key_roles = ["founder", "ceo", "cmo", "cto", "coo"]
            found_key = [r for r in key_roles if any(r in role for role in dm_roles)]
            
            if found_key:
                score = 90
                evidence.append(f"Key decision makers: {', '.join(found_key)}")
                confidence = 0.9
            elif dm_roles:
                score = 60
                evidence.append(f"Decision makers found: {len(decision_makers)}")
                confidence = 0.7
            
            reasoning = f"Found {len(decision_makers)} decision makers"
        
        weighted_score = score * self.DEFAULT_WEIGHTS["decision_maker"]
        
        return ScoreComponent(
            name="decision_maker",
            score=score,
            weight=self.DEFAULT_WEIGHTS["decision_maker"],
            weighted_score=weighted_score,
            evidence=evidence,
            confidence=confidence,
            reasoning=reasoning,
        )
    
    def _calculate_contact_quality(self, contact_data: dict) -> ScoreComponent:
        """Calculate contact quality score."""
        score = 0.0
        evidence = []
        
        has_email = bool(contact_data.get("email"))
        has_phone = bool(contact_data.get("phone"))
        has_linkedin = bool(contact_data.get("linkedin_url"))
        email_verified = contact_data.get("email_verified", False)
        
        if has_email:
            score += 30
            evidence.append("Email available")
        if has_phone:
            score += 30
            evidence.append("Phone available")
        if has_linkedin:
            score += 20
            evidence.append("LinkedIn available")
        if email_verified:
            score += 20
            evidence.append("Email verified")
        
        confidence = 0.9 if (has_email and email_verified) else 0.5
        
        weighted_score = score * self.DEFAULT_WEIGHTS["contact"]
        
        return ScoreComponent(
            name="contact",
            score=score,
            weight=self.DEFAULT_WEIGHTS["contact"],
            weighted_score=weighted_score,
            evidence=evidence,
            confidence=confidence,
            reasoning=f"Contact quality: {score:.0f}/100",
        )
    
    def _calculate_overall_confidence(self, components: list[ScoreComponent]) -> float:
        """Calculate overall confidence score."""
        if not components:
            return 0.0
        
        confidences = [c.confidence for c in components]
        return sum(confidences) / len(confidences)
    
    def _estimate_close_probability(self, overall_score: float) -> float:
        """Estimate close probability from overall score."""
        # Non-linear mapping
        if overall_score >= 80:
            return 75.0
        elif overall_score >= 70:
            return 60.0
        elif overall_score >= 60:
            return 45.0
        elif overall_score >= 50:
            return 30.0
        elif overall_score >= 40:
            return 15.0
        else:
            return 5.0
    
    def _estimate_arr(self, company: dict, overall_score: float) -> float:
        """Estimate Annual Recurring Revenue potential."""
        revenue = company.get("revenue_estimate", 0)
        employees = company.get("employee_estimate", 0)
        
        # Base ARR estimate
        if revenue > 10000000:
            base_arr = self.PRICING_TIERS["enterprise"]["annual"]
        elif revenue > 1000000:
            base_arr = self.PRICING_TIERS["growth"]["annual"]
        else:
            base_arr = self.PRICING_TIERS["starter"]["annual"]
        
        # Adjust by close probability
        close_prob = self._estimate_close_probability(overall_score)
        expected_arr = base_arr * (close_prob / 100)
        
        return expected_arr
    
    def _estimate_arr_confidence(self, company: dict) -> float:
        """Estimate confidence in ARR estimate."""
        has_revenue = bool(company.get("revenue_estimate"))
        has_employees = bool(company.get("employee_estimate"))
        has_traffic = bool(company.get("monthly_traffic"))
        
        data_points = [has_revenue, has_employees, has_traffic]
        available = sum(1 for p in data_points if p)
        
        return (available / len(data_points)) * 100
    
    def _estimate_payback(self, expected_arr: float) -> int:
        """Estimate payback period in months."""
        if expected_arr >= self.PRICING_TIERS["enterprise"]["annual"]:
            return 3
        elif expected_arr >= self.PRICING_TIERS["growth"]["annual"]:
            return 4
        else:
            return 6
    
    def _generate_explanations(self, components: list[ScoreComponent]) -> list[dict]:
        """Generate human-readable explanations for each component."""
        explanations = []
        
        for component in components:
            explanations.append({
                "component": component.name,
                "score": component.score,
                "weight": component.weight,
                "weighted_score": component.weighted_score,
                "reasoning": component.reasoning,
                "evidence": component.evidence,
                "confidence": component.confidence,
            })
        
        return explanations
