import time
from uuid import uuid4

from sales_intelligence import SalesIntelligencePipeline, SalesIntelligenceService
from sales_intelligence.models.types import SalesIntelligenceInput


def _item(i: int) -> SalesIntelligenceInput:
    return SalesIntelligenceInput(
        company_id=uuid4(),
        company_name=f"Perf Co {i}",
        industry="SaaS" if i % 2 == 0 else "Ecommerce",
        employee_count=40 + (i % 200),
        funding_days_ago=10 + (i % 80),
        technologies=["Python", "Next.js"],
        pains=["manual workflows", "high support cost"],
        signals=["hiring", "funding"],
        hiring_count=i % 8,
        decision_makers=[{"name": f"DM {i}", "title": "CEO"}],
        recommended_service="AI Automation",
        opportunity_score=50 + (i % 40),
        priority_grade="A" if i % 3 == 0 else "B",
        probability=40 + (i % 50),
        replies=[{"body": "Interested, let's meet", "subject": "Re"}],
        emails=[{"subject": "Outreach", "body": "Hello"}],
        vendors=["Zendesk"] if i % 4 == 0 else [],
    )


def test_100_company_evaluations_under_3_seconds() -> None:
    pipeline = SalesIntelligencePipeline()
    started = time.perf_counter()
    results = [pipeline.process(_item(i)) for i in range(100)]
    elapsed = time.perf_counter() - started
    assert len(results) == 100
    assert elapsed < 3.0, f"100 evaluations took {elapsed:.3f}s"


def test_service_batch_under_budget() -> None:
    service = SalesIntelligenceService()
    started = time.perf_counter()
    service.evaluate_many([_item(i) for i in range(50)])
    assert (time.perf_counter() - started) < 2.0
