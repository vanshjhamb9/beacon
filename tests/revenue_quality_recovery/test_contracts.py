"""RQP v1 contracts, migration, API, worker, dashboard, regression tests."""

from __future__ import annotations

from pathlib import Path

from revenue_quality_recovery import PRODUCTION_SEND_ENABLED, SCORING_VERSION
from revenue_quality_recovery.pipelines.engine import RevenueQualityPipeline
from runtime_ops.migrations.catalog import HEAD_REVISION, PENDING_CHAIN, REQUIRED_TABLES


def test_version():
    assert SCORING_VERSION == "rqp-v1"
    assert PRODUCTION_SEND_ENABLED is False


def test_migration_file():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "api" / "alembic" / "versions" / "20260724_0033_create_revenue_quality_recovery_tables.py"
    text = path.read_text(encoding="utf-8")
    for table in ("rqp_snapshots", "rqp_daily_kpis", "rqp_acceptance_gates", "rqp_golden_dataset"):
        assert table in text
    assert "20260724_0032" in text
    assert HEAD_REVISION == "20260724_0039"
    assert "20260724_0033" in PENDING_CHAIN
    for table in ("rqp_snapshots", "rqp_daily_kpis", "rqp_acceptance_gates", "rqp_golden_dataset"):
        assert table in REQUIRED_TABLES


def test_api_route_prefix():
    from app.api.routes import revenue_quality_recovery as mod

    assert mod.router.prefix == "/revenue-quality"


def test_models_importable():
    from app.models.revenue_quality_recovery import (
        RqpAcceptanceRow,
        RqpDailyKpiRow,
        RqpGoldenDatasetRow,
        RqpSnapshotRow,
    )

    assert RqpSnapshotRow.__tablename__ == "rqp_snapshots"
    assert RqpDailyKpiRow.__tablename__ == "rqp_daily_kpis"
    assert RqpAcceptanceRow.__tablename__ == "rqp_acceptance_gates"
    assert RqpGoldenDatasetRow.__tablename__ == "rqp_golden_dataset"


def test_worker_task_names():
    from worker.revenue_quality_recovery_tasks import daily_revenue_quality_kpi, process_revenue_quality

    assert process_revenue_quality.name == "revenue_quality.process_pending"
    assert daily_revenue_quality_kpi.name == "revenue_quality.daily_kpi"


def test_celery_includes_rqp():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "worker" / "worker" / "celery_app.py").read_text(encoding="utf-8")
    assert "worker.revenue_quality_recovery_tasks" in text
    assert "revenue_quality.process_pending" in text
    assert "revenue_quality.daily_kpi" in text


def test_dashboard_component_exists():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "dashboard" / "features" / "rqp" / "rqp-qa-workspace.tsx"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Revenue Quality Recovery" in text
    assert "Production send disabled" in text or "production_unlocked" in text


def test_dashboard_page_exists():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "dashboard" / "app" / "(workspace)" / "revenue-quality" / "page.tsx"
    assert path.exists()


def test_sidebar_nav_exists():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "dashboard" / "components" / "layout" / "sidebar.tsx").read_text(encoding="utf-8")
    assert "/revenue-quality" in text
    assert "RQP Quality" in text


def test_beacon_api_hooks():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "dashboard" / "lib" / "api" / "beacon.ts").read_text(encoding="utf-8")
    for name in ("rqpCompany", "rqpEvaluate", "rqpFounderQueue", "rqpKpi", "rqpAcceptance", "rqpDashboard", "rqpSeedGold"):
        assert name in text


def test_package_exports():
    import revenue_quality_recovery as rqp

    assert rqp.SalesReadyGateEngine is not None
    assert rqp.WebsiteCrawlerEngine is not None
    assert rqp.ContactWaterfallEngine is not None
    assert rqp.IdentityValidatorEngine is not None
    assert rqp.EvidencePanelEngine is not None
    assert rqp.DuplicateRecoveryEngine is not None
    assert rqp.AcceptanceEngine is not None
    assert rqp.GoldenDatasetEngine is not None
    assert rqp.RevenueQualityPipeline is not None


def test_regression_rdi_untouched():
    from revenue_data_recovery import SCORING_VERSION as RDI

    assert RDI == "rdi-v1"


def test_regression_sre_untouched():
    from sales_readiness import SCORING_VERSION as SRE

    assert SRE == "sre-v1"


def test_e2e_binary_path():
    snap = RevenueQualityPipeline().evaluate(
        {
            "company_id": "e2e",
            "company_name": "Northwind Logistics",
            "legal_name": "Northwind Logistics Inc",
            "website": "northwind.com",
            "domain": "northwind.com",
            "linkedin_company": "https://linkedin.com/company/northwind",
            "industry": "Logistics",
            "country": "US",
            "employee_estimate": 400,
            "ai_service_match": "Sales Pipeline Automation System",
            "buying_intent": "hiring",
            "signals": ["hiring", "crm"],
            "evidence": [
                {
                    "summary": "hiring sales ops",
                    "source": "goap",
                    "url": "https://example.com/job",
                    "collector": "goap",
                    "reason": "GOAP hiring signal",
                }
            ],
            "decision_makers": [
                {
                    "name": "Sam",
                    "role": "CEO",
                    "email": "sam@northwind.com",
                    "source": "decision_discovery",
                    "confidence": 90,
                    "verification": "mx_valid",
                }
            ],
            "website_alive": True,
            "ssl": True,
            "dns_ok": True,
            "favicon": "x",
            "website_title": "Northwind",
            "logo": "y",
            "organization_schema": {"name": "Northwind Logistics Inc"},
            "domain_age_days": 800,
            "entity_type": "enterprise",
            "mx_valid": True,
            "why_collected": "GOAP hiring signal",
        }
    )
    assert snap.verdict.value in {"SALES_READY", "REJECTED"}
    if snap.verdict.value == "SALES_READY":
        assert snap.surface.admitted
        assert snap.evidence_panel.complete


def test_service_importable():
    from app.services.revenue_quality_recovery import RevenueQualityRecoveryService

    assert RevenueQualityRecoveryService is not None


def test_routes_registered():
    from app.api.routes import router

    paths = {getattr(r, "path", "") for r in router.routes}
    assert any("/revenue-quality" in p for p in paths)
