from collections import Counter
from datetime import datetime

from intelligence.types import ClassifiedSignalResult, MemoryUpdate, RawSignal


class CompanyMemoryEngine:
    def build_update(
        self,
        signal: RawSignal,
        classifications: list[ClassifiedSignalResult],
        *,
        existing_attributes: dict[str, object] | None = None,
    ) -> MemoryUpdate:
        attributes = dict(existing_attributes or {})
        categories = [classification.category.value for classification in classifications]
        category_counts = Counter(categories)

        historical_intent = dict(attributes.get("historical_intent", {}))
        for category, count in category_counts.items():
            historical_intent[category] = int(historical_intent.get(category, 0)) + count

        attributes["historical_intent"] = historical_intent
        attributes["last_signal_source"] = signal.source
        attributes["last_signal_url"] = signal.url
        attributes["last_categories"] = categories

        return MemoryUpdate(
            last_seen_at=signal.published_at,
            signal_frequency_increment=max(1, len(classifications)),
            memory_summary=self._memory_summary(signal.published_at, historical_intent),
            attributes=attributes,
        )

    def _memory_summary(self, last_seen_at: datetime, historical_intent: dict[str, object]) -> str:
        if not historical_intent:
            return f"Last observed on {last_seen_at.date().isoformat()} with no classified signal."

        strongest = sorted(
            historical_intent.items(),
            key=lambda item: int(item[1]),
            reverse=True,
        )[:3]
        summary = ", ".join(f"{category.replace('_', ' ')}={count}" for category, count in strongest)
        return f"Last observed on {last_seen_at.date().isoformat()}. Strongest memory signals: {summary}."
