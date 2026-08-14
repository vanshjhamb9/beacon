"""PH-1 regression / contract / health / migration tests."""

from __future__ import annotations

from pathlib import Path

from production_hardening import (
    LEAD_QUALITY_HIDE_THRESHOLD,
    SCORING_VERSION,
    CompanyIdentityValidator,
    ContactReadinessEngine,
    LeadQualityScorer,
    OpportunityAdmissionGate,
)
from production_hardening.health.telemetry import LiveHealthTelemetry
from runtime_ops.migrations.catalog import HEAD_REVISION, REQUIRED_TABLES


def test_scoring_version():
    assert SCORING_VERSION == "ph1-v1"
    assert LEAD_QUALITY_HIDE_THRESHOLD == 70.0


def test_migration_file_exists():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "api" / "alembic" / "versions" / "20260724_0030_create_production_hardening_tables.py"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "ph_admission_decisions" in text
    assert "ph_contact_readiness" in text
    assert "ph_company_merges" in text
    assert "ph_trust_snapshots" in text
    assert 'down_revision' in text and "20260724_0029" in text


def test_runtime_ops_head_includes_ph1():
    assert HEAD_REVISION == "20260724_0039"
    assert "ph_admission_decisions" in REQUIRED_TABLES


def test_package_exports():
    assert OpportunityAdmissionGate is not None
    assert CompanyIdentityValidator is not None
    assert ContactReadinessEngine is not None
    assert LeadQualityScorer is not None


def test_health_signals_keys():
    signals = LiveHealthTelemetry().build_signals(
        {
            "redis_ok": True,
            "database_ok": True,
            "api_ok": True,
            "worker_online": True,
            "beat_online": True,
            "email_configured": False,
            "whatsapp_configured": False,
            "oauth_ok": False,
            "collectors_running": 3,
            "collectors_total": 8,
            "queue_depth": 12,
        }
    )
    for key in ("api", "database", "redis", "email", "whatsapp", "oauth", "collectors", "celery", "pipeline"):
        assert key in signals


def test_no_hardcoded_95_in_telemetry_defaults():
    signals = LiveHealthTelemetry().build_signals({})
    assert signals["email"]["success_rate"] != 96.0
    assert signals["whatsapp"]["success_rate"] != 95.0
    assert signals["email"]["success_rate"] == 0.0


def test_api_route_module_importable():
    from app.api.routes import production_hardening as mod

    assert mod.router.prefix == "/production-hardening"


def test_service_module_importable():
    from app.services.production_hardening import ProductionHardeningService

    assert ProductionHardeningService is not None


def test_models_importable():
    from app.models.production_hardening import (
        PhAdmissionDecision,
        PhCompanyMerge,
        PhContactReadiness,
        PhTrustSnapshot,
    )

    assert PhAdmissionDecision.__tablename__ == "ph_admission_decisions"
    assert PhContactReadiness.__tablename__ == "ph_contact_readiness"
    assert PhCompanyMerge.__tablename__ == "ph_company_merges"
    assert PhTrustSnapshot.__tablename__ == "ph_trust_snapshots"
