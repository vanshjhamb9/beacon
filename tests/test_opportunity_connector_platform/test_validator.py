"""Tests for signal validator."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from opportunity_connector_platform.connector_events import EvidenceEvent
from opportunity_connector_platform.signal_validator import (
    MAX_EVENT_AGE_DAYS,
    MIN_CONFIDENCE,
    SUPPORTED_LANGUAGES,
    SignalValidator,
    ValidationResult,
)


def _make_event(**overrides: object) -> EvidenceEvent:
    now = datetime.now(UTC)
    defaults = dict(
        connector_id="test",
        connector_version="1.0",
        company_name="Acme Corp",
        headline="Acme hiring engineers",
        summary="Acme is expanding",
        event_type="Hiring",
        event_category="Identity",
        url="https://example.com/news/1",
        published_at=now,
        captured_at=now,
        country="US",
        language="en",
        confidence=85.0,
        evidence="Acme Corp is hiring 50 engineers",
        collector="test",
    )
    defaults.update(overrides)
    return EvidenceEvent(**defaults)


class TestValidationResult:
    def test_accepted(self):
        r = ValidationResult(accepted=True)
        assert r.accepted is True
        assert r.reason == "accepted"

    def test_rejected(self):
        r = ValidationResult(accepted=False, reason="missing_company")
        assert r.accepted is False
        assert r.reason == "missing_company"

    def test_frozen(self):
        r = ValidationResult(accepted=True)
        with pytest.raises(AttributeError):
            r.accepted = False  # type: ignore[misc]


class TestSignalValidator:
    def test_valid_event_accepted(self):
        v = SignalValidator()
        event = _make_event()
        result = v.validate(event)
        assert result.accepted is True

    def test_missing_company(self):
        v = SignalValidator()
        event = _make_event(company_name=None)
        result = v.validate(event)
        assert result.accepted is False
        assert result.reason == "missing_company"

    def test_empty_company(self):
        v = SignalValidator()
        event = _make_event(company_name="")
        result = v.validate(event)
        assert result.accepted is False
        assert result.reason == "missing_company"

    def test_whitespace_company(self):
        v = SignalValidator()
        event = _make_event(company_name="   ")
        result = v.validate(event)
        assert result.accepted is False
        assert result.reason == "missing_company"

    def test_missing_url(self):
        v = SignalValidator()
        event = _make_event(url=None)
        result = v.validate(event)
        assert result.accepted is False
        assert result.reason == "missing_url"

    def test_empty_url(self):
        v = SignalValidator()
        event = _make_event(url="")
        result = v.validate(event)
        assert result.accepted is False
        assert result.reason == "missing_url"

    def test_duplicate_evidence(self):
        v = SignalValidator()
        event = _make_event()
        v.validate(event)
        result = v.validate(_make_event())
        assert result.accepted is False
        assert result.reason == "duplicate_evidence"

    def test_different_url_not_duplicate(self):
        v = SignalValidator()
        e1 = _make_event(url="https://example.com/1")
        e2 = _make_event(url="https://example.com/2")
        assert v.validate(e1).accepted is True
        assert v.validate(e2).accepted is True

    def test_expired_event(self):
        v = SignalValidator()
        old_date = datetime.now(UTC) - timedelta(days=MAX_EVENT_AGE_DAYS + 1)
        event = _make_event(published_at=old_date)
        result = v.validate(event)
        assert result.accepted is False
        assert result.reason == "expired"

    def test_event_at_boundary_not_expired(self):
        v = SignalValidator()
        boundary_date = datetime.now(UTC) - timedelta(days=MAX_EVENT_AGE_DAYS - 1)
        event = _make_event(published_at=boundary_date)
        result = v.validate(event)
        assert result.accepted is True

    def test_unsupported_language(self):
        v = SignalValidator()
        event = _make_event(language="fr")
        result = v.validate(event)
        assert result.accepted is False
        assert result.reason == "unsupported_language"

    def test_unsupported_event_type(self):
        v = SignalValidator()
        event = _make_event(event_type="InvalidType")
        result = v.validate(event)
        assert result.accepted is False
        assert result.reason == "unsupported_source"

    def test_low_confidence(self):
        v = SignalValidator()
        event = _make_event(confidence=MIN_CONFIDENCE - 1)
        result = v.validate(event)
        assert result.accepted is False
        assert result.reason == "low_confidence"

    def test_confidence_at_boundary(self):
        v = SignalValidator()
        event = _make_event(confidence=MIN_CONFIDENCE)
        result = v.validate(event)
        assert result.accepted is True

    def test_malformed_empty_headline(self):
        v = SignalValidator()
        now = datetime.now(UTC)
        with pytest.raises(Exception):
            EvidenceEvent(
                connector_id="test", connector_version="1.0",
                company_name="Acme", headline="",
                event_type="Hiring", event_category="Identity",
                published_at=now, captured_at=now,
                evidence="e", collector="test",
            )

    def test_malformed_empty_evidence(self):
        v = SignalValidator()
        now = datetime.now(UTC)
        with pytest.raises(Exception):
            EvidenceEvent(
                connector_id="test", connector_version="1.0",
                company_name="Acme", headline="h",
                event_type="Hiring", event_category="Identity",
                published_at=now, captured_at=now,
                evidence="", collector="test",
            )

    def test_whitespace_headline_rejected(self):
        v = SignalValidator()
        event = _make_event(headline="   ")
        result = v.validate(event)
        assert result.accepted is False
        assert result.reason == "malformed"

    def test_whitespace_evidence_rejected(self):
        v = SignalValidator()
        event = _make_event(evidence="   ")
        result = v.validate(event)
        assert result.accepted is False
        assert result.reason == "malformed"

    def test_reset_clears_seen(self):
        v = SignalValidator()
        event = _make_event()
        v.validate(event)
        assert v.seen_count() == 1
        v.reset()
        assert v.seen_count() == 0

    def test_seen_count_increments(self):
        v = SignalValidator()
        assert v.seen_count() == 0
        v.validate(_make_event(url="https://a.com/1"))
        assert v.seen_count() == 1
        v.validate(_make_event(url="https://a.com/2"))
        assert v.seen_count() == 2

    def test_now_override(self):
        v = SignalValidator()
        event = _make_event(published_at=datetime(2020, 1, 1, tzinfo=UTC))
        result = v.validate(event, now=datetime(2025, 1, 1, tzinfo=UTC))
        assert result.accepted is False
        assert result.reason == "expired"

    def test_all_event_types_accepted(self):
        from opportunity_connector_platform.connector_events import SUPPORTED_EVENT_TYPES
        v = SignalValidator()
        for i, etype in enumerate(SUPPORTED_EVENT_TYPES):
            v.reset()
            event = _make_event(
                url=f"https://example.com/{i}",
                headline=f"headline {i}",
                event_type=etype,
            )
            result = v.validate(event)
            assert result.accepted is True, f"Event type {etype} should be accepted"

    def test_default_language_accepted(self):
        v = SignalValidator()
        event = _make_event(language="unknown")
        result = v.validate(event)
        assert result.accepted is True

    def test_en_language_accepted(self):
        v = SignalValidator()
        event = _make_event(language="en")
        result = v.validate(event)
        assert result.accepted is True

    def test_high_confidence_accepted(self):
        v = SignalValidator()
        event = _make_event(confidence=100.0)
        result = v.validate(event)
        assert result.accepted is True

    def test_nine_nine_rejected(self):
        v = SignalValidator()
        event = _make_event(headline="valid headline", evidence="valid evidence", confidence=39.0)
        result = v.validate(event)
        assert result.accepted is False
        assert result.reason == "low_confidence"

    def test_multiple_rejections_same_event(self):
        v = SignalValidator()
        event = _make_event(company_name=None, url=None)
        result = v.validate(event)
        assert result.accepted is False
        assert result.reason == "missing_company"
