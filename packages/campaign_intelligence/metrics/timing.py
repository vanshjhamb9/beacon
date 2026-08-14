from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class CampaignTimer:
    def time_call(self, fn: Callable[[], T]) -> tuple[T, float]:
        started = time.perf_counter()
        result = fn()
        return result, (time.perf_counter() - started) * 1000.0
