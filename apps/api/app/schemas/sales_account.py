from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DecisionMakerResponse(BaseModel):
    name: str
    normalized_role: str
    department: str = ""
    work_email: str = ""
    business_phone: str = ""
    linkedin_url: str = ""
    confidence: float
    source: str
    is_primary: bool = False
    is_secondary: bool = False

    model_config = {"from_attributes": True}


class ContactChannelResponse(BaseModel):
    kind: str
    value: str
    label: str = ""
    confidence: float
    verification_level: str
    source: str
    is_verified_public: bool = False

    model_config = {"from_attributes": True}


class BuyingCommitteeResponse(BaseModel):
    trigger: str
    founder: str = ""
    operations: str = ""
    technology: str = ""
    growth: str = ""
    members: list[dict[str, str]] = Field(default_factory=list)
    confidence: float

    model_config = {"from_attributes": True}


class AccountHealthResponse(BaseModel):
    completeness_pct: float
    decision_maker_count: int
    verified_emails: int
    verified_phones: int
    linkedin_coverage: bool
    evidence_count: int
    missing_data: list[str] = Field(default_factory=list)
    manual_review_needed: bool
    sales_ready: bool

    model_config = {"from_attributes": True}


class AccountScoreResponse(BaseModel):
    total: float
    decision_makers: float
    verified_email: float
    verified_phone: float
    linkedin: float
    buying_committee: float
    evidence: float
    completeness: float

    model_config = {"from_attributes": True}


class SalesAccountResponse(BaseModel):
    id: str | UUID
    ecommerce_lead_id: str
    company_name: str
    website: str
    domain: str
    platform: str
    category: str
    country: str
    city: str
    state: str
    status: str
    primary_decision_maker: str
    primary_email: str
    primary_phone: str
    primary_linkedin: str
    shopify_detected: bool
    woocommerce_detected: bool
    chatbot_detected: bool
    whatsapp_detected: bool
    crm_detected: bool
    pain_score: float
    growth_score: float
    buying_intent: float
    probability_to_buy: float
    revenue_potential: float
    account_score: float
    completeness_pct: float
    decision_makers: list[DecisionMakerResponse] = Field(default_factory=list)
    contact_channels: list[ContactChannelResponse] = Field(default_factory=list)
    buying_committee: BuyingCommitteeResponse | None = None
    health: AccountHealthResponse | None = None
    score: AccountScoreResponse | None = None
    evidence_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    # Sprint 39 fields
    technology_profile: dict[str, Any] = Field(default_factory=dict)
    pain_analysis: dict[str, Any] = Field(default_factory=dict)
    opportunity_score: dict[str, Any] = Field(default_factory=dict)
    sales_summary: dict[str, Any] = Field(default_factory=dict)
    call_preparation: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class SalesAccountListResponse(BaseModel):
    accounts: list[SalesAccountResponse]
    total: int
    page: int
    page_size: int


class SalesDashboardResponse(BaseModel):
    total_accounts: int
    sales_ready: int
    needs_enrichment: int
    manual_review: int
    top_buyers: list[dict[str, Any]] = Field(default_factory=list)
    top_pain: list[dict[str, Any]] = Field(default_factory=list)
    highest_probability: list[dict[str, Any]] = Field(default_factory=list)
    missing_email_count: int = 0
    missing_phone_count: int = 0
    missing_dm_count: int = 0
    platforms: dict[str, int] = Field(default_factory=dict)
    categories: dict[str, int] = Field(default_factory=dict)
    avg_score: float = 0.0


class SalesAccountRefreshRequest(BaseModel):
    lead_ids: list[str] = Field(default_factory=list)


class SalesAccountRefreshResponse(BaseModel):
    status: str
    processed: int
    message: str
