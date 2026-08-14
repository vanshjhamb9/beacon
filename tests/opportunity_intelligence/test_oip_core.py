from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from opportunity_intelligence.buying_window_engine import BuyingWindowEngine
from opportunity_intelligence.confidence_engine import ConfidenceEngine
from opportunity_intelligence.evidence_engine import EvidenceEngine
from opportunity_intelligence.freshness_engine import FreshnessEngine
from opportunity_intelligence.opportunity_builder import OpportunityBuilder
from opportunity_intelligence.opportunity_ranker import OpportunityRanker
from opportunity_intelligence.opportunity_scoring import OpportunityScoring
from opportunity_intelligence.recommendation_engine import RecommendationEngine
from opportunity_intelligence.schemas import CompanyInput, EvidenceInput, SignalInput
from opportunity_intelligence.signal_registry import SignalRegistry
from opportunity_intelligence.source_registry import SourceRegistry


NOW = datetime(2026, 7, 29, tzinfo=UTC)


def evidence(provider: str = "Google News", title: str = "Hiring plan") -> EvidenceInput:
    return EvidenceInput(
        provider=provider,
        source_type="news",
        url=f"https://example.com/{provider.lower().replace(' ', '-')}",
        title=title,
        description="Verified source",
        captured_at=NOW,
        trust=90,
        confidence=88,
    )


def signal(days_old: int = 5) -> SignalInput:
    return SignalInput(
        type="headcount_growth",
        source="Career Pages",
        category="HIRING",
        title="Hiring 500 AI Engineers",
        summary="Company is expanding AI engineering hiring.",
        url="https://example.com/jobs",
        timestamp=NOW - timedelta(days=days_old),
    )


def company() -> CompanyInput:
    return CompanyInput(
        id=uuid4(),
        name="Microsoft",
        website="https://microsoft.com",
        industry="Software",
        country="US",
        icp_score=93,
    )


def test_freshness_buckets_are_deterministic() -> None:
    engine = FreshnessEngine()
    assert engine.calculate(NOW - timedelta(days=7), now=NOW).score == 100
    assert engine.calculate(NOW - timedelta(days=30), now=NOW).score == 90
    assert engine.calculate(NOW - timedelta(days=60), now=NOW).score == 75
    assert engine.calculate(NOW - timedelta(days=90), now=NOW).score == 60
    assert engine.calculate(NOW - timedelta(days=180), now=NOW).score == 30
    assert engine.calculate(NOW - timedelta(days=181), now=NOW).score == 5


def test_buying_window_rules() -> None:
    engine = BuyingWindowEngine()
    assert engine.calculate(30) == "Immediate"
    assert engine.calculate(60) == "Warm"
    assert engine.calculate(90) == "Future"
    assert engine.calculate(91) == "Dormant"


def test_evidence_engine_requires_minimum_and_deduplicates() -> None:
    engine = EvidenceEngine()
    duplicate = evidence()
    unique = engine.deduplicate([duplicate, duplicate, evidence("Crunchbase", "Hiring plan")])
    assert len(unique) == 2
    with pytest.raises(ValueError):
        engine.validate([duplicate])


def test_confidence_increases_with_independent_sources() -> None:
    engine = ConfidenceEngine()
    one = engine.calculate([evidence()])
    many = engine.calculate([evidence(), evidence("Crunchbase"), evidence("LinkedIn")])
    assert many > one


def test_scoring_returns_explainable_breakdown() -> None:
    result = OpportunityScoring().calculate(
        signal_category="HIRING",
        freshness_score=100,
        evidence_score=91,
        icp_score=88,
        buying_window="Immediate",
    )
    assert result.score > 0
    assert set(result.breakdown) == {"intent", "pain", "budget", "growth", "timing", "freshness", "evidence", "icp"}
    assert result.reasons


def test_builder_returns_immutable_opportunity_and_score_record() -> None:
    opportunity = OpportunityBuilder().build(
        signal=signal(),
        company=company(),
        evidence=[evidence(), evidence("Crunchbase")],
        now=NOW,
    )
    assert opportunity.company_name == "Microsoft"
    assert opportunity.buying_window == "Immediate"
    assert opportunity.score_record is not None
    assert len(opportunity.evidence) == 2
    with pytest.raises(Exception):
        opportunity.company_name = "Changed"  # type: ignore[misc]


def test_dedupe_key_changes_by_signal_not_company_only() -> None:
    builder = OpportunityBuilder()
    target = company()
    first = builder.build(signal=signal(5), company=target, evidence=[evidence(), evidence("Crunchbase")], now=NOW)
    second = builder.build(signal=signal(40), company=target, evidence=[evidence(), evidence("Crunchbase")], now=NOW)
    assert first.company_id == second.company_id
    assert first.dedupe_key != second.dedupe_key


def test_ranking_and_recommendation_are_deterministic() -> None:
    builder = OpportunityBuilder()
    target = company()
    immediate = builder.build(signal=signal(5), company=target, evidence=[evidence(), evidence("Crunchbase")], now=NOW)
    dormant = builder.build(signal=signal(120), company=target, evidence=[evidence(), evidence("Crunchbase")], now=NOW)
    ranked = OpportunityRanker().rank([dormant, immediate])
    assert ranked[0] == immediate
    recommendation = RecommendationEngine().build(immediate)
    assert "verified HIRING signal" in recommendation.why_contact
    assert recommendation.supporting_evidence


def test_registries_expose_configuration_only() -> None:
    signals = SignalRegistry().all()
    sources = SourceRegistry().all()
    assert len(signals) == 11
    assert {source.name for source in sources} >= {"LinkedIn", "Twitter", "SEC"}
    assert SourceRegistry().trust_for("LinkedIn") > SourceRegistry().trust_for("RSS")
