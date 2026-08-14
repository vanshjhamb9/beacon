"""Ground Truth Alpha+ contracts."""

from __future__ import annotations

from pathlib import Path

from ground_truth import LIVE_OUTREACH_ENABLED, PRODUCTION_SEND_LOCKED, SCORING_VERSION
from ground_truth.pipelines.engine import GroundTruthPipeline
from runtime_ops.migrations.catalog import HEAD_REVISION, PENDING_CHAIN, REQUIRED_TABLES


def test_version():
    assert SCORING_VERSION == "alpha-plus-v1"
    assert LIVE_OUTREACH_ENABLED is False
    assert PRODUCTION_SEND_LOCKED is True


def test_migration():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "api" / "alembic" / "versions" / "20260724_0035_create_ground_truth_tables.py"
    text = path.read_text(encoding="utf-8")
    for table in ("gt_snapshots", "gt_daily_reports", "gt_acceptance_gates", "gt_founder_queue"):
        assert table in text
        assert table in REQUIRED_TABLES
    assert "20260724_0034" in text
    assert HEAD_REVISION == "20260724_0039"
    assert "20260724_0035" in PENDING_CHAIN


def test_api_prefix():
    from app.api.routes import ground_truth as mod

    assert mod.router.prefix == "/ground-truth"


def test_models():
    from app.models.ground_truth import GtAcceptanceRow, GtDailyReportRow, GtFounderQueueRow, GtSnapshotRow

    assert GtSnapshotRow.__tablename__ == "gt_snapshots"
    assert GtDailyReportRow.__tablename__ == "gt_daily_reports"
    assert GtAcceptanceRow.__tablename__ == "gt_acceptance_gates"
    assert GtFounderQueueRow.__tablename__ == "gt_founder_queue"


def test_worker():
    from worker.ground_truth_tasks import daily_ground_truth_report, process_ground_truth

    assert process_ground_truth.name == "ground_truth.process_pending"
    assert daily_ground_truth_report.name == "ground_truth.daily_report"


def test_celery():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "worker" / "worker" / "celery_app.py").read_text(encoding="utf-8")
    assert "worker.ground_truth_tasks" in text
    assert "ground_truth.process_pending" in text


def test_ui():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "dashboard" / "features" / "ground-truth" / "ground-truth-workspace.tsx"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Quality funnel" in text
    assert "Founder Queue" in text
    assert "/ground-truth" in (root / "apps" / "dashboard" / "components" / "layout" / "sidebar.tsx").read_text(encoding="utf-8")


def test_api_hooks():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "dashboard" / "lib" / "api" / "beacon.ts").read_text(encoding="utf-8")
    for name in ("gtFounderQueue", "gtFunnel", "gtDailyReport", "gtAcceptance"):
        assert name in text


def test_regression():
    from beacon_alpha import SCORING_VERSION as ALPHA
    from revenue_quality_recovery import SCORING_VERSION as RQP

    assert ALPHA == "alpha-v1"
    assert RQP == "rqp-v1"


def test_service():
    from app.services.ground_truth import GroundTruthService

    assert GroundTruthService is not None


def test_routes():
    from app.api.routes import router

    assert any("/ground-truth" in getattr(r, "path", "") for r in router.routes)


def test_e2e():
    snap = GroundTruthPipeline().evaluate(
        {
            "company_id": "e2e",
            "company_name": "Acme Robotics",
            "website": "acme-robotics.com",
            "domain": "acme-robotics.com",
            "industry": "Robotics",
            "country": "US",
            "employees": 120,
            "description": "Industrial robotics company automating warehouse workflows with AI agents",
            "narrative": "Hiring AI engineers; expanding enterprise automation products",
            "source": "hn",
            "evidence": [{"summary": "Hiring AI engineers", "source": "hn"}],
            "timeline": [{"timestamp": "2026-07-20", "summary": "Hiring AI Engineers", "source": "hn"}],
            "signals": ["hiring ai", "automation", "openai", "enterprise"],
            "decision_makers": [{"name": "Pat", "role": "CTO", "email": "pat@acme-robotics.com", "source": "dd", "confidence": 90}],
            "emails": ["pat@acme-robotics.com"],
            "linkedin_company": "https://linkedin.com/company/acme-robotics",
            "website_alive": True,
            "ssl": True,
            "recommended_service": "Custom AI Automation Platform",
            "estimated_deal": "$42k",
            "why_now": "Hiring AI Engineers; Enterprise Expansion",
            "technologies": ["ROS", "OpenAI"],
            "entity_type": "startup",
        }
    )
    assert snap.questions.all_answered or snap.verdict.value == "REJECTED"
    if snap.production_lock.unlocked:
        assert snap.founder_item is not None
