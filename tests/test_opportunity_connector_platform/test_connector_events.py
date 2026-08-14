"""Tests for connector interface, events, and health."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from opportunity_connector_platform.connector import Connector, ConnectorHealth, NullConnector
from opportunity_connector_platform.connector_capabilities import ConnectorCapability
from opportunity_connector_platform.connector_events import EvidenceEvent, EventBatch, RoutedEvidenceEvent


def _make_event(**overrides: object) -> EvidenceEvent:
    now = datetime.now(UTC)
    defaults = dict(
        connector_id="test_connector",
        connector_version="1.0.0",
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
        raw_metadata={"source": "test"},
        collector="test",
    )
    defaults.update(overrides)
    return EvidenceEvent(**defaults)


class TestConnectorHealth:
    def test_healthy_default(self):
        h = ConnectorHealth()
        assert h.status == "healthy"

    def test_frozen(self):
        h = ConnectorHealth(status="critical")
        with pytest.raises(AttributeError):
            h.status = "healthy"  # type: ignore[misc]

    def test_all_fields(self):
        now = datetime.now(UTC)
        h = ConnectorHealth(
            status="warning",
            detail="rate limited",
            latency_ms=150.0,
            failure_rate=5.0,
            rate_limit_remaining=0,
            failures=3,
            retries=1,
            authenticated=True,
            queue_size=50,
            freshness_minutes=10,
            last_check=now,
        )
        assert h.status == "warning"
        assert h.detail == "rate limited"
        assert h.latency_ms == 150.0
        assert h.failure_rate == 5.0
        assert h.rate_limit_remaining == 0
        assert h.failures == 3
        assert h.retries == 1
        assert h.authenticated is True
        assert h.queue_size == 50
        assert h.freshness_minutes == 10
        assert h.last_check == now


class TestNullConnector:
    def test_id(self):
        assert NullConnector().id() == "null"

    def test_name(self):
        assert NullConnector().name() == "Null"

    def test_version(self):
        assert NullConnector().version() == "0.0.1"

    def test_capabilities_empty(self):
        assert NullConnector().capabilities() == ()

    def test_health_healthy(self):
        assert NullConnector().health().status == "healthy"

    @pytest.mark.asyncio
    async def test_authenticate(self):
        assert await NullConnector().authenticate() is True

    @pytest.mark.asyncio
    async def test_discover_empty(self):
        assert await NullConnector().discover() == []

    def test_normalize(self):
        event = NullConnector().normalize({"key": "value"})
        assert event.connector_id == "null"
        assert event.headline == "test"

    def test_validate(self):
        event = NullConnector().normalize({})
        assert NullConnector().validate(event) is True

    @pytest.mark.asyncio
    async def test_emit(self):
        event = NullConnector().normalize({})
        emitted = await NullConnector().emit(event)
        assert emitted.event_id == event.event_id

    @pytest.mark.asyncio
    async def test_shutdown(self):
        await NullConnector().shutdown()


class TestEvidenceEvent:
    def test_create(self):
        now = datetime.now(UTC)
        event = EvidenceEvent(
            connector_id="c1",
            connector_version="1.0",
            headline="test",
            event_type="Hiring",
            event_category="Identity",
            published_at=now,
            captured_at=now,
            evidence="test evidence",
            collector="test",
        )
        assert event.connector_id == "c1"
        assert event.event_type == "Hiring"

    def test_frozen(self):
        now = datetime.now(UTC)
        event = EvidenceEvent(
            connector_id="c1",
            connector_version="1.0",
            headline="test",
            event_type="Hiring",
            event_category="Identity",
            published_at=now,
            captured_at=now,
            evidence="test",
            collector="test",
        )
        with pytest.raises(Exception):
            event.headline = "changed"  # type: ignore[misc]

    def test_default_confidence(self):
        now = datetime.now(UTC)
        event = EvidenceEvent(
            connector_id="c1",
            connector_version="1.0",
            headline="test",
            event_type="Hiring",
            event_category="Identity",
            published_at=now,
            captured_at=now,
            evidence="test",
            collector="test",
        )
        assert event.confidence == 0.0

    def test_event_id_auto(self):
        now = datetime.now(UTC)
        e1 = EvidenceEvent(
            connector_id="c1", connector_version="1.0", headline="a",
            event_type="Hiring", event_category="Identity",
            published_at=now, captured_at=now, evidence="x", collector="t",
        )
        e2 = EvidenceEvent(
            connector_id="c1", connector_version="1.0", headline="b",
            event_type="Hiring", event_category="Identity",
            published_at=now, captured_at=now, evidence="y", collector="t",
        )
        assert e1.event_id != e2.event_id

    def test_minimal_fields(self):
        now = datetime.now(UTC)
        event = EvidenceEvent(
            connector_id="c",
            connector_version="1",
            headline="h",
            event_type="Hiring",
            event_category="Identity",
            published_at=now,
            captured_at=now,
            evidence="e",
            collector="t",
        )
        assert event.company_name is None
        assert event.url is None
        assert event.country is None
        assert event.language == "unknown"
        assert event.raw_metadata == {}

    def test_raw_metadata(self):
        now = datetime.now(UTC)
        meta = {"key": "value", "nested": {"a": 1}}
        event = EvidenceEvent(
            connector_id="c", connector_version="1", headline="h",
            event_type="Hiring", event_category="Identity",
            published_at=now, captured_at=now, evidence="e", collector="t",
            raw_metadata=meta,
        )
        assert event.raw_metadata == meta


class TestRoutedEvidenceEvent:
    def test_accepted(self):
        now = datetime.now(UTC)
        event = _make_event()
        routed = RoutedEvidenceEvent(event=event, accepted=True)
        assert routed.accepted is True
        assert routed.rejection_reason is None
        assert routed.route == "live_opportunity_discovery"

    def test_rejected(self):
        event = _make_event()
        routed = RoutedEvidenceEvent(event=event, accepted=False, rejection_reason="missing_company")
        assert routed.accepted is False
        assert routed.rejection_reason == "missing_company"

    def test_frozen(self):
        event = _make_event()
        routed = RoutedEvidenceEvent(event=event, accepted=True)
        with pytest.raises(Exception):
            routed.accepted = False  # type: ignore[misc]

    def test_routed_at_auto(self):
        event = _make_event()
        routed = RoutedEvidenceEvent(event=event, accepted=True)
        assert routed.routed_at is not None


class TestEventBatch:
    def test_create(self):
        now = datetime.now(UTC)
        batch = EventBatch(
            connector_id="c1",
            connector_version="1.0",
            total_collected=10,
            total_accepted=8,
            total_rejected=2,
        )
        assert batch.connector_id == "c1"
        assert batch.total_collected == 10

    def test_empty_events(self):
        batch = EventBatch(connector_id="c", connector_version="1")
        assert batch.events == ()
        assert batch.total_collected == 0


class TestConnectorCapability:
    def test_create(self):
        cap = ConnectorCapability(category="Identity", event_types=("Hiring",))
        assert cap.category == "Identity"
        assert cap.emits_evidence_only is True

    def test_frozen(self):
        cap = ConnectorCapability(category="Identity")
        with pytest.raises(AttributeError):
            cap.category = "Other"  # type: ignore[misc]

    def test_defaults(self):
        cap = ConnectorCapability(category="Test")
        assert cap.emits_evidence_only is True
        assert cap.supports_incremental_sync is True
        assert cap.supports_historical is False
        assert cap.max_batch_size == 100
        assert cap.requires_authentication is False
