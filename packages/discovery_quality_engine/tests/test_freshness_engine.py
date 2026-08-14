"""Tests for FreshnessEngine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from discovery_quality_engine.freshness_engine import FreshnessEngine, FreshnessResult
from discovery_quality_engine.quality_engine import QualityDecision, QualityGate


class TestFreshnessEngine:
    def setup_method(self) -> None:
        self.engine = FreshnessEngine()

    def test_fresh_hiring_signal(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=5)
        result = self.engine.evaluate("HIRING", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT
        assert result.age_days == 5
        assert result.max_age_days == 30

    def test_stale_hiring_signal(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=45)
        result = self.engine.evaluate("HIRING", ts, now=now)
        assert result.decision == QualityDecision.REJECT
        assert result.age_days == 45
        assert "STALE_SIGNAL" in result.reasons

    def test_fresh_funding_signal(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=60)
        result = self.engine.evaluate("FUNDING", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_stale_funding_signal(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=100)
        result = self.engine.evaluate("FUNDING", ts, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_fresh_product_launch(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=10)
        result = self.engine.evaluate("PRODUCT_LAUNCH", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_stale_product_launch(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=35)
        result = self.engine.evaluate("PRODUCT_LAUNCH", ts, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_fresh_technology_adoption(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=30)
        result = self.engine.evaluate("TECHNOLOGY_ADOPTION", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_stale_technology_adoption(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=65)
        result = self.engine.evaluate("TECHNOLOGY_ADOPTION", ts, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_fresh_partnership(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=20)
        result = self.engine.evaluate("PARTNERSHIP", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_stale_partnership(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=50)
        result = self.engine.evaluate("PARTNERSHIP", ts, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_fresh_expansion(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=45)
        result = self.engine.evaluate("EXPANSION", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_stale_expansion(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=95)
        result = self.engine.evaluate("EXPANSION", ts, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_fresh_conference(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=10)
        result = self.engine.evaluate("CONFERENCE", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_stale_conference(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=20)
        result = self.engine.evaluate("CONFERENCE", ts, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_fresh_award(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=15)
        result = self.engine.evaluate("AWARD", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_stale_award(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=35)
        result = self.engine.evaluate("AWARD", ts, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_fresh_press_release(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=25)
        result = self.engine.evaluate("PRESS_RELEASE", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_stale_press_release(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=40)
        result = self.engine.evaluate("PRESS_RELEASE", ts, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_unknown_signal_type_uses_default_90d(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=50)
        result = self.engine.evaluate("UNKNOWN_TYPE", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT
        assert result.max_age_days == 90

    def test_unknown_signal_type_stale(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=100)
        result = self.engine.evaluate("UNKNOWN_TYPE", ts, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_naive_timestamp_handled(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = datetime(2026, 7, 20)
        result = self.engine.evaluate("HIRING", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_same_day(self) -> None:
        now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
        ts = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)
        result = self.engine.evaluate("HIRING", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT
        assert result.age_days == 0

    def test_boundary_exact_limit(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=30)
        result = self.engine.evaluate("HIRING", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_boundary_one_over_limit(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=31)
        result = self.engine.evaluate("HIRING", ts, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_case_insensitive_signal_type(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=5)
        result = self.engine.evaluate("hiring", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_gate_name(self) -> None:
        assert self.engine.gate_name() == QualityGate.FRESHNESS.value

    def test_custom_limits(self) -> None:
        from discovery_quality_engine.quality_engine import FreshnessLimit

        custom = [FreshnessLimit(signal_type="HIRING", max_age_days=7)]
        engine = FreshnessEngine(limits=custom)
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=5)
        result = engine.evaluate("HIRING", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT
        assert result.max_age_days == 7

    def test_custom_limits_exceeded(self) -> None:
        from discovery_quality_engine.quality_engine import FreshnessLimit

        custom = [FreshnessLimit(signal_type="HIRING", max_age_days=7)]
        engine = FreshnessEngine(limits=custom)
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=10)
        result = engine.evaluate("HIRING", ts, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_reasons_include_rejection_reason_enum(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=50)
        result = self.engine.evaluate("HIRING", ts, now=now)
        assert any("STALE_SIGNAL" in r for r in result.reasons)

    def test_accept_reasons_descriptive(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=5)
        result = self.engine.evaluate("HIRING", ts, now=now)
        assert any("within limit" in r.lower() for r in result.reasons)
