from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SalesIntelligencePackResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    snapshot_id: str | None = None
    company_id: str
    company_name: str
    opportunity_id: str | None = None
    buying_intent: dict[str, Any] = Field(default_factory=dict)
    psychology: dict[str, Any] = Field(default_factory=dict)
    objections: list[dict[str, Any]] = Field(default_factory=list)
    offer: dict[str, Any] = Field(default_factory=dict)
    trust: dict[str, Any] = Field(default_factory=dict)
    proposal: dict[str, Any] = Field(default_factory=dict)
    meeting_coach: dict[str, Any] = Field(default_factory=dict)
    reply_intelligence: list[dict[str, Any]] = Field(default_factory=list)
    memory: dict[str, Any] = Field(default_factory=dict)
    score: dict[str, Any] = Field(default_factory=dict)
    scoring_version: str | None = None
    evidence_chain: list[str] = Field(default_factory=list)
    buying_intent_score: float | None = None
    buying_stage: str | None = None
    urgency: str | None = None
    primary_offer: str | None = None
    deal_probability: float | None = None
    close_probability: float | None = None
    created_at: str | None = None


class SalesIntelligenceDashboardResponse(BaseModel):
    total_evaluated: int = 0
    hot_intent: int = 0
    high_close_probability: int = 0
    avg_intent: float = 0.0
    avg_deal_probability: float = 0.0
    top_accounts: list[dict[str, Any]] = Field(default_factory=list)
    scoring_version: str = "si-v1"


class SalesIntelligenceRefreshResponse(BaseModel):
    refreshed: bool = True
    pack: SalesIntelligencePackResponse
