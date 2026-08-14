"""CIR v1 types — evidence-attributed company intelligence."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

UNKNOWN = "UNKNOWN"


class CirVerdict(StrEnum):
    RECONSTRUCTED = "RECONSTRUCTED"
    PARTIAL = "PARTIAL"
    SKIPPED = "SKIPPED"
    REJECTED = "REJECTED"


class CirClassification(StrEnum):
    REJECTED = "Rejected"
    OBSERVED = "Observed"
    PROMISING = "Promising"
    REVENUE_READY = "Revenue Ready"
    PRIORITY_ACCOUNT = "Priority Account"


class AttributedValue(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: str = UNKNOWN
    confidence: float = 0.0
    source: str = UNKNOWN
    page: str | None = None
    excerpt: str | None = None
    evidence: list[str] = Field(default_factory=list)


class WebsitePage(BaseModel):
    model_config = ConfigDict(frozen=True)

    url: str
    path: str
    title: str = UNKNOWN
    description: str = UNKNOWN
    headings: list[str] = Field(default_factory=list)
    text: str = ""
    structured_data: list[dict[str, Any]] = Field(default_factory=list)
    open_graph: dict[str, str] = Field(default_factory=dict)
    navigation: list[str] = Field(default_factory=list)
    footer: str = UNKNOWN
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str = "website_crawl"
    evidence: list[str] = Field(default_factory=list)


class WebsiteCorpus(BaseModel):
    model_config = ConfigDict(frozen=True)

    website: str
    domain: str
    pages: list[WebsitePage] = Field(default_factory=list)
    page_count: int = 0
    crawled: bool = False
    evidence: list[str] = Field(default_factory=list)


class CompanyBusinessProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    description: AttributedValue = Field(default_factory=AttributedValue)
    tagline: AttributedValue = Field(default_factory=AttributedValue)
    mission: AttributedValue = Field(default_factory=AttributedValue)
    vision: AttributedValue = Field(default_factory=AttributedValue)
    industry: AttributedValue = Field(default_factory=AttributedValue)
    business_model: AttributedValue = Field(default_factory=AttributedValue)
    company_type: AttributedValue = Field(default_factory=AttributedValue)
    target_market: AttributedValue = Field(default_factory=AttributedValue)
    primary_product: AttributedValue = Field(default_factory=AttributedValue)
    primary_services: AttributedValue = Field(default_factory=AttributedValue)
    country: AttributedValue = Field(default_factory=AttributedValue)
    locations: AttributedValue = Field(default_factory=AttributedValue)
    languages: AttributedValue = Field(default_factory=AttributedValue)
    customer_type: AttributedValue = Field(default_factory=AttributedValue)
    founded: AttributedValue = Field(default_factory=AttributedValue)
    employee_hints: AttributedValue = Field(default_factory=AttributedValue)
    revenue_hints: AttributedValue = Field(default_factory=AttributedValue)
    enterprise_status: AttributedValue = Field(default_factory=AttributedValue)
    evidence: list[str] = Field(default_factory=list)


class ProductCatalog(BaseModel):
    model_config = ConfigDict(frozen=True)

    products: list[AttributedValue] = Field(default_factory=list)
    solutions: list[AttributedValue] = Field(default_factory=list)
    features: list[AttributedValue] = Field(default_factory=list)
    plans: list[AttributedValue] = Field(default_factory=list)
    pricing: AttributedValue = Field(default_factory=AttributedValue)
    free_trial: AttributedValue = Field(default_factory=AttributedValue)
    enterprise: AttributedValue = Field(default_factory=AttributedValue)
    api: AttributedValue = Field(default_factory=AttributedValue)
    marketplace: AttributedValue = Field(default_factory=AttributedValue)
    mobile_apps: AttributedValue = Field(default_factory=AttributedValue)
    platform: AttributedValue = Field(default_factory=AttributedValue)
    integrations: list[AttributedValue] = Field(default_factory=list)
    capabilities: list[AttributedValue] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class IcpProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    segments: list[AttributedValue] = Field(default_factory=list)
    primary_icp: AttributedValue = Field(default_factory=AttributedValue)
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class TechnologyHit(BaseModel):
    model_config = ConfigDict(frozen=True)

    technology: str
    category: str
    version: str = UNKNOWN
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)
    source: str = "website"


class BuyingSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_type: str
    confidence: float = 0.0
    source: str = UNKNOWN
    timestamp: datetime | str | None = None
    page: str | None = None
    excerpt: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class ServiceMatch(BaseModel):
    model_config = ConfigDict(frozen=True)

    service: str
    need_score: float = 0.0
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)
    reason: str = UNKNOWN
    potential_value: str = UNKNOWN


class OpportunityNarrative(BaseModel):
    model_config = ConfigDict(frozen=True)

    why_this_company: str = UNKNOWN
    why_now: str = UNKNOWN
    what_changed: str = UNKNOWN
    what_pain: str = UNKNOWN
    what_opportunity: str = UNKNOWN
    which_service: str = UNKNOWN
    expected_impact: str = UNKNOWN
    suggested_opening: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class ContactPerson(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    role: str
    profile: str = UNKNOWN
    email: str = UNKNOWN
    phone: str = UNKNOWN
    confidence: float = 0.0
    source: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class RevenueReadinessScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    total: float = 0.0
    identity: float = 0.0
    website: float = 0.0
    business: float = 0.0
    technology: float = 0.0
    icp: float = 0.0
    buying_intent: float = 0.0
    service_match: float = 0.0
    contacts: float = 0.0
    evidence_score: float = 0.0
    trust: float = 0.0
    classification: CirClassification = CirClassification.REJECTED
    breakdown: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class FounderIntelligenceCard(BaseModel):
    model_config = ConfigDict(frozen=True)

    company: str = UNKNOWN
    industry: str = UNKNOWN
    website: str = UNKNOWN
    country: str = UNKNOWN
    employees: str = UNKNOWN
    revenue_readiness: str = UNKNOWN
    readiness_score: float = 0.0
    primary_product: str = UNKNOWN
    primary_opportunity: str = UNKNOWN
    best_service: str = UNKNOWN
    buying_signals: list[str] = Field(default_factory=list)
    decision_makers: list[str] = Field(default_factory=list)
    business_email: str = UNKNOWN
    phone: str = UNKNOWN
    evidence: list[str] = Field(default_factory=list)
    timeline: list[str] = Field(default_factory=list)
    recommended_action: str = UNKNOWN


class CirSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: str
    company_name: str
    website: str
    domain: str
    verdict: CirVerdict = CirVerdict.REJECTED
    erowd_admitted: bool = False
    corpus: WebsiteCorpus | None = None
    business: CompanyBusinessProfile = Field(default_factory=CompanyBusinessProfile)
    products: ProductCatalog = Field(default_factory=ProductCatalog)
    icp: IcpProfile = Field(default_factory=IcpProfile)
    technologies: list[TechnologyHit] = Field(default_factory=list)
    buying_signals: list[BuyingSignal] = Field(default_factory=list)
    service_matches: list[ServiceMatch] = Field(default_factory=list)
    narrative: OpportunityNarrative = Field(default_factory=OpportunityNarrative)
    contacts: list[ContactPerson] = Field(default_factory=list)
    readiness: RevenueReadinessScore = Field(default_factory=RevenueReadinessScore)
    founder_card: FounderIntelligenceCard = Field(default_factory=FounderIntelligenceCard)
    founder_queue_eligible: bool = False
    scoring_version: str = "cir-v1"
    evidence: list[str] = Field(default_factory=list)


class CirRebuildReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_companies: int = 0
    reconstructed: int = 0
    business_profile_pct: float = 0.0
    industry_icp_pct: float = 0.0
    technology_service_pct: float = 0.0
    contact_pct: float = 0.0
    revenue_ready: int = 0
    priority_accounts: int = 0
    founder_queue: int = 0
    false_fabrications: int = 0
    elapsed_ms: float = 0.0
    classification_distribution: dict[str, int] = Field(default_factory=dict)
    top_accounts: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
