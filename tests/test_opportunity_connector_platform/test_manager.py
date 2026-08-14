"""Tests for connector manager."""

from __future__ import annotations

import pytest

from opportunity_connector_platform.connector import NullConnector
from opportunity_connector_platform.connector_config import ConnectorConfig
from opportunity_connector_platform.manager import ConnectorManager
from opportunity_connector_platform.registry import ConnectorRegistry


class TestConnectorManager:
    def _make_manager(self) -> ConnectorManager:
        reg = ConnectorRegistry()
        reg.register(NullConnector(), ConnectorConfig(connector_id="null", enabled=True))
        return ConnectorManager(registry=reg)

    @pytest.mark.asyncio
    async def test_run_connector(self):
        mgr = self._make_manager()
        result = await mgr.run_connector("null")
        assert result["status"] == "completed"
        assert result["connector_id"] == "null"

    @pytest.mark.asyncio
    async def test_run_connector_not_found(self):
        mgr = self._make_manager()
        result = await mgr.run_connector("nonexistent")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_run_connector_disabled(self):
        reg = ConnectorRegistry()
        reg.register(NullConnector(), ConnectorConfig(connector_id="null", enabled=False))
        mgr = ConnectorManager(registry=reg)
        result = await mgr.run_connector("null")
        assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_run_all(self):
        mgr = self._make_manager()
        results = await mgr.run_all()
        assert len(results) == 1
        assert results[0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_run_all_empty(self):
        mgr = ConnectorManager()
        results = await mgr.run_all()
        assert results == []

    @pytest.mark.asyncio
    async def test_retry_connector(self):
        mgr = self._make_manager()
        result = await mgr.retry_connector("null")
        assert result["status"] == "completed"

    def test_get_history_empty(self):
        mgr = ConnectorManager()
        assert mgr.get_history("null") == []

    def test_all_history_empty(self):
        mgr = ConnectorManager()
        assert mgr.all_history() == {}

    @pytest.mark.asyncio
    async def test_history_recorded(self):
        mgr = self._make_manager()
        await mgr.run_connector("null")
        history = mgr.get_history("null")
        assert len(history) == 1
        assert history[0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_multiple_runs_history(self):
        mgr = self._make_manager()
        await mgr.run_connector("null")
        await mgr.run_connector("null")
        history = mgr.get_history("null")
        assert len(history) == 2
