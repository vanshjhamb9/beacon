import time
from collections.abc import Callable
from typing import TypeVar

from quality_engine.models.types import StageResult

ResultT = TypeVar("ResultT")


class PipelineTimer:
    def time_stage(self, operation: Callable[[], StageResult]) -> StageResult:
        started = time.perf_counter()
        result = operation()
        duration_ms = round((time.perf_counter() - started) * 1000, 4)
        return result.model_copy(update={"duration_ms": duration_ms})

    def time_value(self, operation: Callable[[], tuple[ResultT, StageResult]]) -> tuple[ResultT, StageResult]:
        started = time.perf_counter()
        value, result = operation()
        duration_ms = round((time.perf_counter() - started) * 1000, 4)
        return value, result.model_copy(update={"duration_ms": duration_ms})
