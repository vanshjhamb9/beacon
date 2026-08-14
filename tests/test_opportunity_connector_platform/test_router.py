"""Tests for connector router (high-level)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from opportunity_connector_platform.connector import NullConnector
from opportunity_connector_platform.connector_config import ConnectorConfig
from opportunity_connector_platform.connector_events import EvidenceEvent
from opportunity_connector_platform.router import ConnectorRouter


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


class TestConnectorRouter:
    def test_register(self):
        r = ConnectorRouter()
        r.register(NullConnector())
        assert r.registry.has("null")

    def test_register_with_config(self):
        r = ConnectorRouter()
        config = ConnectorConfig(connector_id="null", enabled=True)
        r.register(NullConnector(), config)
        assert r.registry.has("null")

    def test_configure(self):
        r = ConnectorRouter()
        r.register(NullConnector())
        config = ConnectorConfig(connector_id="null", enabled=True)
        r.configure(config)
        assert r.registry.config("null") is not None

    @pytest.mark.asyncio
    async def test_route_event(self):
        r = ConnectorRouter()
        event = _make_event()
        result = await r.route_event(event)
        assert result["accepted"] is True
        assert result["connector_id"] == "test"

    @pytest.mark.asyncio
    async def test_route_event_rejected(self):
        r = ConnectorRouter()
        event = _make_event(company_name=None)
        result = await r.route_event(event)
        assert result["accepted"] is False
        assert result["rejection_reason"] == "missing_company"

    @pytest.mark.asyncio
    async def test_route_batch(self):
        r = ConnectorRouter()
        events = [_make_event(url=f"https://example.com/{i}") for i in range(3)]
        result = await r.route_batch(events)
        assert result["total"] == 3
        assert result["accepted"] == 3
        assert result["rejected"] == 0

    @pytest.mark.asyncio
    async def test_route_batch_mixed(self):
        r = ConnectorRouter()
        events = [
            _make_event(url="https://example.com/1"),
            _make_event(url=None),
        ]
        result = await r.route_batch(events)
        assert result["accepted"] == 1
        assert result["rejected"] == 1

    @pytest.mark.asyncio
    async def test_run_connector(self):
        r = ConnectorRouter()
        r.register(NullConnector(), ConnectorConfig(connector_id="null", enabled=True))
        result = await r.run_connector("null")
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_run_all(self):
        r = ConnectorRouter()
        r.register(NullConnector(), ConnectorConfig(connector_id="null", enabled=True))
        results = await r.run_all()
        assert len(results) == 1

    def test_registry_entries(self):
        r = ConnectorRouter()
        r.register(NullConnector())
        entries = r.registry_entries()
        assert len(entries) == 1
        assert entries[0]["connector_id"] == "null"
