from __future__ import annotations

from sales_intelligence.models.types import SalesIntelligenceDecision, SalesIntelligenceInput
from sales_intelligence.pipelines.sales_intelligence_pipeline import SalesIntelligencePipeline
from sales_intelligence.reply.engine import ReplyIntelligenceEngine


class SalesIntelligenceService:
    def __init__(self, pipeline: SalesIntelligencePipeline | None = None) -> None:
        self.pipeline = pipeline or SalesIntelligencePipeline()
        self.reply_engine = ReplyIntelligenceEngine()

    def evaluate(self, data: SalesIntelligenceInput) -> SalesIntelligenceDecision:
        return self.pipeline.process(data)

    def evaluate_many(self, items: list[SalesIntelligenceInput]) -> list[SalesIntelligenceDecision]:
        return [self.evaluate(item) for item in items]

    def classify_reply(self, reply_text: str, *, subject: str = ""):
        return self.reply_engine.classify(reply_text, subject=subject)
