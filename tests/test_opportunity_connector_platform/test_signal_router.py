"""Tests for signal router."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from opportunity_connector_platform.connector_events import EvidenceEvent
from opportunity_connector_platform.signal_router import SignalRouter


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
        evidence="Acme Corp is hiring",
        collector="test",
    )
    defaults.update(overrides)
    return EvidenceEvent(**defaults)


class TestSignalRouter:
    def test_route_valid_event(self):
        router = SignalRouter()
        event = _make_event()
        routed = router.route(event)
        assert routed.accepted is True
        assert routed.rejection_reason is None

    def test_route_missing_company(self):
        router = SignalRouter()
        event = _make_event(company_name=None)
        routed = router.route(event)
        assert routed.accepted is False
        assert routed.rejection_reason == "missing_company"

    def test_route_missing_url(self):
        router = SignalRouter()
        event = _make_event(url=None)
        routed = router.route(event)
        assert routed.accepted is False
        assert routed.rejection_reason == "missing_url"

    def test_route_low_confidence(self):
        router = SignalRouter()
        event = _make_event(confidence=10.0)
        routed = router.route(event)
        assert routed.accepted is False
        assert routed.rejection_reason == "low_confidence"

    def test_route_batch(self):
        router = SignalRouter()
        events = [_make_event(url=f"https://example.com/{i}") for i in range(5)]
        routed = router.route_batch(events)
        assert len(routed) == 5

    def test_route_batch_mixed(self):
        router = SignalRouter()
        events = [
            _make_event(url="https://example.com/1"),
            _make_event(url=None),
        ]
        routed = router.route_batch(events)
        accepted = sum(1 for r in routed if r.accepted)
        rejected = sum(1 for r in routed if not r.accepted)
        assert accepted == 1
        assert rejected == 1

    def test_accepted_count(self):
        router = SignalRouter()
        events = [_make_event(url=f"https://example.com/{i}") for i in range(3)]
        routed = router.route_batch(events)
        assert router.accepted_count(routed) == 3

    def test_rejected_count(self):
        router = SignalRouter()
        events = [_make_event(url=None) for _ in range(3)]
        routed = router.route_batch(events)
        assert router.rejected_count(routed) == 3

    def test_rejection_reasons(self):
        router = SignalRouter()
        events = [
            _make_event(company_name=None, url="https://a.com/1"),
            _make_event(url=None, url2="https://a.com/2"),
        ]
        routed = router.route_batch(events)
        reasons = router.rejection_reasons(routed)
        assert "missing_company" in reasons

    def test_route_preserves_event_data(self):
        router = SignalRouter()
        event = _make_event(company_name="TestCo")
        routed = router.route(event)
        assert routed.event.company_name == "TestCo"

    def test_route_normalizes_country(self):
        router = SignalRouter()
        event = _make_event(country="usa")
        routed = router.route(event)
        assert routed.event.country == "US"

    def test_route_normalizes_language(self):
        router = SignalRouter()
        event = _make_event(language="english")
        routed = router.route(event)
        assert routed.event.language == "en"

    def test_default_route(self):
        router = SignalRouter()
        event = _make_event()
        routed = router.route(event)
        assert routed.route == "live_opportunity_discovery"

    def test_empty_batch(self):
        router = SignalRouter()
        routed = router.route_batch([])
        assert routed == []
