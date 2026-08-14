from datetime import UTC, datetime

from intelligence.knowledge_graph import KnowledgeGraphEngine
from intelligence.types import (
    ClassifiedSignalResult,
    EntityResolutionResult,
    Polarity,
    RawSignal,
    ResolvedEntity,
    SignalCategory,
    Urgency,
)


def test_knowledge_graph_connects_company_signal_and_category() -> None:
    signal = RawSignal(
        source="product_hunt",
        url="https://example.com/acme-product",
        title="Acme launches support automation",
        content="Acme launches support automation.",
        published_at=datetime(2026, 7, 10, tzinfo=UTC),
    )
    resolution = EntityResolutionResult(
        company=ResolvedEntity(
            entity_type="company",
            value="Acme",
            normalized_value="acme",
            confidence=0.8,
        )
    )
    classification = ClassifiedSignalResult(
        category=SignalCategory.PRODUCT_LAUNCH,
        subcategory="launch_event",
        confidence=0.88,
        business_function="product",
        urgency=Urgency.HIGH,
        positive_or_negative=Polarity.POSITIVE,
    )

    nodes, edges = KnowledgeGraphEngine().build_graph(signal, resolution, [classification])

    assert {node.node_type for node in nodes} == {"company", "signal", "signal_category"}
    assert {edge.edge_type for edge in edges} == {"has_signal", "classified_as"}
