"""Tests for ActivityEngine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from discovery_quality_engine.activity_engine import ActivityEngine, ActivityEvidence, ActivityResult
from discovery_quality_engine.quality_engine import QualityDecision, QualityGate, RejectionReason


class TestActivityEngine:
    def setup_method(self) -> None:
        self.engine = ActivityEngine()

    def test_no_evidence_rejected(self) -> None:
        result = self.engine.evaluate([], now=datetime.now(UTC))
        assert result.decision == QualityDecision.REJECT
        assert "NO_RECENT_ACTIVITY" in result.reasons
        assert result.activity_count == 0

    def test_none_evidence_rejected(self) -> None:
        result = self.engine.evaluate(None, now=datetime.now(UTC))
        assert result.decision == QualityDecision.REJECT

    def test_recent_evidence_accepted(self) -> None:
        now = datetime.now(UTC)
        evidence = [
            ActivityEvidence(
                activity_type="HIRING",
                timestamp=now - timedelta(days=5),
                source="linkedin",
                title="Hiring SDRs",
            ),
        ]
        result = self.engine.evaluate(evidence, now=now)
        assert result.decision == QualityDecision.ACCEPT
        assert result.activity_count == 1

    def test_old_evidence_rejected(self) -> None:
        now = datetime.now(UTC)
        evidence = [
            ActivityEvidence(
                activity_type="HIRING",
                timestamp=now - timedelta(days=100),
                source="linkedin",
                title="Old hiring post",
            ),
        ]
        result = self.engine.evaluate(evidence, now=now)
        assert result.decision == QualityDecision.REJECT
        assert result.activity_count == 0

    def test_mixed_old_and_recent(self) -> None:
        now = datetime.now(UTC)
        evidence = [
            ActivityEvidence(
                activity_type="HIRING",
                timestamp=now - timedelta(days=5),
                source="linkedin",
                title="Recent",
            ),
            ActivityEvidence(
                activity_type="FUNDING",
                timestamp=now - timedelta(days=200),
                source="crunchbase",
                title="Old",
            ),
        ]
        result = self.engine.evaluate(evidence, now=now)
        assert result.decision == QualityDecision.ACCEPT
        assert result.activity_count == 1

    def test_multiple_recent_evidence(self) -> None:
        now = datetime.now(UTC)
        evidence = [
            ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a"),
            ActivityEvidence(activity_type="FUNDING", timestamp=now - timedelta(days=7), source="b", title="b"),
            ActivityEvidence(activity_type="EXPANSION", timestamp=now - timedelta(days=14), source="c", title="c"),
        ]
        result = self.engine.evaluate(evidence, now=now)
        assert result.decision == QualityDecision.ACCEPT
        assert result.activity_count == 3

    def test_gate_name(self) -> None:
        assert self.engine.gate_name() == QualityGate.ACTIVITY_CHECK.value

    def test_custom_min_signals(self) -> None:
        engine = ActivityEngine(min_signals=3)
        now = datetime.now(UTC)
        evidence = [
            ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a"),
            ActivityEvidence(activity_type="FUNDING", timestamp=now - timedelta(days=7), source="b", title="b"),
        ]
        result = engine.evaluate(evidence, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_custom_max_age_days(self) -> None:
        engine = ActivityEngine(max_age_days=10)
        now = datetime.now(UTC)
        evidence = [
            ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=15), source="a", title="a"),
        ]
        result = engine.evaluate(evidence, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_naive_timestamp_handled(self) -> None:
        now = datetime.now(UTC)
        evidence = [
            ActivityEvidence(activity_type="HIRING", timestamp=datetime(2026, 7, 20), source="a", title="a"),
        ]
        result = self.engine.evaluate(evidence, now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_exact_boundary(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        evidence = [
            ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=90), source="a", title="a"),
        ]
        result = self.engine.evaluate(evidence, now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_one_day_over_boundary(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        evidence = [
            ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=91), source="a", title="a"),
        ]
        result = self.engine.evaluate(evidence, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_result_has_reasons(self) -> None:
        result = self.engine.evaluate([], now=datetime.now(UTC))
        assert isinstance(result.reasons, tuple)
