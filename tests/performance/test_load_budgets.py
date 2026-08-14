"""Load / throughput smoke benchmarks for Sprint 21 budgets."""

import time
from uuid import uuid4

from live_revenue_execution import LiveRevenueExecutionPipeline
from live_revenue_execution.models.types import LREInput
from production_validation import ProductionValidationPipeline
from production_validation.models.types import ProductionValidationInput


def test_load_mixed_pipeline_budget() -> None:
    """Approximate daily-scale bursts: 200 validations + 100 LRE packs under 5s."""
    prv = ProductionValidationPipeline()
    lre = LiveRevenueExecutionPipeline()
    started = time.perf_counter()
    for i in range(200):
        prv.process(
            ProductionValidationInput(
                company_id=uuid4(),
                company_name=f"L{i}",
                website="x.com",
                business_email=f"{i}@x.com",
                decision_makers=[{"name": "A"}],
                industry="SaaS",
                pain_points=["a"],
                buying_triggers=["b"],
                technologies=["c"],
                linkedin_url="https://linkedin.com/x",
                revenue_estimate="$10k",
                service_match="Website",
                confidence=80,
                freshness_days=1,
                verification_score=80,
                security_flags={k: True for k in (
                    "oauth_tokens", "secrets", "encryption", "webhook_signatures", "rbac",
                    "audit_logs", "rate_limits", "csrf", "jwt", "api_keys",
                )},
            )
        )
    for i in range(100):
        lre.process(
            LREInput(
                company_id=uuid4(),
                company_name=f"R{i}",
                campaign_id=uuid4(),
                email_subject="Hi",
                email_body="Body",
                to_email=f"{i}@x.com",
                probability=60,
            )
        )
    assert (time.perf_counter() - started) < 5.0
