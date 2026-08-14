from datetime import UTC, datetime, timedelta
from uuid import uuid4

from opportunity_engine import OpportunityPipeline, RecommendationAction
from opportunity_engine.models import CompanyOpportunityInput, OpportunityEvidenceItem, OpportunityStatus


def make_input(*, include_conflict: bool = False) -> CompanyOpportunityInput:
    now = datetime.now(UTC)
    evidence = [
        OpportunityEvidenceItem(
            source_type="business_context",
            reference_id=uuid4(),
            category="funding",
            summary="Company raised funding and has budget window.",
            confidence=88.0,
            occurred_at=now - timedelta(days=3),
        ),
        OpportunityEvidenceItem(
            source_type="business_pain",
            reference_id=uuid4(),
            category="automation",
            summary="Operations team is seeking automation.",
            confidence=82.0,
            occurred_at=now - timedelta(days=5),
        ),
        OpportunityEvidenceItem(
            source_type="technology_signal",
            reference_id=uuid4(),
            category="technology_migration",
            summary="Company adopted OpenAI and Salesforce.",
            confidence=84.0,
            occurred_at=now - timedelta(days=8),
        ),
    ]
    signals = [{"category": "funding"}, {"category": "expansion"}, {"category": "hiring"}]
    if include_conflict:
        evidence.append(
            OpportunityEvidenceItem(
                source_type="classified_signal",
                reference_id=uuid4(),
                category="budget_cuts",
                summary="Company announced budget cuts.",
                confidence=80.0,
                occurred_at=now - timedelta(days=2),
                polarity="contradicting",
            )
        )
        signals.append({"category": "budget_cuts"})
    return CompanyOpportunityInput(
        company_id=uuid4(),
        company_name="Nike",
        business_context_ids=[uuid4()],
        latest_context_at=now,
        contexts=[
            {
                "budget_probability": 86.0,
                "confidence": 84.0,
                "support_pressure": 35.0,
                "operational_pressure": 78.0,
                "sales_pressure": 62.0,
                "ai_readiness": 76.0,
                "automation_readiness": 82.0,
            }
        ],
        company_profile={"technology_maturity": 78.0, "ai_adoption": 74.0, "automation_adoption": 83.0},
        signals=signals,
        timeline=[{"signal_type": "funding"}, {"signal_type": "expansion"}],
        pains=[{"category": "automation", "confidence": 82.0}],
        goals=[{"category": "deploy_new_capital", "confidence": 80.0}],
        technologies=[{"technology": "OpenAI", "confidence": 84.0}],
        evidence=evidence,
        previous_score=60.0,
        previous_status=OpportunityStatus.EMERGING,
    )


def test_opportunity_pipeline_creates_explainable_decision() -> None:
    decision = OpportunityPipeline().process(make_input())

    assert decision.opportunity_score > 70
    assert decision.status in {OpportunityStatus.QUALIFIED, OpportunityStatus.HIGH_INTENT}
    assert decision.recommendation.action in {
        RecommendationAction.CONTACT_WITHIN_30_DAYS,
        RecommendationAction.CONTACT_WITHIN_7_DAYS,
        RecommendationAction.CONTACT_TODAY,
    }
    assert decision.score_breakdown
    assert decision.evidence
    assert decision.delta.direction == "increased"
    assert "Nike" in decision.narrative


def test_opportunity_pipeline_documents_conflicting_evidence() -> None:
    decision = OpportunityPipeline().process(make_input(include_conflict=True))

    assert decision.conflicts
    assert decision.contradicting_signals
    assert decision.recommendation.reasons
