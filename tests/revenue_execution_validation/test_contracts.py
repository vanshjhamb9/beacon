"""rev-v1 contracts."""

from __future__ import annotations

from pathlib import Path

from revenue_execution_validation import (
    CAMPAIGN_EXECUTION_ENABLED,
    GMAIL_PRODUCTION_ENABLED,
    LIVE_OUTREACH_ENABLED,
    PRODUCTION_SEND_LOCKED,
    SCORING_VERSION,
    WHATSAPP_PRODUCTION_ENABLED,
)
from revenue_execution_validation.pipelines.engine import RevenueExecutionPipeline
from runtime_ops.migrations.catalog import HEAD_REVISION, PENDING_CHAIN, REQUIRED_TABLES

TABLES = (
    "rev_evaluations",
    "rev_rejection_records",
    "rev_funnel_snapshots",
    "rev_connector_scores",
    "rev_founder_queue_cards",
    "rev_manual_qa",
    "rev_daily_reports",
    "rev_acceptance_gates",
)


def test_version_and_locks():
    assert SCORING_VERSION == "rev-v1"
    assert LIVE_OUTREACH_ENABLED is False
    assert PRODUCTION_SEND_LOCKED is True
    assert GMAIL_PRODUCTION_ENABLED is False
    assert WHATSAPP_PRODUCTION_ENABLED is False
    assert CAMPAIGN_EXECUTION_ENABLED is False


def test_migration():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "api" / "alembic" / "versions" / "20260724_0039_create_rev_execution_tables.py"
    text = path.read_text(encoding="utf-8")
    for table in TABLES:
        assert table in text
        assert table in REQUIRED_TABLES
    assert "20260724_0038" in text
    assert HEAD_REVISION == "20260724_0039"
    assert "20260724_0039" in PENDING_CHAIN


def test_api_prefix():
    from app.api.routes import revenue_execution_validation as mod

    assert mod.router.prefix == "/revenue-execution-validation"


def test_models():
    from app.models.revenue_execution_validation import (
        RevAcceptanceGateRow,
        RevConnectorScoreRow,
        RevDailyReportRow,
        RevEvaluationRow,
        RevFounderQueueCardRow,
        RevFunnelSnapshotRow,
        RevManualQaRow,
        RevRejectionRecordRow,
    )

    assert RevEvaluationRow.__tablename__ == "rev_evaluations"
    assert RevRejectionRecordRow.__tablename__ == "rev_rejection_records"
    assert RevFunnelSnapshotRow.__tablename__ == "rev_funnel_snapshots"
    assert RevConnectorScoreRow.__tablename__ == "rev_connector_scores"
    assert RevFounderQueueCardRow.__tablename__ == "rev_founder_queue_cards"
    assert RevManualQaRow.__tablename__ == "rev_manual_qa"
    assert RevDailyReportRow.__tablename__ == "rev_daily_reports"
    assert RevAcceptanceGateRow.__tablename__ == "rev_acceptance_gates"


def test_worker():
    from worker.revenue_execution_validation_tasks import daily_revenue_execution_report, rebuild_revenue_execution

    assert rebuild_revenue_execution.name == "revenue_execution_validation.rebuild"
    assert daily_revenue_execution_report.name == "revenue_execution_validation.daily_report"


def test_celery():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "worker" / "worker" / "celery_app.py").read_text(encoding="utf-8")
    assert "worker.revenue_execution_validation_tasks" in text
    assert "revenue_execution_validation.daily_report" in text


def test_routes():
    from app.api.routes import router

    paths = [getattr(r, "path", "") for r in router.routes]
    assert any("/revenue-execution-validation" in p for p in paths)


def test_ui():
    root = Path(__file__).resolve().parents[2]
    assert (root / "apps" / "dashboard" / "features" / "revenue-execution" / "revenue-execution-workspace.tsx").exists()
    assert (root / "apps" / "dashboard" / "features" / "revenue-execution" / "founder-queue-v3-workspace.tsx").exists()
    sidebar = (root / "apps" / "dashboard" / "components" / "layout" / "sidebar.tsx").read_text(encoding="utf-8")
    assert "/revenue-execution" in sidebar
    assert "/founder-queue-v3" in sidebar


def test_api_hooks():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "dashboard" / "lib" / "api" / "beacon.ts").read_text(encoding="utf-8")
    for name in ("revDashboard", "revFounderQueue", "revQaPending", "revAcceptance", "revDailyReport"):
        assert name in text


def test_e2e_ready_and_reject():
    pipe = RevenueExecutionPipeline()
    good = pipe.evaluate(_ready("Acme Ops"))
    bad = pipe.evaluate(
        {
            "company_id": "b1",
            "company_name": "Noise",
            "source": "hacker_news",
            "url": "https://news.ycombinator.com/item?id=1",
        }
    )
    assert good.check.is_revenue_ready
    assert good.check.business_email
    assert not bad.check.is_revenue_ready
    assert bad.check.rejection_reasons


def _ready(name: str) -> dict:
    return {
        "company_id": "a1",
        "company_name": name,
        "website": "https://acme-ops.com",
        "official_website": "https://acme-ops.com",
        "domain": "acme-ops.com",
        "country": "United States",
        "industry": "Software",
        "description": "Enterprise SaaS automation platform for operations teams",
        "erowd_admitted": True,
        "erowd_verified": True,
        "website_verified": True,
        "source": "product_hunt",
        "buying_signals": ["Hiring", "Product Launch", "Scaling"],
        "best_service": "AI Automation",
        "service_matches": [{"service": "AI Automation", "evidence": ["automation"]}],
        "business_email": "hello@acme-ops.com",
        "decision_maker": "Ada Lovelace (CEO)",
        "why_now": "Hiring AI engineers while launching enterprise plan",
        "opportunity": "Deliver AI Automation for ops workflows",
        "confidence": 88,
        "evidence": ["ph_launch", "hiring"],
        "cir_classification": "Revenue Ready",
    }
