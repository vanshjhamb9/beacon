from __future__ import annotations

from account_journey.models.types import AccountJourneyDecision, AccountJourneyInput
from account_journey.pipelines.goi_pipeline import AccountJourneyPipeline
from account_journey.replies.engine import ReplyIntelligenceV2Engine


class AccountJourneyService:
    def __init__(self, pipeline: AccountJourneyPipeline | None = None) -> None:
        self.pipeline = pipeline or AccountJourneyPipeline()
        self.replies = ReplyIntelligenceV2Engine()

    def evaluate(self, data: AccountJourneyInput) -> AccountJourneyDecision:
        return self.pipeline.process(data)

    def evaluate_many(self, items: list[AccountJourneyInput]) -> list[AccountJourneyDecision]:
        return [self.evaluate(item) for item in items]

    def classify_reply(self, text: str, *, company_name: str = "Account"):
        from uuid import uuid4

        return self.replies.classify(
            AccountJourneyInput(company_id=uuid4(), company_name=company_name, replied=True, reply_text=text)
        )
