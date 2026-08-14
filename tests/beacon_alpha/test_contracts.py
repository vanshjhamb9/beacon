"""Beacon Alpha contracts."""

from __future__ import annotations

from pathlib import Path

from beacon_alpha import LIVE_OUTREACH_ENABLED, SCORING_VERSION
from beacon_alpha.pipelines.engine import BeaconAlphaPipeline
from runtime_ops.migrations.catalog import HEAD_REVISION, PENDING_CHAIN, REQUIRED_TABLES


def test_version():
    assert SCORING_VERSION == "alpha-v1"
    assert LIVE_OUTREACH_ENABLED is False


def test_migration_file():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "api" / "alembic" / "versions" / "20260724_0034_create_beacon_alpha_tables.py"
    text = path.read_text(encoding="utf-8")
    for table in ("alpha_snapshots", "alpha_qa_decisions", "alpha_acceptance_gates", "alpha_founder_queue"):
        assert table in text
    assert "20260724_0033" in text
    assert HEAD_REVISION == "20260724_0039"
    assert "20260724_0034" in PENDING_CHAIN
    for table in ("alpha_snapshots", "alpha_qa_decisions", "alpha_acceptance_gates", "alpha_founder_queue"):
        assert table in REQUIRED_TABLES


def test_api_route_prefix():
    from app.api.routes import beacon_alpha as mod

    assert mod.router.prefix == "/beacon-alpha"


def test_models_importable():
    from app.models.beacon_alpha import AlphaAcceptanceRow, AlphaFounderQueueRow, AlphaQaDecisionRow, AlphaSnapshotRow

    assert AlphaSnapshotRow.__tablename__ == "alpha_snapshots"
    assert AlphaQaDecisionRow.__tablename__ == "alpha_qa_decisions"
    assert AlphaAcceptanceRow.__tablename__ == "alpha_acceptance_gates"
    assert AlphaFounderQueueRow.__tablename__ == "alpha_founder_queue"


def test_worker_task():
    from worker.beacon_alpha_tasks import process_beacon_alpha

    assert process_beacon_alpha.name == "beacon_alpha.process_pending"


def test_celery_includes():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "worker" / "worker" / "celery_app.py").read_text(encoding="utf-8")
    assert "worker.beacon_alpha_tasks" in text
    assert "beacon_alpha.process_pending" in text


def test_dashboard_exists():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "dashboard" / "features" / "beacon-alpha" / "beacon-alpha-workspace.tsx"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Founder Queue" in text
    assert "Manual QA" in text


def test_page_and_sidebar():
    root = Path(__file__).resolve().parents[2]
    assert (root / "apps" / "dashboard" / "app" / "(workspace)" / "beacon-alpha" / "page.tsx").exists()
    sidebar = (root / "apps" / "dashboard" / "components" / "layout" / "sidebar.tsx").read_text(encoding="utf-8")
    assert "/beacon-alpha" in sidebar


def test_beacon_api_hooks():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "dashboard" / "lib" / "api" / "beacon.ts").read_text(encoding="utf-8")
    for name in ("alphaFounderQueue", "alphaQaPending", "alphaQaDecide", "alphaAcceptance"):
        assert name in text


def test_regression_prior_packages():
    from revenue_data_recovery import SCORING_VERSION as RDI
    from revenue_quality_recovery import SCORING_VERSION as RQP

    assert RDI == "rdi-v1"
    assert RQP == "rqp-v1"


def test_service_importable():
    from app.services.beacon_alpha import BeaconAlphaService

    assert BeaconAlphaService is not None


def test_routes_registered():
    from app.api.routes import router

    paths = {getattr(r, "path", "") for r in router.routes}
    assert any("/beacon-alpha" in p for p in paths)


def test_e2e_outbound_card():
    snap = BeaconAlphaPipeline().evaluate(
        {
            "company_id": "e2e",
            "company_name": "Northwind Logistics",
            "legal_name": "Northwind Logistics Inc",
            "website": "northwind.com",
            "domain": "northwind.com",
            "industry": "Logistics",
            "country": "US",
            "business_description": "Freight SaaS automating manual dispatch workflows with AI agents and internal tools",
            "narrative": "Hiring ops; automating repetitive manual workflows with OpenAI agents",
            "source": "goap",
            "collector": "goap",
            "collected_from": "goap",
            "original_url": "https://example.com/job",
            "original_post_title": "Ops automation hire",
            "evidence": [{"summary": "hiring + automation agents openai", "url": "https://example.com/job"}],
            "signals": ["hiring", "automation", "openai", "workflows", "agents", "manual work"],
            "opportunity": "AI automation for dispatch ops",
            "decision_makers": [
                {"name": "Sam", "role": "CEO", "email": "sam@northwind.com", "source": "dd", "confidence": 90}
            ],
            "emails": ["sam@northwind.com"],
            "linkedin_company": "https://linkedin.com/company/northwind",
            "website_alive": True,
            "ssl": True,
            "entity_type": "saas",
        }
    )
    assert snap.verdict.value in {"SALES_READY", "REJECTED"}
    if snap.verdict.value == "SALES_READY":
        assert snap.founder_card is not None
        assert snap.score.total >= 80
