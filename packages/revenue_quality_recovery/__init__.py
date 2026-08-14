"""Revenue Quality Recovery (RQP v1) — measure revenue, not software."""

from revenue_quality_recovery.acceptance.engine import AcceptanceEngine
from revenue_quality_recovery.company_profile.engine import CompanyProfileBuilder
from revenue_quality_recovery.contact_confidence.engine import ContactConfidenceEngine
from revenue_quality_recovery.contact_waterfall.engine import ContactWaterfallEngine
from revenue_quality_recovery.daily_kpi.engine import DailyKpiEngine
from revenue_quality_recovery.duplicate_recovery.engine import DuplicateRecoveryEngine
from revenue_quality_recovery.evidence_panel.engine import EvidencePanelEngine
from revenue_quality_recovery.golden_dataset.engine import GoldenDatasetEngine
from revenue_quality_recovery.identity_validator.engine import IdentityValidatorEngine
from revenue_quality_recovery.models.types import (
    AcceptanceCriteria,
    AttributedField,
    CompanyProfile,
    ConfidentContact,
    ContactConfidenceResult,
    ContactWaterfallResult,
    DailyKpiReport,
    DuplicateRecoveryResult,
    EvidencePanel,
    GoldenDataset,
    IdentityValidationResult,
    RevenueVerdict,
    RqpSnapshot,
    SalesReadyGateResult,
    SurfaceAdmission,
    SurfaceStatus,
    WebsiteCrawlResult,
    UNKNOWN,
)
from revenue_quality_recovery.pipelines.engine import RevenueQualityPipeline
from revenue_quality_recovery.sales_ready_gate.engine import REQUIRED_FIELDS, SalesReadyGateEngine
from revenue_quality_recovery.surface_readiness.engine import SurfaceReadinessEngine
from revenue_quality_recovery.website_crawler.engine import WebsiteCrawlerEngine

__all__ = [
    "REQUIRED_FIELDS",
    "AcceptanceCriteria",
    "AcceptanceEngine",
    "AttributedField",
    "CompanyProfile",
    "CompanyProfileBuilder",
    "ConfidentContact",
    "ContactConfidenceEngine",
    "ContactConfidenceResult",
    "ContactWaterfallEngine",
    "ContactWaterfallResult",
    "DailyKpiEngine",
    "DailyKpiReport",
    "DuplicateRecoveryEngine",
    "DuplicateRecoveryResult",
    "EvidencePanel",
    "EvidencePanelEngine",
    "GoldenDataset",
    "GoldenDatasetEngine",
    "IdentityValidationResult",
    "IdentityValidatorEngine",
    "RevenueQualityPipeline",
    "RevenueVerdict",
    "RqpSnapshot",
    "SalesReadyGateEngine",
    "SalesReadyGateResult",
    "SurfaceAdmission",
    "SurfaceReadinessEngine",
    "SurfaceStatus",
    "WebsiteCrawlResult",
    "WebsiteCrawlerEngine",
    "UNKNOWN",
]

SCORING_VERSION = "rqp-v1"
GOLDEN_DATASET_SIZE = 500
PRODUCTION_SEND_ENABLED = False  # locked until AcceptanceEngine unlocks
