import time
from uuid import uuid4

from client_execution import ClientExecutionPipeline
from client_execution.models.types import ClientExecutionInput, ClientProjectSignal


def test_500_client_evals_under_5_seconds() -> None:
    pipeline = ClientExecutionPipeline()
    started = time.perf_counter()
    for i in range(500):
        pipeline.process(
            ClientExecutionInput(
                company_id=uuid4(),
                company_name=f"Perf Client {i}",
                industry="SaaS" if i % 2 == 0 else "Healthcare",
                won=True,
                contract_signed=i % 3 != 0,
                kickoff_scheduled=i % 4 == 0,
                development_active=i % 5 == 0,
                launched=i % 7 == 0,
                contract_value=10000 + (i % 50) * 1000,
                requirements=[f"Req {i}"],
                hiring_signals=["hiring"] if i % 6 == 0 else [],
                funding_signals=["series"] if i % 9 == 0 else [],
                projects=[
                    ClientProjectSignal(
                        name=f"P{i}",
                        blocked=i % 11 == 0,
                        at_risk=i % 13 == 0,
                        due_today=i % 8 == 0,
                        milestone="M1" if i % 4 == 0 else None,
                        deliverable="D1" if i % 5 == 0 else None,
                    )
                ],
                open_issues=i % 4,
                satisfaction=40 + (i % 50),
            )
        )
    assert (time.perf_counter() - started) < 5.0
