"""DQE v2 schemas — Quality Score, Grade, and Report models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class QualityGrade(str, Enum):
    """Quality grades mapped from Quality Score ranges."""
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    REJECT = "Reject"


class FreshnessStatus(str, Enum):
    """Freshness evaluation status with borderline concept."""
    ACCEPTED = "accepted"
    BORDERLINE = "borderline"
    EXPIRED = "expired"


class BuyingSignalVerdict(str, Enum):
    """Buying signal evaluation verdict."""
    VALID = "valid"
    NOT_VALID = "not_valid"
    BORDERLINE = "borderline"


@dataclass(frozen=True)
class ScoreWeight:
    """Configurable weight for a scoring component."""
    name: str
    weight: int  # Must sum to 100
    description: str = ""


DEFAULT_SCORE_WEIGHTS = [
    ScoreWeight(name="freshness", weight=20, description="How recent is the signal"),
    ScoreWeight(name="buying_signal", weight=25, description="Quality of buying signals"),
    ScoreWeight(name="source_trust", weight=10, description="Trust level of data source"),
    ScoreWeight(name="website_quality", weight=10, description="Company website quality"),
    ScoreWeight(name="company_validation", weight=10, description="Company data validation"),
    ScoreWeight(name="icp_match", weight=15, description="Match to Ideal Customer Profile"),
    ScoreWeight(name="region", weight=5, description="Geographic region fit"),
    ScoreWeight(name="industry", weight=5, description="Industry relevance"),
]


@dataclass(frozen=True)
class ScoreComponent:
    """Individual score component with its value and evidence."""
    name: str
    raw_score: float  # 0.0 to 100.0
    weighted_score: float  # raw_score * weight / 100
    weight: int
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QualityScore:
    """Deterministic quality score (0-100) composed of weighted components."""
    total_score: int  # 0-100
    components: list[ScoreComponent]
    calculated_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AuditEntry:
    """Single audit trail entry."""
    gate: str
    decision: str
    timestamp: datetime
    reasons: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QualityEvidence:
    """Evidence collected during quality evaluation."""
    signal_freshness_days: int | None = None
    signal_freshness_status: FreshnessStatus | None = None
    buying_signals_detected: list[str] = field(default_factory=list)
    buying_signal_verdict: BuyingSignalVerdict | None = None
    source_trust_level: str = ""
    website_score: float = 0.0
    company_age_days: int | None = None
    icp_match_score: float = 0.0
    region_match: bool = False
    industry_match: bool = False
    competitor_flag: bool = False
    duplicate_flag: bool = False
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QualityReport:
    """Complete quality report for a company evaluation."""
    id: UUID = field(default_factory=uuid4)
    company_id: UUID = field(default_factory=uuid4)
    company_name: str = ""
    quality_score: QualityScore | None = None
    quality_grade: QualityGrade = QualityGrade.REJECT
    decision: str = "REJECT"  # ACCEPT, HOLD, REJECT
    reasons: list[str] = field(default_factory=list)
    evidence: QualityEvidence = field(default_factory=QualityEvidence)
    audit_trail: list[AuditEntry] = field(default_factory=list)
    gates_passed: list[str] = field(default_factory=list)
    gates_failed: list[str] = field(default_factory=list)
    rejection_reasons: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FreshnessEvaluation:
    """v2 Freshness evaluation result with borderline status."""
    status: FreshnessStatus
    signal_age_days: int
    thresholds: dict[str, int] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BuyingSignalEvaluation:
    """v2 Buying signal evaluation result with explicit lists."""
    verdict: BuyingSignalVerdict
    valid_signals: list[str] = field(default_factory=list)
    not_valid_signals: list[str] = field(default_factory=list)
    borderline_signals: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


def grade_from_score(score: int) -> QualityGrade:
    """Map a quality score (0-100) to a quality grade."""
    if score >= 95:
        return QualityGrade.A_PLUS
    elif score >= 90:
        return QualityGrade.A
    elif score >= 85:
        return QualityGrade.B
    elif score >= 75:
        return QualityGrade.C
    else:
        return QualityGrade.REJECT
