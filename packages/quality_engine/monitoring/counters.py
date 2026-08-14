from collections import Counter


class QualityCounters:
    def __init__(self) -> None:
        self._counter: Counter[str] = Counter()

    def increment(self, key: str, value: int = 1) -> None:
        self._counter[key] += value

    def snapshot(self) -> dict[str, int]:
        return dict(self._counter)
