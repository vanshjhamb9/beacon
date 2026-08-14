"""Database model tests for validation engine."""

from __future__ import annotations


class TestValidationEngineModels:
    def test_validation_engine_models_importable(self) -> None:
        from validation_engine.models import (
            ConnectorRoi,
            DailyReport,
            DealEvent,
            FunnelStage,
            IndustryRoi,
            MeetingEvent,
            MonthlyReport,
            ObjectionEvent,
            PersonaRoi,
            ProposalEvent,
            ReplyEvent,
            ServiceRoi,
            TimelineEntry,
            TriggerRoi,
            ValidationDashboard,
            ValidationEvent,
            WeeklyReport,
        )
        assert all([
            ValidationEvent, TimelineEntry, ReplyEvent, MeetingEvent,
            ProposalEvent, DealEvent, ObjectionEvent, ConnectorRoi,
            IndustryRoi, ServiceRoi, PersonaRoi, TriggerRoi, FunnelStage,
            ValidationDashboard, DailyReport, WeeklyReport, MonthlyReport,
        ])

    def test_validation_event_model_fields(self) -> None:
        from datetime import UTC, datetime

        from validation_engine.models import ValidationEvent
        event = ValidationEvent(
            event_id="evt_1",
            company_id="company_1",
            stage="REVENUE_READY",
            timestamp=datetime.now(UTC),
        )
        assert event.event_id == "evt_1"
        assert event.company_id == "company_1"
        assert event.stage == "REVENUE_READY"

    def test_timeline_entry_model_fields(self) -> None:
        from datetime import UTC, datetime

        from validation_engine.models import TimelineEntry
        entry = TimelineEntry(
            stage="REVENUE_READY",
            timestamp=datetime.now(UTC),
        )
        assert entry.stage == "REVENUE_READY"

    def test_reply_event_model_fields(self) -> None:
        from datetime import UTC, datetime

        from validation_engine.models import ReplyEvent
        event = ReplyEvent(
            company_id="company_1",
            reply_type="positive",
            timestamp=datetime.now(UTC),
        )
        assert event.company_id == "company_1"
        assert event.reply_type == "positive"

    def test_meeting_event_model_fields(self) -> None:
        from datetime import UTC, datetime

        from validation_engine.models import MeetingEvent
        event = MeetingEvent(
            company_id="company_1",
            meeting_type="scheduled",
            timestamp=datetime.now(UTC),
        )
        assert event.company_id == "company_1"
        assert event.meeting_type == "scheduled"

    def test_proposal_event_model_fields(self) -> None:
        from datetime import UTC, datetime

        from validation_engine.models import ProposalEvent
        event = ProposalEvent(
            company_id="company_1",
            status="sent",
            timestamp=datetime.now(UTC),
        )
        assert event.company_id == "company_1"
        assert event.status == "sent"

    def test_deal_event_model_fields(self) -> None:
        from validation_engine.models import DealEvent
        event = DealEvent(
            company_id="company_1",
            status="won",
            revenue=50000.0,
        )
        assert event.company_id == "company_1"
        assert event.status == "won"
        assert event.revenue == 50000.0

    def test_objection_event_model_fields(self) -> None:
        from datetime import UTC, datetime

        from validation_engine.models import ObjectionEvent
        event = ObjectionEvent(
            company_id="company_1",
            category="no_budget",
            timestamp=datetime.now(UTC),
        )
        assert event.company_id == "company_1"
        assert event.category == "no_budget"

    def test_connector_roi_model_fields(self) -> None:
        from validation_engine.models import ConnectorRoi
        roi = ConnectorRoi(connector="linkedin")
        assert roi.connector == "linkedin"
        assert roi.revenue == 0.0

    def test_industry_roi_model_fields(self) -> None:
        from validation_engine.models import IndustryRoi
        roi = IndustryRoi(industry="healthcare")
        assert roi.industry == "healthcare"
        assert roi.revenue == 0.0

    def test_service_roi_model_fields(self) -> None:
        from validation_engine.models import ServiceRoi
        roi = ServiceRoi(service="ai_automation")
        assert roi.service == "ai_automation"
        assert roi.revenue == 0.0

    def test_persona_roi_model_fields(self) -> None:
        from validation_engine.models import PersonaRoi
        roi = PersonaRoi(persona="founder")
        assert roi.persona == "founder"
        assert roi.revenue == 0.0

    def test_trigger_roi_model_fields(self) -> None:
        from validation_engine.models import TriggerRoi
        roi = TriggerRoi(trigger="funding")
        assert roi.trigger == "funding"
        assert roi.revenue == 0.0

    def test_funnel_stage_model_fields(self) -> None:
        from validation_engine.models import FunnelStage
        stage = FunnelStage(stage="REVENUE_READY", count=10)
        assert stage.stage == "REVENUE_READY"
        assert stage.count == 10

    def test_validation_dashboard_model_fields(self) -> None:
        from datetime import UTC, datetime

        from validation_engine.models import ValidationDashboard
        dashboard = ValidationDashboard(generated_at=datetime.now(UTC))
        assert dashboard.today_replies == 0
        assert dashboard.scoring_version == "bvcl-v1"

    def test_daily_report_model_fields(self) -> None:
        from validation_engine.models import DailyReport
        report = DailyReport(report_date="2026-07-29")
        assert report.report_date == "2026-07-29"
        assert report.revenue == 0.0

    def test_weekly_report_model_fields(self) -> None:
        from validation_engine.models import WeeklyReport
        report = WeeklyReport(week_start="2026-07-22", week_end="2026-07-29")
        assert report.week_start == "2026-07-22"
        assert report.revenue == 0.0

    def test_monthly_report_model_fields(self) -> None:
        from validation_engine.models import MonthlyReport
        report = MonthlyReport(month="2026-07")
        assert report.month == "2026-07"
        assert report.revenue == 0.0
