import time
from uuid import uuid4

from account_journey import AccountJourneyPipeline
from account_journey.models.types import AccountJourneyInput


def test_300_account_evals_under_5_seconds() -> None:
    pipeline = AccountJourneyPipeline()
    started = time.perf_counter()
    for i in range(300):
        pipeline.process(
            AccountJourneyInput(
                company_id=uuid4(),
                company_name=f"Perf {i}",
                industry="SaaS" if i % 2 == 0 else "Healthcare",
                probability=30 + (i % 60),
                buying_intent=20 + (i % 70),
                emailed=True,
                opened=i % 3 == 0,
                replied=i % 7 == 0,
                no_reply_days=i % 12,
                decision_makers=[{"name": "A", "title": "CEO"}],
                reply_text="interested" if i % 7 == 0 else "",
            )
        )
    assert (time.perf_counter() - started) < 5.0
