"""CIR v1 contracts."""

from __future__ import annotations

from pathlib import Path

from company_intelligence import FOUNDER_QUEUE_CLASSIFICATIONS, REQUIRES_EROWD_ADMITTED, SCORING_VERSION
from company_intelligence.models.types import CirClassification
from company_intelligence.pipelines.engine import CirPipeline
from runtime_ops.migrations.catalog import HEAD_REVISION, PENDING_CHAIN, REQUIRED_TABLES

TABLES = (
    "cir_company_profiles",
    "cir_business_profiles",
    "cir_product_profiles",
    "cir_technology_profiles",
    "cir_buying_signals",
    "cir_service_matches",
    "cir_revenue_readiness",
    "cir_opportunity_narratives",
)


def test_version():
    assert SCORING_VERSION == "cir-v1"
    assert REQUIRES_EROWD_ADMITTED is True
    assert CirClassification.REVENUE_READY in FOUNDER_QUEUE_CLASSIFICATIONS
    assert CirClassification.PRIORITY_ACCOUNT in FOUNDER_QUEUE_CLASSIFICATIONS


def test_migration():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "api" / "alembic" / "versions" / "20260724_0038_create_cir_tables.py"
    text = path.read_text(encoding="utf-8")
    for table in TABLES:
        assert table in text
        assert table in REQUIRED_TABLES
    assert "20260724_0037" in text
    assert HEAD_REVISION == "20260724_0039"
    assert "20260724_0038" in PENDING_CHAIN


def test_api_prefix():
    from app.api.routes import company_intelligence as mod

    assert mod.router.prefix == "/company-intelligence"


def test_models():
    from app.models.company_intelligence import (
        CirBusinessProfileRow,
        CirBuyingSignalRow,
        CirCompanyProfileRow,
        CirOpportunityNarrativeRow,
        CirProductProfileRow,
        CirRevenueReadinessRow,
        CirServiceMatchRow,
        CirTechnologyProfileRow,
    )

    assert CirCompanyProfileRow.__tablename__ == "cir_company_profiles"
    assert CirBusinessProfileRow.__tablename__ == "cir_business_profiles"
    assert CirProductProfileRow.__tablename__ == "cir_product_profiles"
    assert CirTechnologyProfileRow.__tablename__ == "cir_technology_profiles"
    assert CirBuyingSignalRow.__tablename__ == "cir_buying_signals"
    assert CirServiceMatchRow.__tablename__ == "cir_service_matches"
    assert CirRevenueReadinessRow.__tablename__ == "cir_revenue_readiness"
    assert CirOpportunityNarrativeRow.__tablename__ == "cir_opportunity_narratives"


def test_worker():
    from worker.company_intelligence_tasks import process_verified, rebuild_intelligence

    assert process_verified.name == "company_intelligence.process_verified"
    assert rebuild_intelligence.name == "company_intelligence.rebuild"


def test_celery_beat():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "worker" / "worker" / "celery_app.py").read_text(encoding="utf-8")
    assert "worker.company_intelligence_tasks" in text
    assert "company_intelligence.process_verified" in text
    assert '"schedule": 120' in text or "'schedule': 120" in text


def test_routes():
    from app.api.routes import router

    paths = [getattr(r, "path", "") for r in router.routes]
    assert any("/company-intelligence" in p for p in paths)
    for suffix in ("/dashboard", "/rebuild", "/search", "/opportunities", "/summary"):
        assert any(suffix in p for p in paths)


def test_ui():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "dashboard" / "features" / "company-intelligence" / "company-intelligence-workspace.tsx"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Revenue Readiness" in text
    assert "Company Intelligence" in (root / "apps" / "dashboard" / "components" / "layout" / "sidebar.tsx").read_text(
        encoding="utf-8"
    )
    company = (root / "apps" / "dashboard" / "features" / "companies" / "company-workspace.tsx").read_text(encoding="utf-8")
    assert "CirExecutiveSummary" in company


def test_api_hooks():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "dashboard" / "lib" / "api" / "beacon.ts").read_text(encoding="utf-8")
    for name in ("cirDashboard", "cirSummary", "cirCompany", "cirOpportunities", "cirRebuild"):
        assert name in text


def test_rh_compose():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "api" / "app" / "repositories" / "revenue_hunter.py").read_text(encoding="utf-8")
    assert "cir_narrative" in text
    assert "cir_technologies" in text


def test_skips_without_erowd():
    snap = CirPipeline().evaluate(
        {
            "company_id": "x",
            "company_name": "NoAdmit Co",
            "website": "https://noadmit.com",
            "erowd_admitted": False,
        }
    )
    assert snap.verdict.value == "SKIPPED"
    assert not snap.founder_queue_eligible


def test_e2e_reconstruct():
    snap = CirPipeline().evaluate(_rich("Urban Webworks Client"))
    assert snap.verdict.value in {"RECONSTRUCTED", "PARTIAL"}
    assert snap.business.industry.value != "UNKNOWN"
    assert snap.readiness.evidence
    assert snap.founder_card.company != "UNKNOWN"


def _rich(name: str) -> dict:
    return {
        "company_id": "c1",
        "company_name": name,
        "website": "https://acme-ops.com",
        "domain": "acme-ops.com",
        "official_website": "https://acme-ops.com",
        "erowd_admitted": True,
        "erowd_verified": True,
        "industry": "Software",
        "country": "United States",
        "employees": "120",
        "description": "Acme Ops is a SaaS automation platform for enterprise teams.",
        "website_pages": [
            {
                "url": "https://acme-ops.com",
                "path": "/",
                "title": "Acme Ops — AI automation for enterprise",
                "description": "Automate workflows with AI agents for mid-market and enterprise buyers.",
                "headings": ["AI automation platform", "Built for enterprise operations"],
                "text": (
                    "Acme Ops helps enterprises automate support and ops with AI agents. "
                    "Integrates with Salesforce HubSpot Slack Stripe. SOC 2 and GDPR. "
                    "We're hiring AI engineers. Enterprise plan available. Public API and docs. "
                    "Trusted by growing companies. Based in San Francisco United States. "
                    "Founded in 2019. 120 employees. OpenAI powered workflows."
                ),
            },
            {
                "url": "https://acme-ops.com/pricing",
                "path": "/pricing",
                "title": "Pricing",
                "headings": ["Starter", "Pro", "Enterprise"],
                "text": "Free trial available. New pricing for enterprise launch.",
            },
            {
                "url": "https://acme-ops.com/team",
                "path": "/team",
                "title": "Team",
                "headings": ["Leadership"],
                "text": "Ada Lovelace, CEO. Grace Hopper, CTO. Contact hello@acme-ops.com",
            },
            {
                "url": "https://acme-ops.com/careers",
                "path": "/careers",
                "title": "Careers",
                "text": "Now hiring software engineers and AI engineers. Scaling globally.",
            },
        ],
        "technologies": ["React", "AWS"],
        "decision_makers": [{"name": "Ada Lovelace", "role": "CEO", "email": "ada@acme-ops.com", "confidence": 90}],
    }
