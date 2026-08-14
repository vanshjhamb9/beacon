"""Tests for connector registry."""

from __future__ import annotations

import pytest

from opportunity_connector_platform.connector import NullConnector
from opportunity_connector_platform.connector_config import ConnectorConfig
from opportunity_connector_platform.registry import ConnectorRegistry, ConnectorRegistryEntry


class TestConnectorRegistryEntry:
    def test_create(self):
        entry = ConnectorRegistryEntry(
            connector_id="c1",
            name="Test",
            enabled=True,
            configured=True,
            healthy=True,
            version="1.0",
            category="Identity",
            capabilities=(),
        )
        assert entry.connector_id == "c1"

    def test_frozen(self):
        entry = ConnectorRegistryEntry(
            connector_id="c1", name="Test", enabled=True, configured=True,
            healthy=True, version="1.0", category="Identity", capabilities=(),
        )
        with pytest.raises(AttributeError):
            entry.enabled = False  # type: ignore[misc]


class TestConnectorRegistry:
    def test_register(self):
        reg = ConnectorRegistry()
        reg.register(NullConnector())
        assert reg.has("null")

    def test_register_with_config(self):
        reg = ConnectorRegistry()
        config = ConnectorConfig(connector_id="null", enabled=True)
        reg.register(NullConnector(), config)
        assert reg.has("null")
        assert reg.config("null") is not None

    def test_get(self):
        reg = ConnectorRegistry()
        reg.register(NullConnector())
        assert reg.get("null") is not None

    def test_get_nonexistent(self):
        reg = ConnectorRegistry()
        assert reg.get("nonexistent") is None

    def test_all(self):
        reg = ConnectorRegistry()
        reg.register(NullConnector())
        entries = reg.all()
        assert len(entries) == 1
        assert entries[0].connector_id == "null"

    def test_enabled(self):
        reg = ConnectorRegistry()
        config = ConnectorConfig(connector_id="null", enabled=True)
        reg.register(NullConnector(), config)
        enabled = reg.enabled()
        assert len(enabled) == 1

    def test_disabled_not_in_enabled(self):
        reg = ConnectorRegistry()
        config = ConnectorConfig(connector_id="null", enabled=False)
        reg.register(NullConnector(), config)
        enabled = reg.enabled()
        assert len(enabled) == 0

    def test_entry(self):
        reg = ConnectorRegistry()
        reg.register(NullConnector())
        entry = reg.entry("null")
        assert entry.connector_id == "null"
        assert entry.name == "Null"

    def test_ids(self):
        reg = ConnectorRegistry()
        reg.register(NullConnector())
        assert reg.ids() == ["null"]

    def test_count(self):
        reg = ConnectorRegistry()
        reg.register(NullConnector())
        assert reg.count() == 1

    def test_update_stats(self):
        reg = ConnectorRegistry()
        reg.register(NullConnector())
        reg.update_stats("null", events_today=10, events_accepted=8)
        entry = reg.entry("null")
        assert entry.events_today == 10
        assert entry.events_accepted == 8

    def test_configure(self):
        reg = ConnectorRegistry()
        reg.register(NullConnector())
        config = ConnectorConfig(connector_id="null", enabled=True)
        reg.configure(config)
        assert reg.config("null") is not None

    def test_multiple_connectors(self):
        reg = ConnectorRegistry()
        c1 = NullConnector()
        c2 = NullConnector()
        reg.register(c1)
        reg.register(c2)
        assert reg.count() == 1

    def test_category_for_entry(self):
        reg = ConnectorRegistry()
        reg.register(NullConnector())
        entry = reg.entry("null")
        assert entry.category == "Unknown"
