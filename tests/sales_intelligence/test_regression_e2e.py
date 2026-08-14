"""Regression: compose with existing Beacon engines without redesign."""

from uuid import uuid4

from sales_intelligence import SalesIntelligencePipeline, SalesIntelligenceService
from sales_intelligence.models.types import ReplyClass, SalesIntelligenceInput


def test_regression_hot_buyer_example_shape() -> None:
    decision = SalesIntelligencePipeline().process(
        SalesIntelligenceInput(
            company_id=uuid4(),
            company_name="Example Buyer",
            industry="Ecommerce",
            employee_count=95,
            funding_days_ago=14,
            technologies=["Shopify", "Gorgias", "WhatsApp"],
            pains=["growing support", "high support cost", "manual workflows"],
            signals=["funding", "hiring", "whatsapp"],
            hiring_count=8,
            decision_makers=[{"name": "Sam", "title": "COO"}],
            recommended_service="AI Customer Support",
            expected_budget="$25k–$55k",
            opportunity_score=92,
            priority_grade="A+",
            probability=80,
            replies=[{"body": "Interested — let's schedule a call next week"}],
            emails=[{"subject": "Intro", "body": "Hi"}],
            vendors=["Gorgias"],
        )
    )
    assert decision.buying_intent.buying_intent_score >= 70
    assert decision.buying_intent.urgency.value in {"High", "Critical", "Medium"}
    assert decision.offer.primary_offer
    assert decision.score.close_probability >= 0
    assert decision.scoring_version == "si-v1"


def test_regression_reply_updates_classification_path() -> None:
    service = SalesIntelligenceService()
    classified = service.classify_reply("Please send a proposal with timeline and budget")
    assert classified.classification == ReplyClass.NEED_PROPOSAL
    assert classified.best_response
    assert classified.confidence >= 50


def test_regression_no_gpt_dependency_in_package() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "packages" / "sales_intelligence"
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "openai" not in text.lower()
        assert "chat.completions" not in text.lower()
        assert "gpt-4" not in text.lower()
