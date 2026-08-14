import time
from datetime import UTC, datetime
from uuid import uuid4

from founder_os import FounderOsPipeline, FounderOsInput


def test_founder_os_pipeline_throughput() -> None:
    pipeline = FounderOsPipeline()
    started = time.perf_counter()
    for i in range(50):
        pipeline.process(
            FounderOsInput(
                a_plus_opportunities=i % 5,
                campaigns_waiting_approval=i % 3,
                replies_waiting=i % 2,
                meetings_today=1,
                estimated_pipeline=100_000,
                expected_revenue=25_000,
                contacted_count=20,
                replied_count=5,
                industry_wins={"SaaS": 2},
                service_wins={"Website": 1},
                top_companies=[
                    {
                        "company_id": str(uuid4()),
                        "company_name": f"Co {i}",
                        "priority_grade": "A",
                        "recommended_service": "Website",
                        "expected_budget": "$12k–$30k",
                        "probability": 60,
                        "evidence": ["test"],
                    }
                ],
                pending_campaigns=[{"id": str(uuid4()), "company_name": f"Co {i}", "status": "needs_review"}],
                now=datetime.now(UTC),
            )
        )
    assert (time.perf_counter() - started) < 2.0
