import time
from uuid import uuid4

from target_account_engine import TargetAccountPipeline, TargetAccountInput


def test_pipeline_throughput_budget() -> None:
    pipeline = TargetAccountPipeline()
    started = time.perf_counter()
    for idx in range(100):
        pipeline.process(
            TargetAccountInput(
                company_id=uuid4(),
                company_name=f"Co {idx}",
                industry="Software",
                employee_count=120,
                technologies=["crm", "zendesk"],
                signals=["funding", "hiring", "automation"],
                pains=["manual workflows"],
                hiring_roles=["Support Engineer"],
                hiring_count=3,
                channels=["email"],
                decision_makers=[{"name": "A", "role": "CTO"}],
            )
        )
    assert (time.perf_counter() - started) < 2.5
