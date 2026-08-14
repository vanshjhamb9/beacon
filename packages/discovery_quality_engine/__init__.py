"""Discovery Quality Engine (DQE) — deterministic quality gate between data collection and Opportunity Intelligence."""

from __future__ import annotations

DQE_VERSION = "dqe-v2"

from discovery_quality_engine.buying_signal_engine_v2 import (
    NOT_BUYING_SIGNALS,
    VALID_BUYING_SIGNALS,
    BuyingSignalEngineV2,
)
from discovery_quality_engine.freshness_engine_v2 import FreshnessEngineV2
from discovery_quality_engine.quality_grade_engine import QualityGradeEngine
from discovery_quality_engine.quality_report_engine import QualityReportEngine
from discovery_quality_engine.quality_score_engine import QualityScoreEngine
from discovery_quality_engine.v2_schemas import (
    AuditEntry,
    BuyingSignalEvaluation,
    BuyingSignalVerdict,
    FreshnessEvaluation,
    FreshnessStatus,
    QualityEvidence,
    QualityGrade,
    QualityReport,
    QualityScore,
    ScoreComponent,
    ScoreWeight,
    grade_from_score,
)

__all__ = [
    "DQE_VERSION",
    "BuyingSignalEngineV2",
    "FreshnessEngineV2",
    "QualityGradeEngine",
    "QualityReportEngine",
    "QualityScoreEngine",
    "VALID_BUYING_SIGNALS",
    "NOT_BUYING_SIGNALS",
    "AuditEntry",
    "BuyingSignalEvaluation",
    "BuyingSignalVerdict",
    "FreshnessEvaluation",
    "FreshnessStatus",
    "QualityEvidence",
    "QualityGrade",
    "QualityReport",
    "QualityScore",
    "ScoreComponent",
    "ScoreWeight",
    "grade_from_score",
]
