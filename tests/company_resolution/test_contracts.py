"""CRE v1 contracts."""

from __future__ import annotations

from pathlib import Path

from company_resolution import COMPANY_CREATE_REQUIRES_CRE, SCORING_VERSION
from company_resolution.pipelines.engine import CompanyResolutionPipeline
from runtime_ops.migrations.catalog import HEAD_REVISION, PENDING_CHAIN, REQUIRED_TABLES


def test_version():
    assert SCORING_VERSION == "cre-v1"
    assert COMPANY_CREATE_REQUIRES_CRE is True


def test_migration():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "api" / "alembic" / "versions" / "20260724_0036_create_company_resolution_tables.py"
    text = path.read_text(encoding="utf-8")
    for table in ("cre_snapshots", "cre_admission_decisions", "cre_rebuild_reports"):
        assert table in text
        assert table in REQUIRED_TABLES
    assert "20260724_0035" in text
    assert HEAD_REVISION == "20260724_0039"
    assert "20260724_0036" in PENDING_CHAIN
    assert "20260724_0037" in PENDING_CHAIN


def test_api_prefix():
    from app.api.routes import company_resolution as mod

    assert mod.router.prefix == "/company-resolution"


def test_models():
    from app.models.company_resolution import CreAdmissionDecisionRow, CreRebuildReportRow, CreSnapshotRow

    assert CreSnapshotRow.__tablename__ == "cre_snapshots"
    assert CreAdmissionDecisionRow.__tablename__ == "cre_admission_decisions"
    assert CreRebuildReportRow.__tablename__ == "cre_rebuild_reports"


def test_worker():
    from worker.company_resolution_tasks import rebuild_companies

    assert rebuild_companies.name == "company_resolution.rebuild"


def test_celery():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "worker" / "worker" / "celery_app.py").read_text(encoding="utf-8")
    assert "worker.company_resolution_tasks" in text


def test_intelligence_intercept():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "api" / "app" / "services" / "intelligence.py").read_text(encoding="utf-8")
    assert "CompanyResolutionPipeline" in text
    assert "CRE soft-bypass" in text or "cre_rejected" in text
    assert "ErowdPipeline" in text
    assert "erowd_rejected" in text

def test_routes():
    from app.api.routes import router

    assert any("/company-resolution" in getattr(r, "path", "") for r in router.routes)


def test_e2e_admit_reject():
    pipe = CompanyResolutionPipeline()
    good = pipe.evaluate(
        {
            "signal_id": "e2e",
            "title": "Helios — clinic AI automation",
            "body": "Helios Health automates clinic operations with AI agents for enterprise hospitals and support teams.",
            "url": "https://www.producthunt.com/posts/helios",
            "source": "product_hunt",
            "metadata": {"domain": "helios.health", "company_hints": ["Helios"]},
            "domains": ["helios.health"],
            "website_alive": True,
            "http_status": 200,
            "industry": "Healthcare",
            "description": "AI clinic operations platform",
            "country": "US",
        }
    )
    bad = pipe.evaluate(
        {
            "signal_id": "e2e-bad",
            "title": "Kubernetes tips",
            "body": "notes",
            "url": "https://news.ycombinator.com/item?id=2",
            "source": "hacker_news",
        }
    )
    assert good.admission.allow_create_company
    assert not bad.admission.allow_create_company
