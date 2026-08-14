"""Domain models for Sales Intelligence Platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from packages.sales_intelligence_platform.engines.technology_detector import TechnologyProfile
from packages.sales_intelligence_platform.engines.pain_point_detector import PainAnalysis
from packages.sales_intelligence_platform.engines.comai_opportunity_score import OpportunityScore
from packages.sales_intelligence_platform.engines.sales_intel_summary import SalesIntelligenceSummary
from packages.sales_intelligence_platform.engines.call_preparation import CallPreparation


@dataclass
class DecisionMaker:
    """A verified or probable decision maker at a company."""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    normalized_role: str = ""
    department: str = ""
    seniority_rank: int = 99
    work_email: str = ""
    business_phone: str = ""
    linkedin_url: str = ""
    is_primary: bool = False
    is_secondary: bool = False
    buyer_match_score: float = 0.0
    confidence: float = 0.0
    source: str = ""
    source_url: str = ""
    evidence: list[str] = field(default_factory=list)


@dataclass
class ContactChannel:
    """A verified contact channel for outreach."""

    id: str = field(default_factory=lambda: str(uuid4()))
    kind: str = ""  # founder_email, executive_email, business_phone, linkedin_company, etc.
    value: str = ""
    label: str = ""
    rank: int = 99
    confidence: float = 0.0
    source: str = ""
    source_url: str = ""
    is_verified_public: bool = False
    verification_level: str = "UNKNOWN"  # VERIFIED, LIKELY, UNVERIFIED, INVALID, UNKNOWN
    evidence: list[str] = field(default_factory=list)


@dataclass
class BuyingCommittee:
    """The likely buying committee for a COMAI sale."""

    id: str = field(default_factory=lambda: str(uuid4()))
    trigger: str = ""  # hiring, expansion, technology_migration, funding, pain
    founder: str = ""
    hr: str = ""
    operations: str = ""
    technology: str = ""
    growth: str = ""
    finance: str = ""
    members: list[dict[str, str]] = field(default_factory=list)
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)


@dataclass
class EvidenceRecord:
    """Evidence supporting any field in the account."""

    id: str = field(default_factory=lambda: str(uuid4()))
    field_name: str = ""
    field_value: str = ""
    source: str = ""
    source_url: str = ""
    collector: str = ""
    confidence: float = 0.0
    verification_status: str = "UNVERIFIED"
    collected_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class AccountHealth:
    """Health metrics for an account."""

    completeness_pct: float = 0.0
    decision_maker_count: int = 0
    verified_emails: int = 0
    verified_phones: int = 0
    linkedin_coverage: bool = False
    evidence_count: int = 0
    missing_data: list[str] = field(default_factory=list)
    manual_review_needed: bool = False
    sales_ready: bool = False


@dataclass
class AccountScore:
    """Composite account score."""

    total: float = 0.0
    decision_makers: float = 0.0
    verified_email: float = 0.0
    verified_phone: float = 0.0
    linkedin: float = 0.0
    buying_committee: float = 0.0
    evidence: float = 0.0
    completeness: float = 0.0


@dataclass
class Account:
    """Complete sales-ready account."""

    id: str = field(default_factory=lambda: str(uuid4()))
    ecommerce_lead_id: str = ""
    company_name: str = ""
    website: str = ""
    domain: str = ""
    platform: str = ""
    category: str = ""
    country: str = "India"
    city: str = ""
    state: str = ""

    decision_makers: list[DecisionMaker] = field(default_factory=list)
    contact_channels: list[ContactChannel] = field(default_factory=list)
    buying_committee: BuyingCommittee = field(default_factory=BuyingCommittee)
    evidence_records: list[EvidenceRecord] = field(default_factory=list)
    health: AccountHealth = field(default_factory=AccountHealth)
    score: AccountScore = field(default_factory=AccountScore)

    status: str = "NEEDS_ENRICHMENT"  # SALES_READY, NEEDS_ENRICHMENT, MANUAL_REVIEW, REJECTED
    primary_decision_maker: str = ""
    primary_email: str = ""
    primary_phone: str = ""
    primary_linkedin: str = ""

    shopify_detected: bool = False
    woocommerce_detected: bool = False
    chatbot_detected: bool = False
    whatsapp_detected: bool = False
    crm_detected: bool = False

    pain_score: float = 0.0
    growth_score: float = 0.0
    buying_intent: float = 0.0
    probability_to_buy: float = 0.0
    revenue_potential: float = 0.0

    # Sprint 39: Full intelligence data
    technology_profile: TechnologyProfile = field(default_factory=TechnologyProfile)
    pain_analysis: PainAnalysis = field(default_factory=PainAnalysis)
    opportunity_score: OpportunityScore = field(default_factory=OpportunityScore)
    sales_summary: SalesIntelligenceSummary = field(default_factory=SalesIntelligenceSummary)
    call_preparation: CallPreparation = field(default_factory=CallPreparation)
    website_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "ecommerce_lead_id": self.ecommerce_lead_id,
            "company_name": self.company_name,
            "website": self.website,
            "domain": self.domain,
            "platform": self.platform,
            "category": self.category,
            "country": self.country,
            "city": self.city,
            "state": self.state,
            "status": self.status,
            "primary_decision_maker": self.primary_decision_maker,
            "primary_email": self.primary_email,
            "primary_phone": self.primary_phone,
            "primary_linkedin": self.primary_linkedin,
            "decision_makers": [dm.__dict__ for dm in self.decision_makers],
            "contact_channels": [cc.__dict__ for cc in self.contact_channels],
            "buying_committee": self.buying_committee.__dict__,
            "evidence_count": len(self.evidence_records),
            "health": self.health.__dict__,
            "score": self.score.__dict__,
            "shopify_detected": self.shopify_detected,
            "woocommerce_detected": self.woocommerce_detected,
            "chatbot_detected": self.chatbot_detected,
            "whatsapp_detected": self.whatsapp_detected,
            "crm_detected": self.crm_detected,
            "pain_score": self.pain_score,
            "growth_score": self.growth_score,
            "buying_intent": self.buying_intent,
            "probability_to_buy": self.probability_to_buy,
            "revenue_potential": self.revenue_potential,
            # Sprint 39 fields
            "technology_profile": self.technology_profile.__dict__,
            "pain_analysis": {
                "pain_points": [p.__dict__ for p in self.pain_analysis.pain_points],
                "total_pain_score": self.pain_analysis.total_pain_score,
                "top_pain": self.pain_analysis.top_pain,
                "recommended_module": self.pain_analysis.recommended_module,
                "business_value": self.pain_analysis.business_value,
            },
            "opportunity_score": {
                "total_score": self.opportunity_score.total_score,
                "classification": self.opportunity_score.classification,
                "confidence": self.opportunity_score.confidence,
                "score_breakdown": self.opportunity_score.score_breakdown,
            },
            "sales_summary": self.sales_summary.__dict__,
            "call_preparation": self.call_preparation.__dict__,
        }
