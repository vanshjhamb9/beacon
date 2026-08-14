"""Tests for ValidationDashboard."""

from __future__ import annotations

from validation_engine.validation_dashboard import ValidationDashboardService


class TestValidationDashboardServiceBuild:
    def test_build_empty_dashboard(self) -> None:
        service = ValidationDashboardService()
        dashboard = service.build()
        assert dashboard.today_replies == 0
        assert dashboard.today_meetings == 0
        assert dashboard.today_proposals == 0
        assert dashboard.today_wins == 0
        assert dashboard.today_revenue == 0.0
        assert dashboard.reply_rate == 0.0
        assert dashboard.meeting_rate == 0.0
        assert dashboard.win_rate == 0.0
        assert len(dashboard.funnel) > 0

    def test_build_dashboard_with_data(self) -> None:
        service = ValidationDashboardService()
        service.reply_tracker.record_reply("company_1", "positive")
        service.meeting_tracker.record_meeting("company_1", "completed")
        service.proposal_tracker.record_proposal("company_1", "sent")
        service.deal_tracker.record_deal("company_1", "won", revenue=100000.0)
        dashboard = service.build()
        assert dashboard.today_replies == 1
        assert dashboard.today_meetings == 1
        assert dashboard.today_proposals == 1
        assert dashboard.today_wins == 1
        assert dashboard.today_revenue == 100000.0


class TestValidationDashboardServiceToDict:
    def test_to_dict(self) -> None:
        service = ValidationDashboardService()
        dashboard = service.build()
        payload = service.to_dict(dashboard)
        assert "generated_at" in payload
        assert "today_replies" in payload
        assert "funnel" in payload
        assert isinstance(payload["generated_at"], str)
