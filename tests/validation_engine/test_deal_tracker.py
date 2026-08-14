"""Tests for DealTracker."""

from __future__ import annotations

import pytest

from validation_engine import DEAL_STATUSES
from validation_engine.deal_tracker import DealTracker


class TestDealTrackerRecordDeal:
    def test_record_valid_deal(self, deal_tracker: DealTracker) -> None:
        event = deal_tracker.record_deal("company_1", "won", revenue=50000.0)
        assert event.company_id == "company_1"
        assert event.status == "won"
        assert event.revenue == 50000.0

    def test_record_invalid_status_raises(self, deal_tracker: DealTracker) -> None:
        with pytest.raises(ValueError, match="Invalid status"):
            deal_tracker.record_deal("company_1", "invalid")

    def test_record_all_statuses(self, deal_tracker: DealTracker) -> None:
        for status in DEAL_STATUSES:
            event = deal_tracker.record_deal("company_1", status)
            assert event.status == status

    def test_record_with_service_sold(self, deal_tracker: DealTracker) -> None:
        event = deal_tracker.record_deal("company_1", "won", service_sold="ai_automation")
        assert event.service_sold == "ai_automation"

    def test_record_with_reason(self, deal_tracker: DealTracker) -> None:
        event = deal_tracker.record_deal("company_1", "lost", reason="Too expensive")
        assert event.reason == "Too expensive"

    def test_record_with_expected_revenue(self, deal_tracker: DealTracker) -> None:
        event = deal_tracker.record_deal("company_1", "won", expected_revenue=60000.0)
        assert event.expected_revenue == 60000.0


class TestDealTrackerGetDealsForCompany:
    def test_get_empty_deals(self, deal_tracker: DealTracker) -> None:
        deals = deal_tracker.get_deals_for_company("nonexistent")
        assert deals == []

    def test_get_deals_filtered(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won")
        deal_tracker.record_deal("company_1", "lost")
        deal_tracker.record_deal("company_2", "won")
        deals = deal_tracker.get_deals_for_company("company_1")
        assert len(deals) == 2


class TestDealTrackerFilteredViews:
    def test_won_deals(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won")
        deal_tracker.record_deal("company_2", "lost")
        won = deal_tracker.get_won_deals()
        assert len(won) == 1

    def test_lost_deals(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "lost")
        lost = deal_tracker.get_lost_deals()
        assert len(lost) == 1

    def test_paused_deals(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "paused")
        paused = deal_tracker.get_paused_deals()
        assert len(paused) == 1


class TestDealTrackerRevenue:
    def test_total_revenue_empty(self, deal_tracker: DealTracker) -> None:
        total = deal_tracker.get_total_revenue()
        assert total == 0.0

    def test_total_revenue_calculated(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won", revenue=50000.0)
        deal_tracker.record_deal("company_2", "won", revenue=75000.0)
        deal_tracker.record_deal("company_3", "lost", revenue=30000.0)
        total = deal_tracker.get_total_revenue()
        assert total == 125000.0

    def test_total_expected_revenue(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won", expected_revenue=60000.0)
        deal_tracker.record_deal("company_2", "lost", expected_revenue=40000.0)
        total = deal_tracker.get_total_expected_revenue()
        assert total == 60000.0


class TestDealTrackerRates:
    def test_win_rate_empty(self, deal_tracker: DealTracker) -> None:
        rate = deal_tracker.get_win_rate()
        assert rate == 0.0

    def test_win_rate_calculated(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won")
        deal_tracker.record_deal("company_2", "lost")
        rate = deal_tracker.get_win_rate()
        assert rate == 50.0

    def test_avg_deal_size_empty(self, deal_tracker: DealTracker) -> None:
        avg = deal_tracker.get_avg_deal_size()
        assert avg == 0.0

    def test_avg_deal_size_calculated(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won", revenue=100000.0)
        deal_tracker.record_deal("company_2", "won", revenue=50000.0)
        avg = deal_tracker.get_avg_deal_size()
        assert avg == 75000.0


class TestDealTrackerRevenueByService:
    def test_revenue_by_service_empty(self, deal_tracker: DealTracker) -> None:
        result = deal_tracker.get_revenue_by_service()
        assert result == {}

    def test_revenue_by_service_calculated(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won", revenue=50000.0, service_sold="ai_automation")
        deal_tracker.record_deal("company_2", "won", revenue=75000.0, service_sold="crm")
        deal_tracker.record_deal("company_3", "won", revenue=25000.0, service_sold="ai_automation")
        result = deal_tracker.get_revenue_by_service()
        assert result["ai_automation"] == 75000.0
        assert result["crm"] == 75000.0


class TestDealTrackerDealsByStatus:
    def test_deals_by_status(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won")
        deal_tracker.record_deal("company_2", "won")
        deal_tracker.record_deal("company_3", "lost")
        counts = deal_tracker.get_deals_by_status()
        assert counts["won"] == 2
        assert counts["lost"] == 1
