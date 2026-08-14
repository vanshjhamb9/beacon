"""Ground Truth Recovery (Alpha+) — stop features; improve email confidence."""

from ground_truth.acceptance.engine import GtAcceptanceEngine
from ground_truth.contact_waterfall_v2.engine import WATERFALL_V2, ContactWaterfallV2Engine
from ground_truth.daily_report.engine import DailyImprovementReportEngine
from ground_truth.founder_queue.engine import TOP_N, GtFounderQueueEngine
from ground_truth.intelligence_card.engine import IntelligenceCardBuilder
from ground_truth.models.types import (
    AttributedField,
    CompanyTimeline,
    CompanyTruthProfile,
    ContactWaterfallV2Result,
    DailyImprovementReport,
    FounderQueueItem,
    GtAcceptance,
    GtSnapshot,
    GtVerdict,
    IntelligenceCard,
    ProductionLockResult,
    QualityFunnel,
    RejectionReason,
    RejectionRecord,
    TimelineEvent,
    TruthQuestions,
    UNKNOWN,
)
from ground_truth.pipelines.engine import GroundTruthPipeline
from ground_truth.production_lock.engine import ProductionLockEngine
from ground_truth.quality_funnel.engine import QualityFunnelEngine
from ground_truth.rejection.engine import RejectionEngine
from ground_truth.timeline.engine import CompanyTimelineEngine
from ground_truth.truth_engine.engine import QUESTIONS, CompanyTruthEngine

__all__ = [
    "TOP_N",
    "WATERFALL_V2",
    "QUESTIONS",
    "AttributedField",
    "CompanyTimeline",
    "CompanyTimelineEngine",
    "CompanyTruthEngine",
    "CompanyTruthProfile",
    "ContactWaterfallV2Engine",
    "ContactWaterfallV2Result",
    "DailyImprovementReport",
    "DailyImprovementReportEngine",
    "FounderQueueItem",
    "GroundTruthPipeline",
    "GtAcceptance",
    "GtAcceptanceEngine",
    "GtFounderQueueEngine",
    "GtSnapshot",
    "GtVerdict",
    "IntelligenceCard",
    "IntelligenceCardBuilder",
    "ProductionLockEngine",
    "ProductionLockResult",
    "QualityFunnel",
    "QualityFunnelEngine",
    "RejectionEngine",
    "RejectionReason",
    "RejectionRecord",
    "TimelineEvent",
    "TruthQuestions",
    "UNKNOWN",
]

SCORING_VERSION = "alpha-plus-v1"
LIVE_OUTREACH_ENABLED = False
PRODUCTION_SEND_LOCKED = True
