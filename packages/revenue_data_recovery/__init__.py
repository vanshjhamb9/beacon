"""Revenue Data Recovery & Intelligence (RDI v1) — evidence → revenue."""

from revenue_data_recovery.contact_recovery.engine import ContactRecoveryEngine
from revenue_data_recovery.daily_worker.engine import DailyRecoveryWorker
from revenue_data_recovery.dossier.engine import RevenueDossierBuilder
from revenue_data_recovery.recovery_queue.engine import RecoveryQueueEngine
from revenue_data_recovery.fake_elimination.engine import FakeCompanyEliminationEngine
from revenue_data_recovery.identity_recovery.engine import IdentityRecoveryEngine
from revenue_data_recovery.intent_intelligence.engine import IntentIntelligenceEngine, INTENT_WEIGHTS
from revenue_data_recovery.metrics.engine import RecoveryMetricsEngine
from revenue_data_recovery.models.types import (
    AttributedValue,
    ContactRecoveryResult,
    DailyRecoveryReport,
    FakeEliminationResult,
    IdentityRecoveryResult,
    IntentIntelligenceResult,
    OpportunityValidationResult,
    QualityGateResult,
    RecoveredContact,
    RecoveryMetrics,
    RecoveryQueueItem,
    RecoveryStage,
    RevenueDossier,
    RevenueRecommendationResult,
    RdiSnapshot,
    SalesReadyStatus,
    ServiceRecommendation,
    WebsiteRecoveryResult,
    UNKNOWN,
)
from revenue_data_recovery.opportunity_validation.engine import OpportunityValidationEngine
from revenue_data_recovery.pipelines.engine import RevenueDataRecoveryPipeline
from revenue_data_recovery.quality_gates.engine import QualityGateEngine
from revenue_data_recovery.revenue_recommendation.engine import RevenueRecommendationEngine
from revenue_data_recovery.website_recovery.engine import WebsiteRecoveryEngine

__all__ = [
    "AttributedValue",
    "ContactRecoveryEngine",
    "ContactRecoveryResult",
    "DailyRecoveryReport",
    "DailyRecoveryWorker",
    "FakeCompanyEliminationEngine",
    "FakeEliminationResult",
    "INTENT_WEIGHTS",
    "IdentityRecoveryEngine",
    "IdentityRecoveryResult",
    "IntentIntelligenceEngine",
    "IntentIntelligenceResult",
    "OpportunityValidationEngine",
    "OpportunityValidationResult",
    "QualityGateEngine",
    "QualityGateResult",
    "RecoveredContact",
    "RecoveryMetrics",
    "RecoveryMetricsEngine",
    "RecoveryQueueEngine",
    "RecoveryQueueItem",
    "RecoveryStage",
    "RevenueDataRecoveryPipeline",
    "RevenueDossier",
    "RevenueDossierBuilder",
    "RevenueRecommendationEngine",
    "RevenueRecommendationResult",
    "RdiSnapshot",
    "SalesReadyStatus",
    "ServiceRecommendation",
    "WebsiteRecoveryEngine",
    "WebsiteRecoveryResult",
    "UNKNOWN",
]

SCORING_VERSION = "rdi-v1"
INTENT_THRESHOLD = 25.0
TRUST_THRESHOLD = 55.0
