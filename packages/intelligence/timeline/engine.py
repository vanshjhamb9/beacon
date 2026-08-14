from intelligence.types import ClassifiedSignalResult, ConfidenceResult, RawSignal, TimelineItemDraft


class TimelineEngine:
    def build_item(
        self,
        signal: RawSignal,
        classification: ClassifiedSignalResult,
        confidence: ConfidenceResult,
    ) -> TimelineItemDraft:
        summary = self._summary(signal, classification)
        return TimelineItemDraft(
            timestamp=signal.published_at,
            source=signal.source,
            signal_type=classification.category.value,
            summary=summary,
            confidence=confidence.overall_confidence,
            evidence={
                "url": signal.url,
                "title": signal.title,
                "source": signal.source,
                "classification": classification.model_dump(mode="json"),
                "confidence": confidence.model_dump(mode="json"),
            },
        )

    def _summary(self, signal: RawSignal, classification: ClassifiedSignalResult) -> str:
        title = signal.title.strip()
        category = classification.category.value.replace("_", " ")
        if title:
            return f"{category.title()}: {title}"
        return f"{category.title()} signal from {signal.source}"
