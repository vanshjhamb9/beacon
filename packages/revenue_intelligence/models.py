"""Domain models for Revenue Intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CompanyIntelligence:
    """Complete intelligence profile for a company."""

    company_name: str
    website: str
    domain: str

    pain_score: float = 0.0
    pain_signals: list[str] = field(default_factory=list)

    growth_score: float = 0.0
    growth_signals: list[str] = field(default_factory=list)

    buying_intent: float = 0.0
    intent_signals: list[str] = field(default_factory=list)

    technology_gap: float = 0.0
    tech_gaps: list[str] = field(default_factory=list)

    support_gap: float = 0.0
    support_gaps: list[str] = field(default_factory=list)

    icp_match: bool = False
    icp_score: float = 0.0
    icp_reasons: list[str] = field(default_factory=list)
    rejection_reasons: list[str] = field(default_factory=list)

    revenue_potential: float = 0.0
    probability_to_buy: float = 0.0
    probability_reasons: list[str] = field(default_factory=list)

    why_comai: str = ""
    recommended_pitch: str = ""
    priority: str = "REJECT"
    evidence: list[dict[str, Any]] = field(default_factory=list)

    traffic_score: float = 0.0
    review_score: float = 0.0
    social_growth: float = 0.0
    whatsapp_score: float = 0.0
    founder_score: float = 0.0

    platform: str = ""
    category: str = ""
    product_count: int = 0
    country: str = "India"

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "website": self.website,
            "domain": self.domain,
            "pain_score": round(self.pain_score, 1),
            "pain_signals": self.pain_signals,
            "growth_score": round(self.growth_score, 1),
            "growth_signals": self.growth_signals,
            "buying_intent": round(self.buying_intent, 1),
            "intent_signals": self.intent_signals,
            "technology_gap": round(self.technology_gap, 1),
            "tech_gaps": self.tech_gaps,
            "support_gap": round(self.support_gap, 1),
            "support_gaps": self.support_gaps,
            "icp_match": self.icp_match,
            "icp_score": round(self.icp_score, 1),
            "icp_reasons": self.icp_reasons,
            "rejection_reasons": self.rejection_reasons,
            "revenue_potential": round(self.revenue_potential, 1),
            "probability_to_buy": round(self.probability_to_buy, 1),
            "probability_reasons": self.probability_reasons,
            "why_comai": self.why_comai,
            "recommended_pitch": self.recommended_pitch,
            "priority": self.priority,
            "evidence": self.evidence,
            "traffic_score": round(self.traffic_score, 1),
            "review_score": round(self.review_score, 1),
            "social_growth": round(self.social_growth, 1),
            "whatsapp_score": round(self.whatsapp_score, 1),
            "founder_score": round(self.founder_score, 1),
            "platform": self.platform,
            "category": self.category,
            "product_count": self.product_count,
            "country": self.country,
        }
