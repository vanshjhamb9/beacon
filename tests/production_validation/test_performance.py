import time
from uuid import uuid4

from production_validation import ProductionValidationPipeline
from production_validation.models.types import ProductionValidationInput


def test_100_validation_evals_under_2_seconds() -> None:
    pipeline = ProductionValidationPipeline()
    started = time.perf_counter()
    for i in range(100):
        pipeline.process(
            ProductionValidationInput(
                company_id=uuid4(),
                company_name=f"Co {i}",
                website="x.com",
                business_email=f"a{i}@x.com",
                decision_makers=[{"name": "A"}],
                industry="SaaS",
                pain_points=["ops"],
                buying_triggers=["hiring"],
                technologies=["Python"],
                linkedin_url="https://linkedin.com/x",
                revenue_estimate="$20k",
                service_match="Website",
                confidence=80,
                freshness_days=3,
                verification_score=80,
                oauth_ok=True,
                workers_online=True,
                security_flags={k: True for k in (
                    "oauth_tokens", "secrets", "encryption", "webhook_signatures", "rbac",
                    "audit_logs", "rate_limits", "csrf", "jwt", "api_keys",
                )},
            )
        )
    assert (time.perf_counter() - started) < 2.0
