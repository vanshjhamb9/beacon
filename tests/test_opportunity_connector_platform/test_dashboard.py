"""Tests for connector dashboard."""

from __future__ import annotations

import pytest

from opportunity_connector_platform.connector_dashboard import ConnectorDashboard


class TestConnectorDashboard:
    def test_cards_empty(self):
        d = ConnectorDashboard()
        assert d.cards([]) == []

    def test_cards_with_data(self):
        d = ConnectorDashboard()
        rows = [
            {
                "connector_id": "c1",
                "status": "healthy",
                "signals": 100,
                "accepted": 80,
                "revenue_ready": 10,
                "meetings": 5,
                "won": 2,
                "revenue": 1000,
                "health": "healthy",
                "failure_rate": 5.0,
            }
        ]
        cards = d.cards(rows)
        assert len(cards) == 1
        assert cards[0]["connector"] == "c1"
        assert cards[0]["status"] == "healthy"
        assert cards[0]["signals_today"] == 100
        assert cards[0]["accepted"] == 80

    def test_cards_multiple(self):
        d = ConnectorDashboard()
        rows = [
            {"connector_id": "c1", "signals": 100, "accepted": 50, "revenue_ready": 5, "meetings": 2, "won": 1, "revenue": 500, "failure_rate": 10},
            {"connector_id": "c2", "signals": 200, "accepted": 150, "revenue_ready": 20, "meetings": 10, "won": 3, "revenue": 2000, "failure_rate": 5},
        ]
        cards = d.cards(rows)
        assert len(cards) == 2

    def test_details_empty(self):
        d = ConnectorDashboard()
        result = d.details("c1", [])
        assert result["connector_id"] == "c1"
        assert result["events_timeline"] == []

    def test_details_with_events(self):
        d = ConnectorDashboard()
        rows = [
            {"connector_id": "c1", "event_type": "Hiring", "company_name": "Acme"},
            {"connector_id": "c1", "event_type": "Funding", "company_name": "Acme"},
        ]
        result = d.details("c1", rows)
        assert len(result["events_timeline"]) == 2
        assert "Hiring" in result["top_event_types"]

    def test_operations_center_section_empty(self):
        d = ConnectorDashboard()
        result = d.operations_center_section([])
        assert result["section"] == "Opportunity Connector Platform"
        assert result["live_connectors"] == 0

    def test_operations_center_section_with_data(self):
        d = ConnectorDashboard()
        rows = [
            {"connector_id": "c1", "enabled": True, "signals": 1000, "accepted": 500, "revenue": 10000, "failures": 5},
            {"connector_id": "c2", "enabled": False, "signals": 0, "accepted": 0, "revenue": 0, "failures": 0},
        ]
        result = d.operations_center_section(rows)
        assert result["live_connectors"] == 1
        assert result["acceptance"] == 50.0
        assert "c2" in result["disabled_sources"]

    def test_cards_roi_action_keep(self):
        d = ConnectorDashboard()
        rows = [{"connector_id": "c1", "signals": 100, "accepted": 80, "revenue_ready": 10, "meetings": 5, "won": 2, "revenue": 10000, "failure_rate": 5}]
        cards = d.cards(rows)
        assert cards[0]["roi_action"] == "keep_enabled"

    def test_cards_roi_action_disable(self):
        d = ConnectorDashboard()
        rows = [{"connector_id": "c1", "signals": 100, "accepted": 2, "revenue_ready": 0, "meetings": 0, "won": 0, "revenue": 0, "failure_rate": 60}]
        cards = d.cards(rows)
        assert cards[0]["roi_action"] == "disable_review"

    def test_operations_center_signals_per_sec(self):
        d = ConnectorDashboard()
        rows = [{"connector_id": "c1", "enabled": True, "signals": 86400, "accepted": 0, "revenue": 0, "failures": 0}]
        result = d.operations_center_section(rows)
        assert result["signals_per_sec"] == 1.0

    def test_operations_center_no_signals(self):
        d = ConnectorDashboard()
        rows = [{"connector_id": "c1", "enabled": True, "signals": 0, "accepted": 0, "revenue": 0, "failures": 0}]
        result = d.operations_center_section(rows)
        assert result["acceptance"] == 0.0
