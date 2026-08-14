"""EROWD v1 contracts."""

from __future__ import annotations

from pathlib import Path

from entity_resolution import COMPANY_REQUIRES_OFFICIAL_WEBSITE, LIVE_OUTREACH_ENABLED, SCORING_VERSION
from entity_resolution.pipelines.engine import ErowdPipeline
from runtime_ops.migrations.catalog import HEAD_REVISION, PENDING_CHAIN, REQUIRED_TABLES

TABLES = (
    "entity_resolution_runs",
    "entity_candidates",
    "official_websites",
    "website_attributions",
    "identity_scores",
    "canonical_entities",
    "website_validation",
    "entity_aliases",
)


def test_version():
    assert SCORING_VERSION == "erowd-v1"
    assert LIVE_OUTREACH_ENABLED is False
    assert COMPANY_REQUIRES_OFFICIAL_WEBSITE is True


def test_migration():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "api" / "alembic" / "versions" / "20260724_0037_create_erowd_tables.py"
    text = path.read_text(encoding="utf-8")
    for table in TABLES:
        assert table in text
        assert table in REQUIRED_TABLES
    assert "20260724_0036" in text
    assert HEAD_REVISION == "20260724_0039"
    assert "20260724_0037" in PENDING_CHAIN


def test_api_prefix():
    from app.api.routes import entity_resolution as mod

    assert mod.router.prefix == "/entity-resolution"


def test_models():
    from app.models.entity_resolution_erowd import (
        CanonicalEntityRow,
        EntityAliasRow,
        EntityCandidateRow,
        EntityResolutionRunRow,
        IdentityScoreRow,
        OfficialWebsiteRow,
        WebsiteAttributionRow,
        WebsiteValidationRow,
    )

    assert EntityResolutionRunRow.__tablename__ == "entity_resolution_runs"
    assert EntityCandidateRow.__tablename__ == "entity_candidates"
    assert OfficialWebsiteRow.__tablename__ == "official_websites"
    assert WebsiteAttributionRow.__tablename__ == "website_attributions"
    assert IdentityScoreRow.__tablename__ == "identity_scores"
    assert CanonicalEntityRow.__tablename__ == "canonical_entities"
    assert WebsiteValidationRow.__tablename__ == "website_validation"
    assert EntityAliasRow.__tablename__ == "entity_aliases"


def test_worker():
    from worker.entity_resolution_tasks import rebuild_entities

    assert rebuild_entities.name == "entity_resolution.rebuild"


def test_celery():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "worker" / "worker" / "celery_app.py").read_text(encoding="utf-8")
    assert "worker.entity_resolution_tasks" in text


def test_intelligence_intercept():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "api" / "app" / "services" / "intelligence.py").read_text(encoding="utf-8")
    assert "ErowdPipeline" in text
    assert "erowd_rejected" in text
    assert "persist_run" in text


def test_routes():
    from app.api.routes import router

    paths = [getattr(r, "path", "") for r in router.routes]
    assert any("/entity-resolution" in p for p in paths)
    for suffix in ("/search", "/evaluate", "/rebuild", "/report", "/dashboard"):
        assert any(suffix in p for p in paths)


def test_ui():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "dashboard" / "features" / "entity-resolution" / "entity-resolution-workspace.tsx"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Official Website" in text
    assert "Entity Resolution" in (root / "apps" / "dashboard" / "components" / "layout" / "sidebar.tsx").read_text(
        encoding="utf-8"
    )
    company = (root / "apps" / "dashboard" / "features" / "companies" / "company-workspace.tsx").read_text(encoding="utf-8")
    assert "erowdCompany" in company or "company-erowd" in company
    assert "Official Website" in company


def test_api_hooks():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "dashboard" / "lib" / "api" / "beacon.ts").read_text(encoding="utf-8")
    for name in ("erowdDashboard", "erowdReport", "erowdSearch", "erowdCompany", "erowdEvaluate", "erowdRebuild"):
        assert name in text


def test_product_hunt_never_uses_listing_as_identity():
    root = Path(__file__).resolve().parents[2]
    text = (root / "packages" / "collectors" / "sources" / "product_hunt.py").read_text(encoding="utf-8")
    assert "OfficialWebsiteDiscoveryEngine" in text
    assert "official_website" in text


def test_github_captures_repo_homepage():
    root = Path(__file__).resolve().parents[2]
    text = (root / "packages" / "collectors" / "sources" / "github_trending.py").read_text(encoding="utf-8")
    assert "repo_homepage" in text
    assert "homepage" in text


def test_rss_rejects_article_only():
    root = Path(__file__).resolve().parents[2]
    text = (root / "packages" / "collectors" / "rss_parser.py").read_text(encoding="utf-8")
    assert "article_only" in text
    assert "organization_website" in text or "canonical_website" in text


def test_e2e_admit_reject():
    pipe = ErowdPipeline()
    good = pipe.evaluate(
        {
            "signal_id": "e2e",
            "title": "PromptQL — natural language to SQL",
            "body": "PromptQL turns natural language into trusted analytics SQL for enterprise teams.",
            "url": "https://www.producthunt.com/posts/promptql",
            "source": "product_hunt",
            "metadata": {"company_hints": ["PromptQL"], "official_website": "https://promptql.ai"},
            "official_website": "https://promptql.ai",
            "website_verified": True,
            "website_title": "PromptQL",
            "industry": "Software",
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
    assert good.identity.domain == "promptql.ai"
    assert good.identity.official_website
    assert "producthunt.com" not in (good.identity.domain or "")
    assert not bad.admission.allow_create_company
