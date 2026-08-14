from datetime import UTC, datetime

from intelligence.types import ClassifiedSignalResult, ConfidenceResult, EntityResolutionResult, RawSignal

SOURCE_CONFIDENCE = {
    "hacker_news": 0.82,
    "product_hunt": 0.78,
    "reddit": 0.68,
    "rss": 0.74,
}


class ConfidenceEngine:
    def calculate(
        self,
        signal: RawSignal,
        classification: ClassifiedSignalResult,
        resolution: EntityResolutionResult,
        *,
        source_reliability: float | None = None,
    ) -> ConfidenceResult:
        source_confidence = source_reliability or SOURCE_CONFIDENCE.get(signal.source, 0.6)
        entity_confidence = self._entity_confidence(resolution)
        classification_confidence = classification.confidence
        freshness_score = self._freshness_score(signal.published_at)
        reliability_score = round((source_confidence * 0.7) + (freshness_score * 0.3), 4)

        overall = (
            source_confidence * 0.2
            + entity_confidence * 0.25
            + classification_confidence * 0.3
            + freshness_score * 0.15
            + reliability_score * 0.1
        )

        return ConfidenceResult(
            source_confidence=round(source_confidence, 4),
            entity_confidence=round(entity_confidence, 4),
            classification_confidence=round(classification_confidence, 4),
            freshness_score=round(freshness_score, 4),
            reliability_score=round(reliability_score, 4),
            overall_confidence=round(overall, 4),
            explanation={
                "formula": {
                    "source_confidence": 0.2,
                    "entity_confidence": 0.25,
                    "classification_confidence": 0.3,
                    "freshness_score": 0.15,
                    "reliability_score": 0.1,
                },
                "source": signal.source,
                "classification_category": classification.category.value,
                "entity_resolution": resolution.model_dump(mode="json"),
            },
        )

    def _entity_confidence(self, resolution: EntityResolutionResult) -> float:
        scores = [
            entity.confidence
            for entity in [
                resolution.company,
                resolution.domain,
                resolution.person,
                *resolution.technologies,
                *resolution.products,
            ]
            if entity is not None
        ]
        if not scores:
            return 0.35
        return sum(scores) / len(scores)

    def _freshness_score(self, published_at: datetime) -> float:
        published = published_at if published_at.tzinfo else published_at.replace(tzinfo=UTC)
        age_days = max(0.0, (datetime.now(UTC) - published.astimezone(UTC)).total_seconds() / 86_400)
        if age_days <= 1:
            return 1.0
        if age_days <= 7:
            return 0.86
        if age_days <= 30:
            return 0.68
        if age_days <= 90:
            return 0.42
        return 0.2
