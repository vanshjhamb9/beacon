"""Tests for ValidationEngine."""

from __future__ import annotations

from validation_engine.validation_engine import ValidationEngine


class TestValidationEngineRecordEmailSent:
    def test_record_email_sent(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_email_sent("company_1")
        assert result["ok"] is True
        assert result["stage"] == "CONTACTED"

    def test_record_email_sent_with_evidence(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_email_sent("company_1", evidence={"campaign_id": "abc"})
        assert result["ok"] is True


class TestValidationEngineRecordEmailOpened:
    def test_record_email_opened(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_email_opened("company_1")
        assert result["ok"] is True
        assert result["stage"] == "EMAIL_OPENED"


class TestValidationEngineRecordEmailClicked:
    def test_record_email_clicked(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_email_clicked("company_1")
        assert result["ok"] is True
        assert result["stage"] == "EMAIL_CLICKED"


class TestValidationEngineRecordReply:
    def test_record_positive_reply(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_reply("company_1", "positive")
        assert result["ok"] is True
        assert result["reply_type"] == "positive"

    def test_record_negative_reply(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_reply("company_1", "negative")
        assert result["ok"] is True
        assert result["reply_type"] == "negative"


class TestValidationEngineRecordMeeting:
    def test_record_scheduled_meeting(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_meeting("company_1", "scheduled")
        assert result["ok"] is True
        assert result["meeting_type"] == "scheduled"

    def test_record_completed_meeting(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_meeting("company_1", "completed", duration_minutes=45.0)
        assert result["ok"] is True


class TestValidationEngineRecordProposal:
    def test_record_sent_proposal(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_proposal("company_1", "sent", value=50000.0)
        assert result["ok"] is True
        assert result["status"] == "sent"

    def test_record_accepted_proposal(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_proposal("company_1", "accepted")
        assert result["ok"] is True


class TestValidationEngineRecordDeal:
    def test_record_won_deal(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_deal("company_1", "won", revenue=100000.0)
        assert result["ok"] is True
        assert result["revenue"] == 100000.0

    def test_record_lost_deal(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_deal("company_1", "lost", reason="Too expensive")
        assert result["ok"] is True


class TestValidationEngineGetCompanyTimeline:
    def test_get_empty_timeline(self, validation_engine: ValidationEngine) -> None:
        timeline = validation_engine.get_company_timeline("nonexistent")
        assert timeline == []

    def test_get_timeline_after_events(self, validation_engine: ValidationEngine) -> None:
        validation_engine.record_email_sent("company_1")
        validation_engine.record_reply("company_1", "positive")
        timeline = validation_engine.get_company_timeline("company_1")
        assert len(timeline) > 0


class TestValidationEngineGetFunnel:
    def test_get_funnel(self, validation_engine: ValidationEngine) -> None:
        funnel = validation_engine.get_funnel()
        assert len(funnel) > 0


class TestValidationEngineGetDashboardData:
    def test_get_dashboard_data(self, validation_engine: ValidationEngine) -> None:
        dashboard = validation_engine.get_dashboard_data()
        assert "generated_at" in dashboard
        assert "reply_rate" in dashboard
        assert "meeting_rate" in dashboard
        assert "win_rate" in dashboard
        assert "total_revenue" in dashboard
