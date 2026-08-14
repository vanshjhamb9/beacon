"""Beacon Observatory & Live Collector Runtime (BOLR v1) — Sprint 38.5.

Beacon becomes its own observability platform.

Architecture:
    Internet → Collectors → Collector Runtime Monitor → OCP → DQE → LOVP
                                    ↓
                            Beacon Observatory
                                    ↓
                            Founder Workspace

BOLR_VERSION = "bolr-v1"
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any


class CollectorStatus(str, Enum):
    RUNNING = "running"
    IDLE = "idle"
    WAITING = "waiting"
    FAILED = "failed"
    DISABLED = "disabled"


class PipelineStage(str, Enum):
    COLLECTED = "collected"
    NORMALIZED = "normalized"
    VALIDATED = "validated"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    REVENUE_READY = "revenue_ready"
    INBOX = "inbox"
    PIPELINE = "pipeline"
    CONTACTED = "contacted"
    MEETING = "meeting"
    PROPOSAL = "proposal"
    WON = "won"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class DataType(str, Enum):
    LIVE = "live"
    CACHED = "cached"
    UNKNOWN = "unknown"


REJECTION_CATEGORIES = {
    "old_signal": "Signal older than threshold",
    "ai_company": "AI/LLM company detected",
    "duplicate": "Duplicate company detected",
    "low_trust": "Low trust source",
    "bad_website": "Website validation failed",
    "no_buying_signal": "No valid buying signal",
    "icp_mismatch": "Not in Ideal Customer Profile",
    "low_quality": "Quality score below threshold",
    "competitor": "Known competitor",
    "parked_domain": "Parked domain detected",
}

DEMO_KEYWORDS = [
    "techflow", "cloudfirst", "growthedge", "demo", "sample",
    "placeholder", "lorem", "example", "test", "mock",
]

BOLR_VERSION = "bolr-v1"

from .runtime_engine import RuntimeEngine, CollectorRuntimeInfo
from .collector_runtime import CollectorRuntime
from .scheduler_monitor import SchedulerMonitor
from .worker_runtime import WorkerRuntime
from .event_stream import EventStream
from .pipeline_trace import PipelineTrace
from .evidence_explorer import EvidenceExplorer
from .rejection_explorer import RejectionExplorer
from .connector_runtime import ConnectorRuntime
from .runtime_metrics import RuntimeMetrics
from .latency_engine import LatencyEngine
from .bottleneck_engine import BottleneckEngine
from .replay_engine import ReplayEngine
from .timeline_engine import TimelineEngine
from .verification_engine import VerificationEngine
from .dashboard_service import DashboardService
from .reports import Reports
from .alerts import Alerting
