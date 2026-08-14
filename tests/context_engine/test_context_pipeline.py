from datetime import UTC, datetime
from uuid import uuid4

from context_engine import BuyingStage, ContextPipeline
from context_engine.models import BusinessContextInput


def make_input(category: str = "customer_support") -> BusinessContextInput:
    return BusinessContextInput(
        company_id=uuid4(),
        company_name="Nike",
        classified_signal_id=uuid4(),
        raw_event_id=uuid4(),
        category=category,
        subcategory=None,
        signal_confidence=84.0,
        business_function="support",
        urgency="high",
        polarity="negative",
        title="Nike customer support complaints increase",
        content="Nike is seeing support complaints and is adopting Zendesk automation for customer support.",
        source="rss",
        published_at=datetime.now(UTC),
        quality_report_id=uuid4(),
        quality_score=88.0,
        timeline_item_id=uuid4(),
        knowledge_node_ids=[uuid4()],
        company_attributes={"industry": "retail", "signal_frequency": 5},
    )


def test_context_pipeline_explains_why_signal_matters() -> None:
    context, dna = ContextPipeline().process(make_input())

    assert context.business_pain.category == "customer_support"
    assert context.support_pressure > 50
    assert context.buying_stage in {BuyingStage.AWARE, BuyingStage.PROBLEM_AWARE}
    assert context.evidence.source_events
    assert context.evidence.quality_references
    assert "Zendesk" in dna.technology_stack
    assert dna.company_stage.value == "mature"
