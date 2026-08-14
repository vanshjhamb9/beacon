"""Tests for connector statistics."""

from __future__ import annotations

import pytest

from opportunity_connector_platform.connector_statistics import ConnectorStatistics


class TestConnectorStatistics:
    def test_summarize_empty(self):
        s = ConnectorStatistics()
        result = s.summarize([])
        assert result["signals"] == 0
        assert result["accepted"] == 0
        assert result["rejected"] == 0

    def test_summarize_with_events(self):
        s = ConnectorStatistics()
        events = [
            {"accepted": True, "event_type": "Hiring", "company_name": "Acme"},
            {"accepted": True, "event_type": "Funding", "company_name": "Acme"},
            {"accepted": False, "event_type": "Hiring", "company_name": "Beta"},
        ]
        result = s.summarize(events)
        assert result["signals"] == 3
        assert result["accepted"] == 2
        assert result["rejected"] == 1
        assert result["acceptance_rate"] == 66.67

    def test_top_event_types(self):
        s = ConnectorStatistics()
        events = [
            {"accepted": True, "event_type": "Hiring", "company_name": "Acme"},
            {"accepted": True, "event_type": "Hiring", "company_name": "Beta"},
            {"accepted": True, "event_type": "Funding", "company_name": "Gamma"},
        ]
        result = s.summarize(events)
        assert result["top_event_types"]["Hiring"] == 2
        assert result["top_event_types"]["Funding"] == 1

    def test_top_companies(self):
        s = ConnectorStatistics()
        events = [
            {"accepted": True, "event_type": "Hiring", "company_name": "Acme"},
            {"accepted": True, "event_type": "Hiring", "company_name": "Acme"},
            {"accepted": True, "event_type": "Funding", "company_name": "Beta"},
        ]
        result = s.summarize(events)
        assert result["top_companies"]["Acme"] == 2
        assert result["top_companies"]["Beta"] == 1

    def test_top_rejections(self):
        s = ConnectorStatistics()
        events = [
            {"accepted": False, "rejection_reason": "missing_company"},
            {"accepted": False, "rejection_reason": "missing_company"},
            {"accepted": False, "rejection_reason": "low_confidence"},
        ]
        result = s.summarize(events)
        assert result["top_rejections"]["missing_company"] == 2
        assert result["top_rejections"]["low_confidence"] == 1

    def test_top_connectors(self):
        s = ConnectorStatistics()
        events = [
            {"connector_id": "c1", "accepted": True},
            {"connector_id": "c1", "accepted": True},
            {"connector_id": "c2", "accepted": True},
        ]
        result = s.summarize(events)
        assert result["top_connectors"]["c1"] == 2
        assert result["top_connectors"]["c2"] == 1

    def test_by_connector(self):
        s = ConnectorStatistics()
        events = [
            {"connector_id": "c1", "accepted": True, "event_type": "Hiring"},
            {"connector_id": "c2", "accepted": False, "event_type": "Funding"},
        ]
        result = s.by_connector(events)
        assert "c1" in result
        assert "c2" in result
        assert result["c1"]["signals"] == 1
        assert result["c2"]["signals"] == 1

    def test_by_event_type(self):
        s = ConnectorStatistics()
        events = [
            {"connector_id": "c1", "accepted": True, "event_type": "Hiring"},
            {"connector_id": "c1", "accepted": True, "event_type": "Hiring"},
            {"connector_id": "c2", "accepted": True, "event_type": "Funding"},
        ]
        result = s.by_event_type(events)
        assert result["Hiring"]["signals"] == 2
        assert result["Funding"]["signals"] == 1

    def test_empty_events_by_connector(self):
        s = ConnectorStatistics()
        result = s.by_connector([])
        assert result == {}

    def test_empty_events_by_event_type(self):
        s = ConnectorStatistics()
        result = s.by_event_type([])
        assert result == {}

    def test_summarize_defaults(self):
        s = ConnectorStatistics()
        events = [{"accepted": True}, {"accepted": False}]
        result = s.summarize(events)
        assert result["signals"] == 2
        assert result["accepted"] == 1
        assert result["rejected"] == 1
        assert result["acceptance_rate"] == 50.0

    def test_acceptance_rate_all_rejected(self):
        s = ConnectorStatistics()
        events = [{"accepted": False}, {"accepted": False}]
        result = s.summarize(events)
        assert result["acceptance_rate"] == 0.0

    def test_acceptance_rate_all_accepted(self):
        s = ConnectorStatistics()
        events = [{"accepted": True}, {"accepted": True}]
        result = s.summarize(events)
        assert result["acceptance_rate"] == 100.0
