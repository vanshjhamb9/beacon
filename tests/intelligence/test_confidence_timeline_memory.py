from datetime import UTC, datetime

from intelligence.company_memory import CompanyMemoryEngine
from intelligence.confidence_engine import ConfidenceEngine
from intelligence.timeline import TimelineEngine
from intelligence.types import (
    ClassifiedSignalResult,
    EntityResolutionResult,
    Polarity,
    RawSignal,
    ResolvedEntity,
    SignalCategory,
    Urgency,
)


def test_confidence_timeline_and_memory_are_deterministic() -> None:
    signal = RawSignal(
        source="hacker_news",
        url="https://example.com/nike-ai",
        title="Nike launches AI automation project",
        content="Nike launches AI automation project for customer support.",
        published_at=datetime.now(UTC),
    )
    classification = ClassifiedSignalResult(
        category=SignalCategory.AI_ADOPTION,
        subcategory="ai_initiative",
        confidence=0.84,
        business_function="technology",
        urgency=Urgency.HIGH,
        positive_or_negative=Polarity.POSITIVE,
        evidence={"matched_terms": ["ai"]},
    )
    resolution = EntityResolutionResult(
        company=ResolvedEntity(
            entity_type="company",
            value="Nike",
            normalized_value="nike",
            confidence=0.92,
            evidence={"method": "domain"},
        )
    )

    confidence = ConfidenceEngine().calculate(signal, classification, resolution)
    timeline_item = TimelineEngine().build_item(signal, classification, confidence)
    memory = CompanyMemoryEngine().build_update(signal, [classification])

    assert confidence.overall_confidence > 0.8
    assert timeline_item.signal_type == "ai_adoption"
    assert "Nike launches AI automation project" in timeline_item.summary
    assert memory.signal_frequency_increment == 1
    assert memory.attributes["historical_intent"]["ai_adoption"] == 1
