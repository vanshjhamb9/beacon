"""Tests for SignalFilter."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from discovery_quality_engine.signal_filter import SignalFilter, SignalFilterResult
from discovery_quality_engine.quality_engine import QualityDecision, QualityGate, RejectionReason


class TestSignalFilter:
    def setup_method(self) -> None:
        self.filter = SignalFilter()

    def test_valid_signal(self) -> None:
        result = self.filter.evaluate(
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring SDRs",
            signal_timestamp=datetime.now(UTC),
        )
        assert result.decision == QualityDecision.ACCEPT

    def test_missing_signal_type(self) -> None:
        result = self.filter.evaluate(
            signal_type=None,
            signal_source="linkedin",
            signal_title="Title",
            signal_timestamp=datetime.now(UTC),
        )
        assert result.decision == QualityDecision.REJECT
        assert "Missing signal type" in result.reasons

    def test_empty_signal_type(self) -> None:
        result = self.filter.evaluate(
            signal_type="",
            signal_source="linkedin",
            signal_title="Title",
            signal_timestamp=datetime.now(UTC),
        )
        assert result.decision == QualityDecision.REJECT

    def test_missing_signal_source(self) -> None:
        result = self.filter.evaluate(
            signal_type="HIRING",
            signal_source=None,
            signal_title="Title",
            signal_timestamp=datetime.now(UTC),
        )
        assert result.decision == QualityDecision.REJECT
        assert "Missing signal source" in result.reasons

    def test_empty_signal_source(self) -> None:
        result = self.filter.evaluate(
            signal_type="HIRING",
            signal_source="",
            signal_title="Title",
            signal_timestamp=datetime.now(UTC),
        )
        assert result.decision == QualityDecision.REJECT

    def test_missing_signal_title(self) -> None:
        result = self.filter.evaluate(
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title=None,
            signal_timestamp=datetime.now(UTC),
        )
        assert result.decision == QualityDecision.REJECT
        assert "Missing signal title" in result.reasons

    def test_empty_signal_title(self) -> None:
        result = self.filter.evaluate(
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="",
            signal_timestamp=datetime.now(UTC),
        )
        assert result.decision == QualityDecision.REJECT

    def test_missing_timestamp(self) -> None:
        result = self.filter.evaluate(
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Title",
            signal_timestamp=None,
        )
        assert result.decision == QualityDecision.REJECT
        assert "Missing signal timestamp" in result.reasons

    def test_future_timestamp_rejected(self) -> None:
        result = self.filter.evaluate(
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Title",
            signal_timestamp=datetime.now(UTC) + timedelta(days=1),
        )
        assert result.decision == QualityDecision.REJECT
        assert "future" in result.reasons[0].lower()

    def test_naive_timestamp_handled(self) -> None:
        result = self.filter.evaluate(
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Title",
            signal_timestamp=datetime(2026, 7, 29),
        )
        assert result.decision == QualityDecision.ACCEPT

    def test_gate_name(self) -> None:
        assert self.filter.gate_name() == "SIGNAL_DATA_INTEGRITY"

    def test_rejection_includes_unknown(self) -> None:
        result = self.filter.evaluate(
            signal_type=None,
            signal_source=None,
            signal_title=None,
            signal_timestamp=None,
        )
        assert RejectionReason.UNKNOWN.value in result.reasons
