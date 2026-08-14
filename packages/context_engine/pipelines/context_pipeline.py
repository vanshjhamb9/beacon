from context_engine.metrics.timing import ContextTimer
from context_engine.models.types import BusinessContextInput, BusinessContextResult, CompanyDNAResult
from context_engine.reasoning.engine import BusinessReasoningEngine


class ContextPipeline:
    def __init__(
        self,
        *,
        reasoning_engine: BusinessReasoningEngine | None = None,
        timer: ContextTimer | None = None,
    ) -> None:
        self.reasoning_engine = reasoning_engine or BusinessReasoningEngine()
        self.timer = timer or ContextTimer()

    def process(self, item: BusinessContextInput) -> tuple[BusinessContextResult, CompanyDNAResult]:
        (context, dna), duration_ms = self.timer.measure(lambda: self.reasoning_engine.reason(item))
        return context.model_copy(update={"processing_time_ms": duration_ms}), dna
