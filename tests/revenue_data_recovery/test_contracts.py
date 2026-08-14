"""RDI v1 contracts, migration, API, worker, dashboard, regression tests."""

from __future__ import annotations

from pathlib import Path

from revenue_data_recovery import SCORING_VERSION, UNKNOWN
from revenue_data_recovery.pipelines.engine import RevenueDataRecoveryPipeline
from runtime_ops.migrations.catalog import HEAD_REVISION, PENDING_CHAIN, REQUIRED_TABLES


def test_version():
    assert SCORING_VERSION == "rdi-v1"
    assert UNKNOWN == "UNKNOWN"


def test_migration_file():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "api" / "alembic" / "versions" / "20260724_0032_create_revenue_data_recovery_tables.py"
    text = path.read_text(encoding="utf-8")
    for table in ("rdi_snapshots", "rdi_recovery_queue", "rdi_dossiers", "rdi_metrics_snapshots"):
        assert table in text
    assert "20260724_0031" in text
    assert HEAD_REVISION == "20260724_0039"
    assert "20260724_0032" in PENDING_CHAIN
    for table in ("rdi_snapshots", "rdi_recovery_queue", "rdi_dossiers", "rdi_metrics_snapshots"):
        assert table in REQUIRED_TABLES


def test_api_route_prefix():
    from app.api.routes import revenue_data_recovery as mod

    assert mod.router.prefix == "/revenue-data-recovery"


def test_models_importable():
    from app.models.revenue_data_recovery import (
        RdiDossierRow,
        RdiMetricsSnapshotRow,
        RdiRecoveryQueueRow,
        RdiSnapshotRow,
    )

    assert RdiSnapshotRow.__tablename__ == "rdi_snapshots"
    assert RdiRecoveryQueueRow.__tablename__ == "rdi_recovery_queue"
    assert RdiDossierRow.__tablename__ == "rdi_dossiers"
    assert RdiMetricsSnapshotRow.__tablename__ == "rdi_metrics_snapshots"


def test_worker_task_names():
    from worker.revenue_data_recovery_tasks import daily_revenue_data_recovery, process_revenue_data_recovery

    assert process_revenue_data_recovery.name == "revenue_data_recovery.process_pending"
    assert daily_revenue_data_recovery.name == "revenue_data_recovery.daily_report"


def test_celery_includes_rdi():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "worker" / "worker" / "celery_app.py").read_text(encoding="utf-8")
    assert "worker.revenue_data_recovery_tasks" in text
    assert "revenue_data_recovery.process_pending" in text
    assert "revenue_data_recovery.daily_report" in text


def test_dashboard_component_exists():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "dashboard" / "features" / "rdi" / "rdi-qa-workspace.tsx"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Revenue Data Recovery" in text
    assert "rdiQa" in text or "beaconApi.rdiQa" in text


def test_dashboard_page_exists():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "dashboard" / "app" / "(workspace)" / "revenue-data-recovery" / "page.tsx"
    assert path.exists()


def test_sidebar_nav_exists():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "dashboard" / "components" / "layout" / "sidebar.tsx").read_text(encoding="utf-8")
    assert "/revenue-data-recovery" in text
    assert "RDI Recovery" in text


def test_beacon_api_client_hooks():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "dashboard" / "lib" / "api" / "beacon.ts").read_text(encoding="utf-8")
    for name in ("rdiCompany", "rdiEvaluate", "rdiDossier", "rdiQueue", "rdiFounderQueue", "rdiDashboard", "rdiQa"):
        assert name in text


def test_package_exports():
    import revenue_data_recovery as rdi

    assert rdi.IdentityRecoveryEngine is not None
    assert rdi.WebsiteRecoveryEngine is not None
    assert rdi.FakeCompanyEliminationEngine is not None
    assert rdi.ContactRecoveryEngine is not None
    assert rdi.OpportunityValidationEngine is not None
    assert rdi.IntentIntelligenceEngine is not None
    assert rdi.RevenueRecommendationEngine is not None
    assert rdi.QualityGateEngine is not None
    assert rdi.RecoveryQueueEngine is not None
    assert rdi.RevenueDossierBuilder is not None
    assert rdi.DailyRecoveryWorker is not None
    assert rdi.RevenueDataRecoveryPipeline is not None


def test_regression_sales_readiness_untouched():
    from sales_readiness import SCORING_VERSION as SRE_VERSION
    from sales_readiness.pipelines.engine import SalesReadinessPipeline

    assert SRE_VERSION == "sre-v1"
    assert SalesReadinessPipeline is not None


def test_regression_production_hardening_untouched():
    from production_hardening import OpportunityAdmissionGate, LeadQualityScorer

    assert OpportunityAdmissionGate is not None
    assert LeadQualityScorer is not None


def test_e2e_compose_to_revenue_hunter_gate():
    snap = RevenueDataRecoveryPipeline().evaluate(
        {
            "company_id": "e2e",
            "company_name": "Northwind Logistics",
            "legal_name": "Northwind Logistics Inc",
            "website": "northwind.com",
            "domain": "northwind.com",
            "industry": "Logistics",
            "country": "US",
            "business_category": "enterprise",
            "description": "Freight SaaS for mid-market shippers",
            "source": "goap",
            "evidence": [{"summary": "hiring automation engineers"}],
            "technologies": ["Salesforce", "AWS", "OpenAI"],
            "signals": ["hiring", "automation", "openai", "funding", "scaling", "crm"],
            "decision_makers": [
                {"name": "Sam", "role": "CEO", "email": "sam@northwind.com", "confidence": 90, "source": "aip"}
            ],
            "emails": ["sam@northwind.com"],
            "linkedin_company_url": "https://linkedin.com/company/northwind",
            "narrative": "Funding round and hiring automation engineers using OpenAI and Salesforce CRM",
            "why_collected": "GOAP hiring + funding signals",
            "employees": 400,
        }
    )
    assert snap.identity.identity_complete
    assert snap.website.website_verified
    assert not snap.fake.is_fake
    assert snap.recommendations.primary_service != "AI Automation"
    if snap.eligible_for_revenue_hunter:
        assert snap.quality_gate.passed
        assert snap.dossier is not None
        assert snap.dossier.status.value == "SALES_READY"


def test_service_module_importable():
    from app.services.revenue_data_recovery import RevenueDataRecoveryService

    assert RevenueDataRecoveryService is not None


def test_routes_registered():
    from app.api.routes import router

    paths = {getattr(r, "path", "") for r in router.routes}
    assert any("/revenue-data-recovery" in p for p in paths)
