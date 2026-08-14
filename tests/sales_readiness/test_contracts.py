"""SRE v1 contracts, migration, API, regression, e2e gate tests."""

from __future__ import annotations

from pathlib import Path

from sales_readiness import FOUNDER_QUEUE_STATUSES, REVENUE_HUNTER_STATUSES, SCORING_VERSION
from sales_readiness.models.types import SalesReadinessStatus
from sales_readiness.pipelines.engine import SalesReadinessPipeline
from runtime_ops.migrations.catalog import HEAD_REVISION, REQUIRED_TABLES


def test_version():
    assert SCORING_VERSION == "sre-v1"


def test_migration_file():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "api" / "alembic" / "versions" / "20260724_0031_create_sales_readiness_tables.py"
    text = path.read_text(encoding="utf-8")
    for table in (
        "sales_readiness_snapshots",
        "sales_identity_scores",
        "sales_contact_readiness",
        "sales_intent_scores",
        "sales_service_matches_v2",
        "sales_revenue_potential",
        "sales_trust_scores",
    ):
        assert table in text
    assert "20260724_0030" in text
    assert HEAD_REVISION == "20260724_0039"
    assert "sales_readiness_snapshots" in REQUIRED_TABLES


def test_api_route_prefix():
    from app.api.routes import sales_readiness as mod

    assert mod.router.prefix == "/sales-readiness"


def test_models_importable():
    from app.models.sales_readiness import SalesReadinessSnapshotRow

    assert SalesReadinessSnapshotRow.__tablename__ == "sales_readiness_snapshots"


def test_worker_task_name():
    from worker.sales_readiness_tasks import process_sales_readiness

    assert process_sales_readiness.name == "sales_readiness.process_pending"


def test_revenue_hunter_statuses_gate():
    assert SalesReadinessStatus.SALES_READY in REVENUE_HUNTER_STATUSES
    assert SalesReadinessStatus.CONTACT_READY in FOUNDER_QUEUE_STATUSES
    assert SalesReadinessStatus.NOT_READY not in FOUNDER_QUEUE_STATUSES


def test_e2e_compose_pipeline_to_rh_eligibility():
    """GOAP/AIP/PH conceptually feed SRE; SRE gates RH."""
    snap = SalesReadinessPipeline().evaluate(
        {
            "company_id": "e2e",
            "company_name": "Northwind Logistics",
            "website": "northwind.com",
            "domain": "northwind.com",
            "industry": "Logistics",
            "country": "US",
            "source": "goap",
            "evidence": ["job"],
            "technologies": ["Salesforce", "AWS", "OpenAI"],
            "signals": ["hiring", "automation", "openai", "funding", "scaling"],
            "decision_makers": [{"name": "Sam", "role": "CEO", "email": "sam@northwind.com", "confidence": 90, "source": "aip"}],
            "emails": ["sam@northwind.com"],
            "verification_score": 85,
            "seo_score": 80,
            "pricing_page": True,
            "has_careers": True,
            "last_seen_at": "2026-07-23T12:00:00+00:00",
            "employees": 400,
            "narrative": "Funding round and hiring automation engineers using OpenAI",
        }
    )
    assert snap.identity.identity_complete
    assert snap.outreach.can_contact_today
    if snap.eligible_for_revenue_hunter:
        assert snap.status in REVENUE_HUNTER_STATUSES
    if snap.visible_in_founder_queue:
        assert snap.status in FOUNDER_QUEUE_STATUSES


def test_regression_production_hardening_untouched_exports():
    from production_hardening import OpportunityAdmissionGate, LeadQualityScorer

    assert OpportunityAdmissionGate is not None
    assert LeadQualityScorer is not None


def test_dashboard_component_exists():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "dashboard" / "features" / "companies" / "sales-readiness-summary.tsx"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Sales Readiness" in text
    assert "UNKNOWN" in text


def test_opportunities_filters_exist():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "dashboard" / "features" / "opportunities" / "opportunities-workspace.tsx"
    text = path.read_text(encoding="utf-8")
    assert "Sales Ready Only" in text
    assert "Enterprise Ready" in text
