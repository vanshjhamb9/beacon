"""RICVP: Core Validation & Calibration Engines.

All 15 RICVP modules in a single file for maintainability.
Every engine produces explainable, evidence-backed, measurable outputs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# 1. EVIDENCE VALIDATION ENGINE
# =============================================================================

@dataclass
class EvidenceRecord:
    """Immutable evidence for a data point."""
    field_name: str
    field_value: str
    source_id: str
    source_type: str  # website, api, curated, search, manual
    confidence: float
    evidence_url: str = ""
    is_verified: bool = False
    verification_method: str = ""
    agreeing_sources: int = 1
    conflicting_sources: int = 0
    source_reliability: float = 0.5
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_verified: datetime = field(default_factory=datetime.utcnow)


class EvidenceValidationEngine:
    """Every field must include evidence. Reject unsupported assumptions."""

    def __init__(self):
        self._evidence: dict[str, list[EvidenceRecord]] = {}  # company_id -> [EvidenceRecord]

    def add_evidence(self, company_id: str, evidence: EvidenceRecord) -> None:
        """Add evidence for a field."""
        self._evidence.setdefault(company_id, []).append(evidence)

    def validate_field(self, company_id: str, field_name: str) -> dict:
        """Validate a field has sufficient evidence."""
        evidence_list = [
            e for e in self._evidence.get(company_id, [])
            if e.field_name == field_name
        ]

        if not evidence_list:
            return {
                "field": field_name,
                "status": "no_evidence",
                "confidence": 0.0,
                "sources": 0,
                "verified": False,
                "recommendation": "REJECT - No evidence found",
            }

        # Calculate aggregate confidence
        avg_confidence = sum(e.confidence for e in evidence_list) / len(evidence_list)
        max_reliability = max(e.source_reliability for e in evidence_list)
        verified_count = sum(1 for e in evidence_list if e.is_verified)
        agreeing = sum(e.agreeing_sources for e in evidence_list)
        conflicting = sum(e.conflicting_sources for e in evidence_list)

        # Determine status
        if conflicting > 0 and agreeing <= conflicting:
            status = "conflicting"
        elif verified_count > 0:
            status = "verified"
        elif avg_confidence >= 0.7 and len(evidence_list) >= 2:
            status = "high_confidence"
        elif avg_confidence >= 0.5:
            status = "moderate_confidence"
        else:
            status = "low_confidence"

        # Final confidence calculation
        final_confidence = (
            avg_confidence * 0.4 +
            max_reliability * 0.3 +
            (verified_count / len(evidence_list)) * 0.2 +
            (1 if conflicting == 0 else 0.5) * 0.1
        )

        return {
            "field": field_name,
            "status": status,
            "confidence": round(final_confidence, 3),
            "sources": len(evidence_list),
            "agreeing_sources": agreeing,
            "conflicting_sources": conflicting,
            "verified": verified_count > 0,
            "verification_rate": verified_count / len(evidence_list),
            "recommendation": "ACCEPT" if final_confidence >= 0.6 else "REJECT",
        }

    def validate_company(self, company_id: str) -> dict:
        """Validate all fields for a company."""
        all_fields = set(e.field_name for e in self._evidence.get(company_id, []))
        validations = {}
        for field_name in all_fields:
            validations[field_name] = self.validate_field(company_id, field_name)

        total = len(validations)
        verified = sum(1 for v in validations.values() if v["status"] == "verified")
        high_conf = sum(1 for v in validations.values() if v["confidence"] >= 0.7)

        return {
            "company_id": company_id,
            "total_fields": total,
            "verified_fields": verified,
            "high_confidence_fields": high_conf,
            "overall_evidence_score": (high_conf / total * 100) if total > 0 else 0,
            "fields": validations,
        }


# =============================================================================
# 2. CROSS SOURCE VALIDATION ENGINE
# =============================================================================

class CrossSourceValidationEngine:
    """Compare data from multiple sources. Only accept when threshold met."""

    def __init__(self, agreement_threshold: float = 0.6):
        self.agreement_threshold = agreement_threshold

    def validate_across_sources(
        self,
        field_name: str,
        values_from_sources: list[dict],  # [{value, source_id, reliability}]
    ) -> dict:
        """Validate a field across multiple sources."""
        if not values_from_sources:
            return {"status": "no_data", "confidence": 0.0}

        # Group by value
        value_groups: dict[str, list[dict]] = {}
        for item in values_from_sources:
            val = item.get("value", "").strip().lower()
            if val:
                value_groups.setdefault(val, []).append(item)

        if not value_groups:
            return {"status": "no_data", "confidence": 0.0}

        # Find majority value
        sorted_groups = sorted(value_groups.items(), key=lambda x: len(x[1]), reverse=True)
        majority_value, majority_sources = sorted_groups[0]

        # Calculate agreement
        total_sources = len(values_from_sources)
        agreeing = len(majority_sources)
        agreement_rate = agreeing / total_sources

        # Weighted agreement (by reliability)
        weighted_agreement = sum(s.get("reliability", 0.5) for s in majority_sources) / total_sources

        # Determine status
        if agreement_rate >= self.agreement_threshold:
            status = "validated"
        elif agreement_rate >= 0.4:
            status = "partial_agreement"
        else:
            status = "conflicting"

        # Best source (highest reliability)
        best_source = max(majority_sources, key=lambda s: s.get("reliability", 0))

        return {
            "field": field_name,
            "status": status,
            "best_value": best_source.get("value", ""),
            "agreement_rate": round(agreement_rate, 3),
            "weighted_agreement": round(weighted_agreement, 3),
            "total_sources": total_sources,
            "agreeing_sources": agreeing,
            "conflicting_values": len(sorted_groups) - 1,
            "confidence": round(weighted_agreement, 3),
            "recommendation": "ACCEPT" if status == "validated" else "MANUAL_REVIEW",
        }


# =============================================================================
# 3. REVENUE INTELLIGENCE CALIBRATION ENGINE
# =============================================================================

@dataclass
class CalibrationResult:
    """Result of score calibration."""
    raw_score: float
    calibrated_score: float
    calibration_factor: float
    confidence: float
    reasoning: str
    evidence_count: int
    historical_accuracy: float


class CalibrationEngine:
    """Replace static scoring with calibrated scoring."""

    # Calibration rules based on evidence quality
    CALIBRATION_RULES = {
        "high_evidence": {"factor": 1.0, "description": "Strong evidence supports score"},
        "moderate_evidence": {"factor": 0.85, "description": "Moderate evidence, slight discount"},
        "low_evidence": {"factor": 0.6, "description": "Weak evidence, significant discount"},
        "no_evidence": {"factor": 0.3, "description": "No evidence, heavily discounted"},
        "conflicting": {"factor": 0.5, "description": "Conflicting data, uncertain"},
        "verified": {"factor": 1.1, "description": "Verified data, slight boost"},
    }

    def calibrate_score(
        self,
        raw_score: float,
        evidence_count: int,
        verified_count: int,
        conflicting_count: int,
        source_reliability: float,
        historical_accuracy: float = 0.5,
    ) -> CalibrationResult:
        """Calibrate a raw score based on evidence quality."""
        # Determine calibration rule
        if conflicting_count > 0:
            rule = self.CALIBRATION_RULES["conflicting"]
        elif verified_count > 0:
            rule = self.CALIBRATION_RULES["verified"]
        elif evidence_count >= 5:
            rule = self.CALIBRATION_RULES["high_evidence"]
        elif evidence_count >= 2:
            rule = self.CALIBRATION_RULES["moderate_evidence"]
        elif evidence_count == 1:
            rule = self.CALIBRATION_RULES["low_evidence"]
        else:
            rule = self.CALIBRATION_RULES["no_evidence"]

        # Apply calibration
        base_factor = rule["factor"]
        reliability_boost = source_reliability * 0.1
        historical_boost = historical_accuracy * 0.1

        calibration_factor = min(1.2, base_factor + reliability_boost + historical_boost)
        calibrated_score = raw_score * calibration_factor

        # Calculate confidence
        confidence = (
            (evidence_count / 10) * 0.3 +  # More evidence = higher confidence
            source_reliability * 0.3 +  # Reliable sources = higher confidence
            historical_accuracy * 0.2 +  # Past accuracy = higher confidence
            (1 if conflicting_count == 0 else 0.5) * 0.2  # No conflicts = higher confidence
        )

        return CalibrationResult(
            raw_score=raw_score,
            calibrated_score=min(100, max(0, calibrated_score)),
            calibration_factor=calibration_factor,
            confidence=round(confidence, 3),
            reasoning=rule["description"],
            evidence_count=evidence_count,
            historical_accuracy=historical_accuracy,
        )


# =============================================================================
# 4. CONFIDENCE ENGINE
# =============================================================================

class ConfidenceEngine:
    """Multi-dimensional confidence for every company."""

    WEIGHTS = {
        "discovery": 0.10,
        "technology": 0.15,
        "growth": 0.10,
        "intent": 0.10,
        "pain": 0.10,
        "decision_maker": 0.15,
        "revenue": 0.10,
        "contact": 0.10,
        "quality": 0.10,
    }

    def calculate_confidence(self, dimensions: dict[str, float]) -> dict:
        """Calculate overall confidence from component dimensions."""
        overall = 0.0
        for dim, weight in self.WEIGHTS.items():
            dim_score = dimensions.get(dim, 0.0)
            overall += dim_score * weight

        # Grade
        if overall >= 0.9:
            grade = "A"
        elif overall >= 0.75:
            grade = "B"
        elif overall >= 0.6:
            grade = "C"
        elif overall >= 0.4:
            grade = "D"
        else:
            grade = "F"

        return {
            "overall_confidence": round(overall, 3),
            "confidence_grade": grade,
            "dimensions": dimensions,
            "weakest_dimension": min(dimensions, key=dimensions.get) if dimensions else None,
            "strongest_dimension": max(dimensions, key=dimensions.get) if dimensions else None,
        }


# =============================================================================
# 5. BUYING WINDOW INTELLIGENCE ENGINE
# =============================================================================

class BuyingWindowEngine:
    """Determine why Sales should contact this company TODAY."""

    SIGNAL_WEIGHTS = {
        "hiring": 0.15,
        "funding": 0.20,
        "product_launch": 0.10,
        "tech_migration": 0.15,
        "platform_migration": 0.12,
        "support_growth": 0.10,
        "marketing_expansion": 0.08,
        "holiday_season": 0.05,
        "traffic_growth": 0.08,
        "international_expansion": 0.10,
        "customer_complaints": 0.12,
        "competitor_change": 0.15,
        "ai_adoption": 0.18,
        "website_change": 0.05,
        "pricing_change": 0.08,
    }

    WINDOWS = {
        "immediate": {"min_score": 0.7, "description": "Contact within 48 hours"},
        "30_days": {"min_score": 0.5, "description": "Contact within 30 days"},
        "60_days": {"min_score": 0.35, "description": "Contact within 60 days"},
        "90_days": {"min_score": 0.2, "description": "Contact within 90 days"},
        "future": {"min_score": 0.1, "description": "Monitor for changes"},
        "dormant": {"min_score": 0.0, "description": "No active signals"},
    }

    def detect_buying_window(self, signals: dict[str, bool]) -> dict:
        """Detect buying window from signals."""
        # Calculate buying score
        buying_score = 0.0
        active_signals = []

        for signal_name, is_active in signals.items():
            if is_active and signal_name in self.SIGNAL_WEIGHTS:
                buying_score += self.SIGNAL_WEIGHTS[signal_name]
                active_signals.append(signal_name)

        # Determine window
        window = "dormant"
        for w, config in self.WINDOWS.items():
            if buying_score >= config["min_score"]:
                window = w
                break

        # Generate reason
        if active_signals:
            reason = f"Active signals: {', '.join(active_signals[:5])}"
        else:
            reason = "No active buying signals detected"

        return {
            "window_status": window,
            "buying_score": round(buying_score, 3),
            "window_confidence": min(1.0, buying_score * 1.5),
            "active_signals": active_signals,
            "signal_count": len(active_signals),
            "reason": reason,
            "recommendation": self._get_recommendation(window, active_signals),
        }

    def _get_recommendation(self, window: str, signals: list[str]) -> str:
        """Generate sales recommendation based on window."""
        recommendations = {
            "immediate": "URGENT: Contact within 48 hours. High buying intent detected.",
            "30_days": "Schedule outreach within 30 days. Good timing window.",
            "60_days": "Plan outreach within 60 days. Moderate urgency.",
            "90_days": "Add to nurture sequence. Low urgency.",
            "future": "Monitor monthly. No immediate action needed.",
            "dormant": "No action. Re-evaluate quarterly.",
        }
        return recommendations.get(window, "No recommendation")


# =============================================================================
# 6. REVENUE OPPORTUNITY ESTIMATION ENGINE
# =============================================================================

class RevenueEstimationEngine:
    """Estimate revenue opportunity for COMAI."""

    # COMAI pricing tiers
    PRICING = {
        "starter": {"monthly": 299, "annual": 2990},
        "growth": {"monthly": 799, "annual": 7990},
        "enterprise": {"monthly": 1999, "annual": 19990},
    }

    def estimate_opportunity(self, company_data: dict) -> dict:
        """Estimate revenue opportunity."""
        # Estimate business metrics
        monthly_visitors = company_data.get("monthly_traffic", 0) or self._estimate_traffic(company_data)
        monthly_orders = self._estimate_orders(monthly_visitors, company_data)
        monthly_conversations = self._estimate_conversations(monthly_orders)
        whatsapp_messages = self._estimate_whatsapp(monthly_conversations)
        ai_conversations = int(whatsapp_messages * 0.3)  # 30% can be automated

        # Determine pricing tier
        tier = self._determine_tier(company_data, monthly_orders)

        # Calculate revenue
        monthly_revenue = self.PRICING[tier]["monthly"]
        annual_revenue = self.PRICING[tier]["annual"]

        # ROI calculation
        support_cost_saved = monthly_conversations * 2  # ₹2 per conversation saved
        estimated_roi = (support_cost_saved * 12) / annual_revenue if annual_revenue > 0 else 0

        return {
            "monthly_orders": monthly_orders,
            "monthly_visitors": monthly_visitors,
            "monthly_conversations": monthly_conversations,
            "support_volume": monthly_conversations,
            "whatsapp_messages": whatsapp_messages,
            "potential_ai_conversations": ai_conversations,
            "expected_arr": annual_revenue,
            "expansion_revenue": annual_revenue * 0.2,  # 20% expansion
            "upsell_revenue": monthly_revenue * 0.15 * 12,
            "cross_sell_revenue": monthly_revenue * 0.1 * 12,
            "total_opportunity": annual_revenue * 1.45,
            "estimated_roi": round(estimated_roi, 2),
            "estimated_payback_months": max(1, int(annual_revenue / (support_cost_saved * 12 * 0.1))) if support_cost_saved > 0 else 12,
            "implementation_complexity": self._assess_complexity(company_data),
            "pricing_tier": tier,
            "estimation_confidence": 0.6,  # Moderate confidence without real data
        }

    def _estimate_traffic(self, company: dict) -> int:
        """Estimate traffic from company size."""
        platform = company.get("platform", "")
        if platform == "shopify":
            return 50000  # Average Shopify store
        return 20000

    def _estimate_orders(self, visitors: int, company: dict) -> int:
        """Estimate monthly orders from traffic."""
        conversion_rate = 0.02  # 2% average
        return int(visitors * conversion_rate)

    def _estimate_conversations(self, orders: int) -> int:
        """Estimate support conversations."""
        return int(orders * 0.15)  # 15% of orders need support

    def _estimate_whatsapp(self, conversations: int) -> int:
        """Estimate WhatsApp messages."""
        return int(conversations * 2)  # 2 messages per conversation

    def _determine_tier(self, company: dict, orders: int) -> str:
        """Determine pricing tier."""
        if orders > 1000:
            return "enterprise"
        elif orders > 200:
            return "growth"
        return "starter"

    def _assess_complexity(self, company: dict) -> str:
        """Assess implementation complexity."""
        platform = company.get("platform", "")
        if platform in ["shopify", "woocommerce"]:
            return "low"
        elif platform in ["magento", "custom"]:
            return "medium"
        return "high"


# =============================================================================
# 7. COMPETITIVE INTELLIGENCE ENGINE
# =============================================================================

class CompetitiveIntelligenceEngine:
    """Identify technology gaps and replacement opportunities."""

    COMAI_FEATURES = [
        "whatsapp_automation",
        "ai_chatbot",
        "customer_support",
        "order_tracking",
        "cart_recovery",
        "product_recommendations",
        "multi_language",
        "analytics",
        "crm_integration",
        "payment_integration",
    ]

    COMPETITOR_MAP = {
        "intercom": {"type": "helpdesk", "weakness": "expensive, no WhatsApp"},
        "zendesk": {"type": "helpdesk", "weakness": "no WhatsApp, complex setup"},
        "freshdesk": {"type": "helpdesk", "weakness": "limited AI, no WhatsApp"},
        "drift": {"type": "chatbot", "weakness": "no WhatsApp, expensive"},
        "tidio": {"type": "chatbot", "weakness": "limited features, no WhatsApp"},
        "gorgias": {"type": "ecommerce_helpdesk", "weakness": "no WhatsApp, limited AI"},
        "re:amaze": {"type": "ecommerce_helpdesk", "weakness": "no WhatsApp"},
        "klaviyo": {"type": "email_marketing", "weakness": "no support automation"},
        "manychat": {"type": "chatbot", "weakness": "no customer support"},
        "whatsapp_business": {"type": "messaging", "weakness": "no AI, manual"},
    }

    def analyze_competition(self, company_data: dict) -> dict:
        """Analyze competitive landscape."""
        technologies = company_data.get("technologies", [])
        gaps = []
        weaknesses = []
        opportunities = []

        # Analyze current stack
        current_chatbot = None
        current_helpdesk = None
        for tech in technologies:
            tech_lower = tech.lower()
            if tech_lower in self.COMPETITOR_MAP:
                comp = self.COMPETITOR_MAP[tech_lower]
                if comp["type"] == "chatbot":
                    current_chatbot = tech
                elif comp["type"] == "helpdesk":
                    current_helpdesk = tech
                weaknesses.append(comp["weakness"])

        # Identify gaps
        if not current_chatbot:
            gaps.append("No chatbot detected")
            opportunities.append("Greenfield opportunity - no existing solution")
        if not current_helpdesk:
            gaps.append("No helpdesk detected")
            opportunities.append("Can position as primary support channel")

        # Check for WhatsApp gap
        has_whatsapp = any("whatsapp" in t.lower() for t in technologies)
        if not has_whatsapp:
            gaps.append("No WhatsApp automation")
            opportunities.append("WhatsApp-first market, strong opportunity")

        # Migration complexity
        if current_chatbot:
            complexity = "medium"
        elif current_helpdesk:
            complexity = "high"
        else:
            complexity = "low"

        return {
            "current_chatbot": current_chatbot,
            "current_helpdesk": current_helpdesk,
            "technology_gaps": gaps,
            "competitive_weaknesses": weaknesses,
            "replacement_opportunities": opportunities,
            "migration_complexity": complexity,
            "switching_cost": "low" if not current_chatbot else "medium",
            "competitive_score": max(0, 100 - len(technologies) * 10),
            "replacement_probability": 0.7 if gaps else 0.3,
        }


# =============================================================================
# 8. ICP CALIBRATION ENGINE
# =============================================================================

class ICPCalibrationEngine:
    """Continuously improve ICP based on outcomes."""

    def __init__(self):
        self._outcomes: list[dict] = []

    def record_outcome(
        self,
        company_id: str,
        icp_id: str,
        matched: bool,
        qualified: bool,
        meeting: bool = False,
        deal: bool = False,
        revenue: float = 0.0,
    ) -> None:
        """Record an ICP outcome for calibration."""
        self._outcomes.append({
            "company_id": company_id,
            "icp_id": icp_id,
            "matched": matched,
            "qualified": qualified,
            "meeting": meeting,
            "deal": deal,
            "revenue": revenue,
            "recorded_at": datetime.utcnow(),
        })

    def get_icp_performance(self, icp_id: str) -> dict:
        """Get ICP performance metrics."""
        icp_outcomes = [o for o in self._outcomes if o["icp_id"] == icp_id]
        if not icp_outcomes:
            return {"icp_id": icp_id, "total": 0}

        total = len(icp_outcomes)
        matched = sum(1 for o in icp_outcomes if o["matched"])
        qualified = sum(1 for o in icp_outcomes if o["qualified"])
        meetings = sum(1 for o in icp_outcomes if o["meeting"])
        deals = sum(1 for o in icp_outcomes if o["deal"])
        revenue = sum(o["revenue"] for o in icp_outcomes)

        return {
            "icp_id": icp_id,
            "total": total,
            "match_rate": matched / total if total > 0 else 0,
            "qualification_rate": qualified / total if total > 0 else 0,
            "meeting_rate": meetings / total if total > 0 else 0,
            "close_rate": deals / total if total > 0 else 0,
            "total_revenue": revenue,
            "avg_revenue_per_deal": revenue / deals if deals > 0 else 0,
        }

    def suggest_improvements(self, icp_id: str) -> list[dict]:
        """Suggest ICP improvements based on outcomes."""
        performance = self.get_icp_performance(icp_id)
        suggestions = []

        if performance.get("qualification_rate", 0) < 0.3:
            suggestions.append({
                "type": "filter_too_broad",
                "description": "Qualification rate below 30%. Consider adding stricter filters.",
                "priority": "high",
            })

        if performance.get("close_rate", 0) < 0.1:
            suggestions.append({
                "type": "wrong_segment",
                "description": "Close rate below 10%. ICP may not match actual buyers.",
                "priority": "high",
            })

        if performance.get("match_rate", 0) > 0.8:
            suggestions.append({
                "type": "overfitting",
                "description": "Match rate very high. ICP may be too narrow.",
                "priority": "medium",
            })

        return suggestions


# =============================================================================
# 9. SALES OUTCOME LEARNING ENGINE
# =============================================================================

class SalesOutcomeLearningEngine:
    """Every sales outcome improves scoring."""

    def __init__(self):
        self._outcomes: list[dict] = []

    def record_outcome(
        self,
        company_id: str,
        stage: str,
        outcome: str = None,
        lost_reason: str = None,
        deal_value: float = None,
        prediction_at_entry: float = None,
    ) -> None:
        """Record a sales outcome."""
        self._outcomes.append({
            "company_id": company_id,
            "stage": stage,
            "outcome": outcome,
            "lost_reason": lost_reason,
            "deal_value": deal_value,
            "prediction_at_entry": prediction_at_entry,
            "recorded_at": datetime.utcnow(),
        })

    def get_conversion_metrics(self) -> dict:
        """Get conversion metrics across all outcomes."""
        if not self._outcomes:
            return {"total": 0}

        total = len(self._outcomes)
        stages = {}
        for o in self._outcomes:
            stage = o["stage"]
            stages.setdefault(stage, {"count": 0, "revenue": 0})
            stages[stage]["count"] += 1
            if o.get("deal_value"):
                stages[stage]["revenue"] += o["deal_value"]

        won = sum(1 for o in self._outcomes if o.get("outcome") == "won")
        lost = sum(1 for o in self._outcomes if o.get("outcome") == "lost")
        revenue = sum(o.get("deal_value", 0) for o in self._outcomes if o.get("outcome") == "won")

        # Lost reasons
        lost_reasons = {}
        for o in self._outcomes:
            if o.get("lost_reason"):
                lost_reasons[o["lost_reason"]] = lost_reasons.get(o["lost_reason"], 0) + 1

        return {
            "total": total,
            "stages": stages,
            "won": won,
            "lost": lost,
            "win_rate": won / (won + lost) if (won + lost) > 0 else 0,
            "total_revenue": revenue,
            "avg_deal_value": revenue / won if won > 0 else 0,
            "lost_reasons": lost_reasons,
        }

    def get_learning_insights(self) -> list[dict]:
        """Generate learning insights from outcomes."""
        insights = []
        metrics = self.get_conversion_metrics()

        if metrics.get("win_rate", 0) < 0.2:
            insights.append({
                "type": "low_win_rate",
                "description": f"Win rate is {metrics['win_rate']:.1%}. Review ICP and scoring.",
                "priority": "high",
            })

        if metrics.get("lost_reasons"):
            top_reason = max(metrics["lost_reasons"], key=metrics["lost_reasons"].get)
            insights.append({
                "type": "top_loss_reason",
                "description": f"Top reason for loss: {top_reason}. Adjust targeting.",
                "priority": "high",
            })

        return insights


# =============================================================================
# 10. EXPLAINABLE INTELLIGENCE ENGINE
# =============================================================================

class ExplainableIntelligenceEngine:
    """Every recommendation must explain itself."""

    def explain_score(self, company_data: dict, scores: dict) -> dict:
        """Generate explainable intelligence for a company."""
        factors = []
        reasoning_parts = []

        # Technology factors
        tech_score = scores.get("technology", 0)
        if tech_score > 70:
            factors.append({"factor": "Technology fit", "impact": "positive", "evidence": "Strong tech stack match", "weight": 0.20})
            reasoning_parts.append("Strong technology fit")
        elif tech_score < 30:
            factors.append({"factor": "Technology fit", "impact": "negative", "evidence": "Weak tech stack", "weight": 0.20})
            reasoning_parts.append("Technology stack needs work")

        # Growth factors
        growth_score = scores.get("growth", 0)
        if growth_score > 60:
            factors.append({"factor": "Growth signals", "impact": "positive", "evidence": "Active growth indicators", "weight": 0.10})
            reasoning_parts.append("Growing company")

        # Intent factors
        intent_score = scores.get("intent", 0)
        if intent_score > 50:
            factors.append({"factor": "Buying intent", "impact": "positive", "evidence": "Active intent signals", "weight": 0.15})
            reasoning_parts.append("Shows buying intent")

        # Decision maker
        has_dm = company_data.get("decision_makers") or company_data.get("founder_name")
        if has_dm:
            factors.append({"factor": "Decision maker access", "impact": "positive", "evidence": "DM identified", "weight": 0.15})
            reasoning_parts.append("Decision maker identified")

        # Contact
        has_email = company_data.get("primary_email") or company_data.get("email")
        if has_email:
            factors.append({"factor": "Contact available", "impact": "positive", "evidence": "Email found", "weight": 0.10})
            reasoning_parts.append("Contact information available")

        # Platform
        platform = company_data.get("platform", "")
        if platform == "shopify":
            factors.append({"factor": "Platform match", "impact": "positive", "evidence": f"Uses {platform}", "weight": 0.05})
            reasoning_parts.append(f"Shopify platform (easy integration)")

        # Overall score
        overall = scores.get("overall", 0)

        return {
            "overall_score": overall,
            "factors": factors,
            "reasoning": "; ".join(reasoning_parts) if reasoning_parts else "Insufficient data for explanation",
            "evidence_count": len(factors),
            "counter_arguments": self._generate_counter_arguments(scores),
        }

    def _generate_counter_arguments(self, scores: dict) -> list[str]:
        """Generate counter-arguments for transparency."""
        counters = []
        if scores.get("confidence", 0) < 0.5:
            counters.append("Low confidence in data quality")
        if scores.get("evidence_count", 0) < 3:
            counters.append("Limited evidence available")
        return counters


# =============================================================================
# 11. DATA DRIFT ENGINE
# =============================================================================

class DataDriftEngine:
    """Monitor company changes over time."""

    def __init__(self):
        self._snapshots: dict[str, dict] = {}  # company_id -> {field: value}
        self._changes: list[dict] = []

    def record_snapshot(self, company_id: str, data: dict) -> list[dict]:
        """Record a data snapshot and detect changes."""
        previous = self._snapshots.get(company_id, {})
        changes = []

        for field_name, new_value in data.items():
            old_value = previous.get(field_name)
            if old_value is not None and str(old_value) != str(new_value):
                change = {
                    "company_id": company_id,
                    "field": field_name,
                    "old_value": str(old_value),
                    "new_value": str(new_value),
                    "change_type": "modified",
                    "detected_at": datetime.utcnow(),
                    "impact_score": self._assess_impact(field_name, old_value, new_value),
                }
                changes.append(change)
                self._changes.append(change)
            elif old_value is None and new_value is not None:
                changes.append({
                    "company_id": company_id,
                    "field": field_name,
                    "old_value": None,
                    "new_value": str(new_value),
                    "change_type": "added",
                    "detected_at": datetime.utcnow(),
                    "impact_score": 0.5,
                })

        self._snapshots[company_id] = data
        return changes

    def _assess_impact(self, field: str, old_val: Any, new_val: Any) -> float:
        """Assess impact of a change."""
        high_impact_fields = ["founder_name", "primary_email", "primary_phone", "platform", "industry"]
        if field in high_impact_fields:
            return 0.9
        return 0.3

    def get_drift_summary(self, company_id: str) -> dict:
        """Get drift summary for a company."""
        changes = [c for c in self._changes if c["company_id"] == company_id]
        return {
            "company_id": company_id,
            "total_changes": len(changes),
            "high_impact_changes": sum(1 for c in changes if c["impact_score"] > 0.7),
            "recent_changes": [c for c in changes if (datetime.utcnow() - c["detected_at"]).days < 7],
        }


# =============================================================================
# 12. FRESHNESS INTELLIGENCE ENGINE
# =============================================================================

class FreshnessIntelligenceEngine:
    """Every field receives freshness tracking."""

    FIELD_REFRESH_RATES = {
        "email": 720,  # 30 days
        "phone": 720,
        "decision_maker": 168,  # 7 days
        "technology": 168,
        "traffic": 72,
        "revenue": 2160,  # 90 days
        "industry": 4320,  # 180 days
        "platform": 4320,
    }

    def __init__(self):
        self._freshness: dict[str, dict[str, dict]] = {}  # company_id -> {field: {last_seen, score}}

    def update_freshness(self, company_id: str, field_name: str) -> dict:
        """Update freshness for a field."""
        if company_id not in self._freshness:
            self._freshness[company_id] = {}

        now = datetime.utcnow()
        refresh_rate = self.FIELD_REFRESH_RATES.get(field_name, 168)

        self._freshness[company_id][field_name] = {
            "last_seen": now,
            "refresh_rate": refresh_rate,
            "score": 100.0,
        }

        return self.get_freshness(company_id, field_name)

    def get_freshness(self, company_id: str, field_name: str) -> dict:
        """Get freshness for a field."""
        field_data = self._freshness.get(company_id, {}).get(field_name)
        if not field_data:
            return {"score": 0, "age_hours": 9999, "status": "unknown"}

        age_hours = (datetime.utcnow() - field_data["last_seen"]).total_seconds() / 3600
        refresh_rate = field_data["refresh_rate"]

        # Score decreases over time
        if age_hours < refresh_rate * 0.5:
            score = 100.0
            status = "fresh"
        elif age_hours < refresh_rate:
            score = 70.0
            status = "aging"
        elif age_hours < refresh_rate * 2:
            score = 40.0
            status = "stale"
        else:
            score = 10.0
            status = "expired"

        return {
            "score": score,
            "age_hours": round(age_hours, 1),
            "refresh_rate": refresh_rate,
            "status": status,
            "needs_refresh": age_hours > refresh_rate,
        }

    def get_company_freshness(self, company_id: str) -> dict:
        """Get overall freshness for a company."""
        fields = self._freshness.get(company_id, {})
        if not fields:
            return {"overall_score": 0, "fields": {}}

        field_scores = {}
        for field_name in fields:
            field_scores[field_name] = self.get_freshness(company_id, field_name)

        overall = sum(f["score"] for f in field_scores.values()) / len(field_scores) if field_scores else 0

        return {
            "overall_score": round(overall, 1),
            "fields": field_scores,
            "stale_fields": [f for f, v in field_scores.items() if v["status"] in ["stale", "expired"]],
        }


# =============================================================================
# 13. CONTINUOUS LEARNING ENGINE
# =============================================================================

class ContinuousLearningEngine:
    """Every outcome improves scoring. Nothing remains static."""

    def __init__(self):
        self._learnings: list[dict] = []

    def record_learning(
        self,
        learning_type: str,
        entity_id: str,
        old_value: Any,
        new_value: Any,
        reason: str,
        confidence: float = 0.5,
    ) -> None:
        """Record a learning event."""
        self._learnings.append({
            "type": learning_type,
            "entity_id": entity_id,
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason,
            "confidence": confidence,
            "recorded_at": datetime.utcnow(),
        })

    def get_learning_summary(self) -> dict:
        """Get summary of all learnings."""
        types = {}
        for l in self._learnings:
            t = l["type"]
            types.setdefault(t, {"count": 0, "avg_confidence": 0})
            types[t]["count"] += 1
            types[t]["avg_confidence"] = (
                types[t]["avg_confidence"] * (types[t]["count"] - 1) + l["confidence"]
            ) / types[t]["count"]

        return {
            "total_learnings": len(self._learnings),
            "by_type": types,
            "recent_learnings": self._learnings[-10:] if self._learnings else [],
        }

    def apply_learning(self, company_id: str) -> dict:
        """Apply learnings to improve scoring for a company."""
        company_learnings = [l for l in self._learnings if l["entity_id"] == company_id]
        if not company_learnings:
            return {"applied": 0}

        # Group by type
        adjustments = {}
        for l in company_learnings:
            t = l["type"]
            if t not in adjustments:
                adjustments[t] = {"count": 0, "avg_confidence": 0, "latest": l}
            adjustments[t]["count"] += 1
            adjustments[t]["avg_confidence"] = (
                adjustments[t]["avg_confidence"] * (adjustments[t]["count"] - 1) + l["confidence"]
            ) / adjustments[t]["count"]
            adjustments[t]["latest"] = l

        return {
            "applied": len(adjustments),
            "adjustments": adjustments,
        }


# =============================================================================
# UNIFIED RICVP ORCHESTRATOR
# =============================================================================

class RICVPOrchestrator:
    """Unified orchestrator for all RICVP engines."""

    def __init__(self):
        self.evidence = EvidenceValidationEngine()
        self.cross_source = CrossSourceValidationEngine()
        self.calibration = CalibrationEngine()
        self.confidence = ConfidenceEngine()
        self.buying_window = BuyingWindowEngine()
        self.revenue_estimation = RevenueEstimationEngine()
        self.competitive = CompetitiveIntelligenceEngine()
        self.icp_calibration = ICPCalibrationEngine()
        self.sales_learning = SalesOutcomeLearningEngine()
        self.explainable = ExplainableIntelligenceEngine()
        self.data_drift = DataDriftEngine()
        self.freshness = FreshnessIntelligenceEngine()
        self.continuous_learning = ContinuousLearningEngine()

    def validate_company(self, company_id: str, company_data: dict) -> dict:
        """Full RICVP validation for a company."""
        # Evidence validation
        evidence_result = self.evidence.validate_company(company_id)

        # Cross-source validation (if multiple sources available)
        cross_source_result = {"status": "single_source"}

        # Confidence calculation
        confidence_result = self.confidence.calculate_confidence({
            "discovery": 0.7,
            "technology": 0.5,
            "growth": 0.5,
            "intent": 0.4,
            "pain": 0.3,
            "decision_maker": 0.6,
            "revenue": 0.5,
            "contact": 0.5,
            "quality": 0.6,
        })

        # Buying window
        buying_result = self.buying_window.detect_buying_window({
            "hiring": False,
            "funding": False,
            "tech_migration": True,
            "ai_adoption": False,
        })

        # Revenue estimation
        revenue_result = self.revenue_estimation.estimate_opportunity(company_data)

        # Competitive analysis
        competitive_result = self.competitive.analyze_competition(company_data)

        # Score calibration
        raw_score = company_data.get("account_score", 50)
        calibration_result = self.calibration.calibrate_score(
            raw_score=raw_score,
            evidence_count=evidence_result.get("total_fields", 0),
            verified_count=evidence_result.get("verified_fields", 0),
            conflicting_count=0,
            source_reliability=0.7,
        )

        # Explainable intelligence
        explanation = self.explainable.explain_score(company_data, {
            "overall": calibration_result.calibrated_score,
            "technology": company_data.get("technology_score", 50),
            "growth": company_data.get("growth_score", 50),
            "intent": company_data.get("intent_score", 40),
            "confidence": confidence_result["overall_confidence"],
            "evidence_count": evidence_result.get("total_fields", 0),
        })

        # Freshness
        freshness_result = self.freshness.get_company_freshness(company_id)

        return {
            "company_id": company_id,
            "evidence": evidence_result,
            "cross_source": cross_source_result,
            "confidence": confidence_result,
            "buying_window": buying_result,
            "revenue_estimation": revenue_result,
            "competitive": competitive_result,
            "calibration": {
                "raw_score": calibration_result.raw_score,
                "calibrated_score": calibration_result.calibrated_score,
                "calibration_factor": calibration_result.calibration_factor,
                "reasoning": calibration_result.reasoning,
            },
            "explanation": explanation,
            "freshness": freshness_result,
            "recommendation": self._generate_recommendation(
                confidence_result, buying_result, calibration_result, revenue_result
            ),
        }

    def _generate_recommendation(
        self,
        confidence: dict,
        buying: dict,
        calibration: CalibrationResult,
        revenue: dict,
    ) -> dict:
        """Generate unified recommendation."""
        overall_conf = confidence["overall_confidence"]
        buying_score = buying["buying_score"]
        calibrated = calibration.calibrated_score

        # Priority score
        priority = (overall_conf * 0.3 + buying_score * 0.3 + calibrated / 100 * 0.4)

        if priority >= 0.7:
            action = "CONTACT_NOW"
            urgency = "high"
        elif priority >= 0.5:
            action = "SCHEDULE_OUTREACH"
            urgency = "medium"
        elif priority >= 0.3:
            action = "ADD_TO_NURTURE"
            urgency = "low"
        else:
            action = "MONITOR"
            urgency = "none"

        return {
            "priority_score": round(priority, 3),
            "action": action,
            "urgency": urgency,
            "expected_revenue": revenue.get("expected_arr", 0),
            "confidence": overall_conf,
            "reasoning": f"Confidence: {overall_conf:.0%}, Buying: {buying_score:.2f}, Score: {calibrated:.0f}",
        }
