import time
from uuid import uuid4

from live_revenue_execution import LiveRevenueExecutionPipeline
from live_revenue_execution.models.types import LREInput


def test_100_lre_evaluations_under_3_seconds() -> None:
    pipeline = LiveRevenueExecutionPipeline()
    started = time.perf_counter()
    for i in range(100):
        pipeline.process(
            LREInput(
                company_id=uuid4(),
                company_name=f"Perf {i}",
                campaign_id=uuid4(),
                probability=50 + (i % 40),
                priority_grade="A" if i % 2 == 0 else "B",
                email_subject="Hello",
                email_body="Body",
                to_email=f"a{i}@example.com",
                to_whatsapp=f"+1555000{i:04d}",
                pain_points=["manual workflows"],
                recommended_service="Website",
                funnel_counts={"emails": i % 5, "replies": i % 2},
            )
        )
    assert (time.perf_counter() - started) < 3.0
