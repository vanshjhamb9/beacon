"""Runtime operations hardening — compose-only infrastructure recovery (sprint 27.5)."""

from runtime_ops.models.types import (
    AlertSeverity,
    OperationalAlert,
    ProductionGateDecision,
    RuntimeOpsSnapshot,
)
from runtime_ops.production.gate import ProductionGate
from runtime_ops.redis.validator import RedisStreamsValidator
from runtime_ops.reports.builder import RuntimeOpsReportBuilder

__all__ = [
    "AlertSeverity",
    "OperationalAlert",
    "ProductionGate",
    "ProductionGateDecision",
    "RedisStreamsValidator",
    "RuntimeOpsReportBuilder",
    "RuntimeOpsSnapshot",
]

SCORING_VERSION = "runtime-ops-v1"
REQUIRED_ALEMBIC_HEAD = "20260724_0031"
MIN_REDIS_MAJOR = 7
