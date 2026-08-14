"""Tests for ValidationMetrics."""

from __future__ import annotations

from validation_engine.validation_metrics import ValidationMetrics


class TestValidationMetricsGetAllMetrics:
    def test_empty_metrics(self) -> None:
        metrics = ValidationMetrics()
        result = metrics.get_all_metrics()
        assert "total_revenue" in result
        assert "win_rate" in result
        assert "reply_rate" in result
        assert "meeting_rate" in result
        assert "proposal_rate" in result
        assert "funnel_summary" in result
        assert result["total_revenue"] == 0.0
        assert result["win_rate"] == 0.0

    def test_metrics_with_data(self) -> None:
        metrics = ValidationMetrics()
        metrics.reply_tracker.record_reply("company_1", "positive")
        metrics.meeting_tracker.record_meeting("company_1", "completed")
        metrics.proposal_tracker.record_proposal("company_1", "sent")
        metrics.deal_tracker.record_deal("company_1", "won", revenue=100000.0)
        result = metrics.get_all_metrics()
        assert result["total_revenue"] == 100000.0
        assert result["total_won"] == 1
        assert result["total_replies"] == 1
        assert result["total_meetings_completed"] == 1
        assert result["total_proposals_sent"] == 1

    def test_metrics_reply_distribution(self) -> None:
        metrics = ValidationMetrics()
        metrics.reply_tracker.record_reply("company_1", "positive")
        metrics.reply_tracker.record_reply("company_2", "negative")
        metrics.reply_tracker.record_reply("company_3", "positive")
        result = metrics.get_all_metrics()
        assert result["reply_type_distribution"]["positive"] == 2
        assert result["reply_type_distribution"]["negative"] == 1

    def test_metrics_meeting_distribution(self) -> None:
        metrics = ValidationMetrics()
        metrics.meeting_tracker.record_meeting("company_1", "completed")
        metrics.meeting_tracker.record_meeting("company_2", "cancelled")
        result = metrics.get_all_metrics()
        assert result["meeting_type_distribution"]["completed"] == 1
        assert result["meeting_type_distribution"]["cancelled"] == 1

    def test_metrics_proposal_distribution(self) -> None:
        metrics = ValidationMetrics()
        metrics.proposal_tracker.record_proposal("company_1", "sent")
        metrics.proposal_tracker.record_proposal("company_2", "accepted")
        result = metrics.get_all_metrics()
        assert result["proposal_status_distribution"]["sent"] == 1
        assert result["proposal_status_distribution"]["accepted"] == 1

    def test_metrics_deal_distribution(self) -> None:
        metrics = ValidationMetrics()
        metrics.deal_tracker.record_deal("company_1", "won")
        metrics.deal_tracker.record_deal("company_2", "lost")
        result = metrics.get_all_metrics()
        assert result["deal_status_distribution"]["won"] == 1
        assert result["deal_status_distribution"]["lost"] == 1
