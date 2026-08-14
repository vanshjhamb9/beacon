"""Recovery / failure-mode composition tests."""

from uuid import uuid4

from communication_gateway.safety.controls import SafetyControls
from production_validation import ProductionValidationService
from production_validation.models.types import ProductionValidationInput


def test_idempotent_send_blocks_duplicates() -> None:
    safety = SafetyControls(daily_email_quota=100, hourly_email_quota=50)
    key = "campaign:step:1"
    first = safety.check_send(idempotency_key=key, campaign_stopped=False)
    assert first.allowed
    safety.record_send(idempotency_key=key)
    second = safety.check_send(idempotency_key=key, campaign_stopped=False)
    assert second.allowed is False
    assert second.code == "duplicate_send"


def test_oauth_and_worker_recovery_alerts() -> None:
    decision = ProductionValidationService().evaluate(
        ProductionValidationInput(
            company_id=uuid4(),
            company_name="Recover",
            website="r.com",
            business_email="a@r.com",
            decision_makers=[{"name": "A"}],
            industry="SaaS",
            pain_points=["x"],
            buying_triggers=["y"],
            technologies=["z"],
            linkedin_url="https://linkedin.com/r",
            revenue_estimate="$10k",
            service_match="MVP",
            confidence=80,
            freshness_days=1,
            verification_score=80,
            oauth_ok=False,
            workers_online=False,
            queue_depth=900,
            webhook_failures=4,
            security_flags={k: True for k in (
                "oauth_tokens", "secrets", "encryption", "webhook_signatures", "rbac",
                "audit_logs", "rate_limits", "csrf", "jwt", "api_keys",
            )},
        )
    )
    codes = {a.code for a in decision.alerts}
    assert {"oauth_expired", "worker_offline", "queue_blocked", "webhook_failure"} <= codes
    assert all(a.recommendation for a in decision.alerts)
