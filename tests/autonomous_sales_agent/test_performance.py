import time
from uuid import uuid4

from autonomous_sales_agent import AutonomousSalesAgentPipeline
from autonomous_sales_agent.models.types import AutonomousSalesAgentInput


def test_100_workflow_evals_under_3_seconds() -> None:
    pipeline = AutonomousSalesAgentPipeline()
    started = time.perf_counter()
    for i in range(100):
        pipeline.process(
            AutonomousSalesAgentInput(
                company_id=uuid4(),
                company_name=f"Perf Co {i}",
                industry="SaaS" if i % 2 == 0 else "Healthcare",
                priority_grade="A" if i % 3 else "B",
                probability=40 + (i % 50),
                buying_intent_score=30 + (i % 60),
                days_since_last_touch=i % 21,
                has_decision_makers=True,
                decision_makers=[{"name": "CEO"}],
                pains=["ops"],
                email_sent=True,
                recommended_service="AI Automation",
            )
        )
    assert (time.perf_counter() - started) < 3.0
