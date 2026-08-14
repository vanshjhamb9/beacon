from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QualityDecision(StrEnum):
    ACCEPT = "accept"
    REVIEW = "review"
    REJECT = "reject"


class QualityGrade(StrEnum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    REJECT = "Reject"


class QualityStage(StrEnum):
    SCHEMA = "schema_validation"
    NORMALIZATION = "normalization"
    SPAM = "spam_detection"
    SOURCE_TRUST = "source_trust"
    FRESHNESS = "freshness"
    COMPLETENESS = "completeness"
    ENTITY_CONFIDENCE = "entity_confidence"
    DUPLICATE = "duplicate_detection"
    QUALITY_SCORE = "quality_score"


class QualityEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID | None = None
    source: str
    url: str
    title: str
    content: str
    published_at: datetime
    collected_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    event_hash: str | None = None

    @property
    def text(self) -> str:
        return f"{self.title}\n{self.content}"


class NormalizedQualityEvent(QualityEvent):
    normalized_language: str = "en"
    content_hash: str
    fingerprint: str


class StageResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    stage: QualityStage
    score: float
    passed: bool
    reason_codes: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0


class QualityReportResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: UUID | None
    source: str
    decision: QualityDecision
    grade: QualityGrade
    schema_score: float
    spam_score: float
    trust_score: float
    freshness_score: float
    completeness_score: float
    entity_confidence_score: float
    duplicate_probability: float
    overall_quality_score: float
    processing_time_ms: float
    queue_time_ms: float | None
    reason_codes: list[str]
    stage_results: list[StageResult]
    normalized_event: NormalizedQualityEvent | None
    explanation: dict[str, Any]


class SourceQualityProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str
    signals_collected: int = 0
    signals_accepted: int = 0
    signals_rejected: int = 0
    spam_rate: float = 0.0
    duplicate_rate: float = 0.0
    average_quality: float = 75.0
    average_confidence: float = 75.0
    average_processing_time_ms: float = 0.0
    collector_health: str = "unknown"
    historical_trend: list[dict[str, Any]] = Field(default_factory=list)
