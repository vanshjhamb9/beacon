import time
from uuid import uuid4

from account_intelligence import AccountIntelligencePipeline
from account_intelligence.models.types import AccountIntelligenceInput, ObservedContact


def test_500_enrichments_under_5_seconds() -> None:
    pipeline = AccountIntelligencePipeline()
    started = time.perf_counter()
    for i in range(500):
        pipeline.process(
            AccountIntelligenceInput(
                company_id=uuid4(),
                company_name=f"Perf {i}",
                domain=f"perf{i}.io",
                industry="SaaS" if i % 2 == 0 else "Healthcare",
                employee_count=10 + (i % 200),
                buying_intent=20 + (i % 70),
                html_hints=["react", "https", "viewport"] if i % 3 == 0 else ["wordpress"],
                tech_hints=["aws"] if i % 4 == 0 else [],
                observed_contacts=(
                    [
                        ObservedContact(
                            full_name=f"Person {i}",
                            role="CEO",
                            business_email=f"p{i}@perf{i}.io",
                            source="public",
                            evidence=["e"],
                        )
                    ]
                    if i % 5 == 0
                    else []
                ),
            )
        )
    assert (time.perf_counter() - started) < 5.0
