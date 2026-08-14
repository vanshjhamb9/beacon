import time
from collections.abc import Callable
from typing import TypeVar

ResultT = TypeVar("ResultT")


class VerificationTimer:
    def measure(self, operation: Callable[[], ResultT]) -> tuple[ResultT, float]:
        started = time.perf_counter()
        result = operation()
        return result, round((time.perf_counter() - started) * 1000.0, 4)
