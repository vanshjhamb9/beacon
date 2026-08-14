"""Tests for OutcomeTracker."""

from __future__ import annotations

import pytest

from validation_engine.outcome_tracker import OutcomeTracker


class TestOutcomeTrackerRecordOutcome:
    def test_record_valid_outcome(self, outcome_tracker: OutcomeTracker) -> None:
        event = outcome_tracker.record_outcome("company_1", "won", revenue=50000.0)
        assert event.company_id == "company_1"
        assert event.status == "won"
        assert event.revenue == 50000.0

    def test_record_invalid_status_raises(self, outcome_tracker: OutcomeTracker) -> None:
        with pytest.raises(ValueError, match="Invalid status"):
            outcome_tracker.record_outcome("company_1", "invalid")

    def test_record_with_service_sold(self, outcome_tracker: OutcomeTracker) -> None:
        event = outcome_tracker.record_outcome("company_1", "won", service_sold="ai_automation")
        assert event.service_sold == "ai_automation"

    def test_record_with_reason(self, outcome_tracker: OutcomeTracker) -> None:
        event = outcome_tracker.record_outcome("company_1", "lost", reason="Too expensive")
        assert event.reason == "Too expensive"


class TestOutcomeTrackerGetOutcome:
    def test_get_outcome_empty(self, outcome_tracker: OutcomeTracker) -> None:
        outcome = outcome_tracker.get_outcome("nonexistent")
        assert outcome is None

    def test_get_outcome_latest(self, outcome_tracker: OutcomeTracker) -> None:
        outcome_tracker.record_outcome("company_1", "won")
        outcome = outcome_tracker.get_outcome("company_1")
        assert outcome is not None
        assert outcome.status == "won"


class TestOutcomeTrackerFilteredViews:
    def test_won_deals(self, outcome_tracker: OutcomeTracker) -> None:
        outcome_tracker.record_outcome("company_1", "won")
        outcome_tracker.record_outcome("company_2", "lost")
        won = outcome_tracker.get_won_deals()
        assert len(won) == 1

    def test_lost_deals(self, outcome_tracker: OutcomeTracker) -> None:
        outcome_tracker.record_outcome("company_1", "lost")
        lost = outcome_tracker.get_lost_deals()
        assert len(lost) == 1

    def test_paused_deals(self, outcome_tracker: OutcomeTracker) -> None:
        outcome_tracker.record_outcome("company_1", "paused")
        paused = outcome_tracker.get_paused_deals()
        assert len(paused) == 1


class TestOutcomeTrackerRevenue:
    def test_total_revenue_empty(self, outcome_tracker: OutcomeTracker) -> None:
        total = outcome_tracker.get_total_revenue()
        assert total == 0.0

    def test_total_revenue_calculated(self, outcome_tracker: OutcomeTracker) -> None:
        outcome_tracker.record_outcome("company_1", "won", revenue=50000.0)
        outcome_tracker.record_outcome("company_2", "won", revenue=75000.0)
        total = outcome_tracker.get_total_revenue()
        assert total == 125000.0

    def test_win_rate_empty(self, outcome_tracker: OutcomeTracker) -> None:
        rate = outcome_tracker.get_win_rate()
        assert rate == 0.0

    def test_win_rate_calculated(self, outcome_tracker: OutcomeTracker) -> None:
        outcome_tracker.record_outcome("company_1", "won")
        outcome_tracker.record_outcome("company_2", "lost")
        rate = outcome_tracker.get_win_rate()
        assert rate == 50.0

    def test_avg_deal_size_empty(self, outcome_tracker: OutcomeTracker) -> None:
        avg = outcome_tracker.get_avg_deal_size()
        assert avg == 0.0

    def test_avg_deal_size_calculated(self, outcome_tracker: OutcomeTracker) -> None:
        outcome_tracker.record_outcome("company_1", "won", revenue=100000.0)
        outcome_tracker.record_outcome("company_2", "won", revenue=50000.0)
        avg = outcome_tracker.get_avg_deal_size()
        assert avg == 75000.0


class TestOutcomeTrackerRevenueByService:
    def test_revenue_by_service_empty(self, outcome_tracker: OutcomeTracker) -> None:
        result = outcome_tracker.get_revenue_by_service()
        assert result == {}

    def test_revenue_by_service_calculated(self, outcome_tracker: OutcomeTracker) -> None:
        outcome_tracker.record_outcome(
            "company_1", "won",
            revenue=50000.0, service_sold="ai_automation",
        )
        outcome_tracker.record_outcome(
            "company_2", "won",
            revenue=75000.0, service_sold="crm",
        )
        outcome_tracker.record_outcome(
            "company_3", "won",
            revenue=25000.0, service_sold="ai_automation",
        )
        result = outcome_tracker.get_revenue_by_service()
        assert result["ai_automation"] == 75000.0
        assert result["crm"] == 75000.0
