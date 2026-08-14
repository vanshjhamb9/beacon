from typing import Protocol

from intelligence_improvement.models import FeedbackSignal, PredictionEvaluation


class ImprovementDatasetRepository(Protocol):
    async def feedback_signals(self, *, limit: int) -> list[FeedbackSignal]:
        ...

    async def prediction_evaluations(self, *, limit: int) -> list[PredictionEvaluation]:
        ...
