from uuid import uuid4

from production_validation import ProductionValidationPipeline, ProductionValidationService
from production_validation.models.types import ProductionValidationInput
from worker.celery_app import celery_app


def _ok() -> ProductionValidationInput:
    return ProductionValidationInput(
        company_id=uuid4(),
        company_name="E2E Co",
        website="e2e.com",
        business_email="ceo@e2e.com",
        decision_makers=[{"name": "Ceo", "email": "ceo@e2e.com"}],
        linkedin_url="https://linkedin.com/company/e2e",
        technologies=["Next.js"],
        industry="Fintech",
        buying_triggers=["funding"],
        pain_points=["compliance"],
        revenue_estimate="$60k",
        service_match="Custom AI",
        confidence=90,
        freshness_days=4,
        verification_score=92,
        oauth_ok=True,
        workers_online=True,
        campaigns=[{
            "campaign_id": str(uuid4()),
            "company_name": "E2E Co",
            "emails_sent": 5,
            "delivered": 5,
            "opened": 3,
            "clicked": 1,
            "replies": 1,
            "meetings": 1,
            "proposals": 1,
            "won": 1,
            "revenue": 60000,
            "stage": "won",
        }],
        revenue_metrics={"pipeline_value": 200000, "revenue_closed": 60000, "sales_ready": 10, "qualified_companies": 20},
        security_flags={k: True for k in (
            "oauth_tokens", "secrets", "encryption", "webhook_signatures", "rbac",
            "audit_logs", "rate_limits", "csrf", "jwt", "api_keys",
        )},
    )


def test_e2e_sales_workflow_observable() -> None:
    decision = ProductionValidationPipeline().process(_ok())
    assert decision.lead_readiness and decision.lead_readiness.outreach_allowed
    assert decision.campaign_funnels[0].won == 1
    assert decision.revenue.revenue_closed >= 0
    assert decision.readiness_report.overall_score >= 90
    assert decision.outcome_learning.requires_human_approval is True


def test_worker_registered() -> None:
    assert "worker.production_validation_tasks" in (celery_app.conf.include or [])
    assert "refresh-production-validation" in (celery_app.conf.beat_schedule or {})


def test_recovery_signals_generate_alerts() -> None:
    decision = ProductionValidationService().evaluate(
        _ok().model_copy(update={
            "workers_online": False,
            "oauth_ok": False,
            "duplicate_send_detected": True,
            "migration_drift": True,
            "api_failures": 9,
        })
    )
    codes = {a.code for a in decision.alerts}
    assert "worker_offline" in codes
    assert "oauth_expired" in codes
    assert "duplicate_sends" in codes
    assert "migration_drift" in codes
