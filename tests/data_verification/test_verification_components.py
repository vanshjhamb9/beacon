from datetime import UTC, datetime, timedelta

from data_verification.coverage.engine import CoverageEngine
from data_verification.freshness.engine import FreshnessEngine
from data_verification.models.types import FreshnessStatus
from data_verification.trust.engine import TrustEngine
from tests.data_verification.test_verification_pipeline import make_input


def test_freshness_bands() -> None:
    engine = FreshnessEngine()
    now = datetime.now(UTC)
    score, status, _age = engine.evaluate(now - timedelta(days=1), now=now)
    assert status == FreshnessStatus.FRESH
    assert score == 100.0
    _score, stale_status, _ = engine.evaluate(now - timedelta(days=45), now=now)
    assert stale_status == FreshnessStatus.STALE
    _score, expired_status, _ = engine.evaluate(now - timedelta(days=100), now=now)
    assert expired_status == FreshnessStatus.EXPIRED


def test_coverage_engine_computes_all_dimensions() -> None:
    completeness, coverage, checklist, missing = CoverageEngine().evaluate(
        make_input().lead_profile,
        timeline_event_count=4,
    )
    assert completeness.overall_completeness > 50
    assert {item.category for item in coverage} >= {
        "company_profile",
        "contacts",
        "leadership",
        "technology",
        "revenue",
        "hiring",
        "social",
        "evidence",
        "timeline",
    }
    assert checklist.public_business_email is True
    assert isinstance(missing, list)


def test_trust_engine_rewards_confirmation() -> None:
    engine = TrustEngine()
    solo = engine.score_field(
        source="company_website",
        confidence=80.0,
        confirmed_by=[],
        conflicting_sources=[],
    )
    confirmed = engine.score_field(
        source="company_website",
        confidence=80.0,
        confirmed_by=["beacon_intelligence"],
        conflicting_sources=[],
    )
    conflicted = engine.score_field(
        source="company_website",
        confidence=80.0,
        confirmed_by=[],
        conflicting_sources=["crunchbase"],
    )
    assert confirmed > solo
    assert conflicted < solo
