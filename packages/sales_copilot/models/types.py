from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


INSUFFICIENT = "Insufficient verified information."


class OutreachStyle(StrEnum):
    PROFESSIONAL = "professional"
    CONSULTATIVE = "consultative"
    FOUNDER_TO_FOUNDER = "founder_to_founder"
    ENTERPRISE = "enterprise"
    TECHNICAL = "technical"
    FRIENDLY = "friendly"


class DraftKind(StrEnum):
    EMAIL = "email"
    SUBJECT_LINE = "subject_line"
    LINKEDIN = "linkedin"
    WHATSAPP = "whatsapp"
    VIDEO_SCRIPT = "video_script"
    MEETING_AGENDA = "meeting_agenda"
    DISCOVERY_QUESTION = "discovery_question"
    FOLLOW_UP_1 = "follow_up_1"
    FOLLOW_UP_2 = "follow_up_2"
    FOLLOW_UP_3 = "follow_up_3"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REGENERATED = "regenerated"
    ARCHIVED = "archived"
    FAVORITE = "favorite"


class ReviewAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REGENERATE = "regenerate"
    ARCHIVE = "archive"
    MARK_FAVORITE = "mark_favorite"


class LLMProviderName(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    GROUNDED = "grounded"


class EvidenceItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: str
    summary: str
    source: str
    source_url: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=100.0)
    reference_id: str | None = None


class SectionAttribution(BaseModel):
    model_config = ConfigDict(frozen=True)

    section: str
    evidence_ids: list[str] = Field(default_factory=list)
    evidence_summaries: list[str] = Field(default_factory=list)
    grounded: bool = True
    note: str = ""


class QualityScores(BaseModel):
    model_config = ConfigDict(frozen=True)

    personalization: float = Field(ge=0.0, le=100.0)
    evidence_coverage: float = Field(ge=0.0, le=100.0)
    readability: float = Field(ge=0.0, le=100.0)
    professional_tone: float = Field(ge=0.0, le=100.0)
    length: float = Field(ge=0.0, le=100.0)
    call_to_action: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=100.0)
    overall: float = Field(ge=0.0, le=100.0)


class IntelligenceSection(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    title: str
    content: str
    attribution: SectionAttribution


class OutreachDraft(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: DraftKind
    style: OutreachStyle
    title: str
    body: str
    subject_lines: list[str] = Field(default_factory=list)
    attribution: SectionAttribution
    metadata: dict[str, Any] = Field(default_factory=dict)


class StyleVariantPackage(BaseModel):
    model_config = ConfigDict(frozen=True)

    style: OutreachStyle
    drafts: list[OutreachDraft] = Field(default_factory=list)


class GenerationMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    prompt_version: str
    llm_provider: LLMProviderName
    model: str
    temperature: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    generation_time_ms: float = 0.0
    cost_estimate_usd: float = 0.0


class SalesIntelligencePackage(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    opportunity_id: UUID
    company_name: str
    opportunity_score: float
    recommended_service: str
    business_pain: str
    version: int
    review_status: ReviewStatus = ReviewStatus.PENDING
    is_favorite: bool = False
    sections: list[IntelligenceSection] = Field(default_factory=list)
    style_variants: list[StyleVariantPackage] = Field(default_factory=list)
    evidence_chain: list[EvidenceItem] = Field(default_factory=list)
    quality: QualityScores
    generation: GenerationMetadata
    package_payload: dict[str, Any] = Field(default_factory=dict)


class SalesCopilotInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: UUID
    opportunity_id: UUID
    company_name: str
    domain: str | None = None
    website: str | None = None
    industry: str | None = None
    opportunity_score: float = 0.0
    opportunity_status: str = ""
    opportunity_narrative: str = ""
    business_pain: str = ""
    recommended_service: str = ""
    buyer_persona: str | None = None
    company: dict[str, Any] = Field(default_factory=dict)
    opportunity: dict[str, Any] = Field(default_factory=dict)
    revenue: dict[str, Any] = Field(default_factory=dict)
    lead_enrichment: dict[str, Any] = Field(default_factory=dict)
    verification: dict[str, Any] = Field(default_factory=dict)
    decision_makers: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    quality: dict[str, Any] = Field(default_factory=dict)
    knowledge_graph: dict[str, Any] = Field(default_factory=dict)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    evidence_chain: list[dict[str, Any]] = Field(default_factory=list)
    force_refresh: bool = False
    preferred_provider: LLMProviderName | None = None
    preferred_style: OutreachStyle | None = None


class PromptVersionSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: str
    name: str
    system_prompt: str
    user_prompt_template: str
    temperature: float = 0.2
    model_hint: str = "grounded-v1"
    provider_hint: LLMProviderName = LLMProviderName.GROUNDED


class LLMRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    system_prompt: str
    user_prompt: str
    model: str
    temperature: float = 0.2
    max_tokens: int = 4096


class LLMResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    content: str
    model: str
    provider: LLMProviderName
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    cost_estimate_usd: float = 0.0
    raw: dict[str, Any] = Field(default_factory=dict)


class ReviewRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    action: ReviewAction
    reviewer: str = "operator"
    notes: str = ""
    rating: float | None = Field(default=None, ge=0.0, le=5.0)
