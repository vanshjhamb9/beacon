"""Revenue Execution Validation (rev-v1) — prove Beacon produces Revenue Ready companies.

Compose-only. No new intelligence engines. No AI. Production locked until hard gates pass.
North star: companies Vansh can confidently contact within 60 seconds.
"""

from revenue_execution_validation.acceptance.engine import AcceptanceGateEngine
from revenue_execution_validation.connector_scoreboard.engine import ConnectorScoreboardEngine
from revenue_execution_validation.daily_report.engine import DailyRevenueReportEngine
from revenue_execution_validation.founder_queue_v3.engine import FounderQueueV3Engine
from revenue_execution_validation.funnel.engine import RealityFunnelEngine
from revenue_execution_validation.manual_qa.engine import ManualQaWorkspaceEngine
from revenue_execution_validation.models.types import (
    UNKNOWN,
    AcceptanceGateResult,
    ConnectorGrade,
    ConnectorScore,
    DailyRevenueReport,
    FounderQueueCardV3,
    FunnelStage,
    ManualQaRating,
    RealityFunnel,
    RejectionReason,
    RevenueReadyCheck,
    RevSnapshot,
)
from revenue_execution_validation.pipelines.engine import RevenueExecutionPipeline
from revenue_execution_validation.rebuild.engine import RevRebuildEngine
from revenue_execution_validation.rejection.engine import RejectionAnalysisEngine
from revenue_execution_validation.revenue_ready.engine import RevenueReadyDefinitionEngine

SCORING_VERSION = "rev-v1"
LIVE_OUTREACH_ENABLED = False
PRODUCTION_SEND_LOCKED = True
GMAIL_PRODUCTION_ENABLED = False
WHATSAPP_PRODUCTION_ENABLED = False
CAMPAIGN_EXECUTION_ENABLED = False

__all__ = [
    "UNKNOWN",
    "AcceptanceGateEngine",
    "AcceptanceGateResult",
    "CAMPAIGN_EXECUTION_ENABLED",
    "ConnectorGrade",
    "ConnectorScore",
    "ConnectorScoreboardEngine",
    "DailyRevenueReport",
    "DailyRevenueReportEngine",
    "FounderQueueCardV3",
    "FounderQueueV3Engine",
    "FunnelStage",
    "GMAIL_PRODUCTION_ENABLED",
    "LIVE_OUTREACH_ENABLED",
    "ManualQaRating",
    "ManualQaWorkspaceEngine",
    "PRODUCTION_SEND_LOCKED",
    "RealityFunnel",
    "RealityFunnelEngine",
    "RejectionAnalysisEngine",
    "RejectionReason",
    "RevenueExecutionPipeline",
    "RevenueReadyCheck",
    "RevenueReadyDefinitionEngine",
    "RevRebuildEngine",
    "RevSnapshot",
    "SCORING_VERSION",
    "WHATSAPP_PRODUCTION_ENABLED",
]
