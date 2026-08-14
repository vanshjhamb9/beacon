from __future__ import annotations

from live_revenue_execution.lifecycle.engine import CampaignLifecycleEngine
from live_revenue_execution.models.types import LREDecision, LREInput, LREStage
from live_revenue_execution.pipelines.lre_pipeline import LiveRevenueExecutionPipeline
from sales_intelligence.reply.engine import ReplyIntelligenceEngine


class LiveRevenueExecutionService:
    def __init__(self, pipeline: LiveRevenueExecutionPipeline | None = None) -> None:
        self.pipeline = pipeline or LiveRevenueExecutionPipeline()
        self.lifecycle = CampaignLifecycleEngine()
        self.reply = ReplyIntelligenceEngine()

    def evaluate(self, data: LREInput) -> LREDecision:
        return self.pipeline.process(data)

    def evaluate_many(self, items: list[LREInput]) -> list[LREDecision]:
        return [self.evaluate(item) for item in items]

    def classify_reply(self, text: str, *, subject: str = ""):
        return self.reply.classify(text, subject=subject)

    def transition(self, current: LREStage, target: LREStage) -> LREStage:
        return self.lifecycle.transition(current, target)
