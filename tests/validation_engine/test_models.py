"""Model and dataclass tests for validation engine."""

from __future__ import annotations

from datetime import UTC, datetime

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


class TestValidationEvent:
    def test_creation(self) -> None:
        event = ValidationEvent(
            event_id="evt_1",
            company_id="company_1",
            stage="REVENUE_READY",
            timestamp=datetime.now(UTC),
        )
        assert event.event_id == "evt_1"
        assert event.company_id == "company_1"
        assert event.stage == "REVENUE_READY"
        assert event.evidence == {}
        assert event.source == ""
        assert event.confidence == 1.0

    def test_with_evidence(self) -> None:
        event = ValidationEvent(
            event_id="evt_1",
            company_id="company_1",
            stage="CONTACTED",
            timestamp=datetime.now(UTC),
            evidence={"source": "email"},
            source="outlook",
            confidence=0.9,
        )
        assert event.evidence == {"source": "email"}
        assert event.source == "outlook"
        assert event.confidence == 0.9


class TestTimelineEntry:
    def test_creation(self) -> None:
        entry = TimelineEntry(
            stage="REVENUE_READY",
            timestamp=datetime.now(UTC),
        )
        assert entry.stage == "REVENUE_READY"
        assert entry.evidence == {}
        assert entry.source == ""
        assert entry.duration_seconds is None

    def test_with_duration(self) -> None:
        entry = TimelineEntry(
            stage="CONTACTED",
            timestamp=datetime.now(UTC),
            duration_seconds=3600.0,
        )
        assert entry.duration_seconds == 3600.0


class TestReplyEvent:
    def test_creation(self) -> None:
        event = ReplyEvent(
            company_id="company_1",
            reply_type="positive",
            timestamp=datetime.now(UTC),
        )
        assert event.company_id == "company_1"
        assert event.reply_type == "positive"
        assert event.reply_time_seconds is None

    def test_with_reply_time(self) -> None:
        event = ReplyEvent(
            company_id="company_1",
            reply_type="positive",
            timestamp=datetime.now(UTC),
            reply_time_seconds=3600.0,
        )
        assert event.reply_time_seconds == 3600.0


class TestMeetingEvent:
    def test_creation(self) -> None:
        event = MeetingEvent(
            company_id="company_1",
            meeting_type="scheduled",
            timestamp=datetime.now(UTC),
        )
        assert event.company_id == "company_1"
        assert event.meeting_type == "scheduled"
        assert event.duration_minutes is None
        assert event.calendar_link == ""
        assert event.notes == ""
        assert event.next_action == ""

    def test_with_details(self) -> None:
        event = MeetingEvent(
            company_id="company_1",
            meeting_type="completed",
            timestamp=datetime.now(UTC),
            duration_minutes=45.0,
            calendar_link="https://cal.com/abc",
            notes="Discussed pricing",
            next_action="Send proposal",
        )
        assert event.duration_minutes == 45.0
        assert event.calendar_link == "https://cal.com/abc"
        assert event.notes == "Discussed pricing"
        assert event.next_action == "Send proposal"


class TestProposalEvent:
    def test_creation(self) -> None:
        event = ProposalEvent(
            company_id="company_1",
            status="sent",
            timestamp=datetime.now(UTC),
        )
        assert event.company_id == "company_1"
        assert event.status == "sent"
        assert event.value is None

    def test_with_value(self) -> None:
        event = ProposalEvent(
            company_id="company_1",
            status="sent",
            timestamp=datetime.now(UTC),
            value=50000.0,
        )
        assert event.value == 50000.0


class TestDealEvent:
    def test_creation(self) -> None:
        event = DealEvent(
            company_id="company_1",
            status="won",
            revenue=50000.0,
        )
        assert event.company_id == "company_1"
        assert event.status == "won"
        assert event.revenue == 50000.0
        assert event.expected_revenue == 0.0
        assert event.service_sold == ""
        assert event.reason == ""

    def test_with_details(self) -> None:
        event = DealEvent(
            company_id="company_1",
            status="won",
            revenue=100000.0,
            expected_revenue=120000.0,
            service_sold="ai_automation",
            reason="Good fit",
        )
        assert event.revenue == 100000.0
        assert event.expected_revenue == 120000.0
        assert event.service_sold == "ai_automation"
        assert event.reason == "Good fit"


class TestObjectionEvent:
    def test_creation(self) -> None:
        event = ObjectionEvent(
            company_id="company_1",
            category="no_budget",
            timestamp=datetime.now(UTC),
        )
        assert event.company_id == "company_1"
        assert event.category == "no_budget"
        assert event.industry == ""
        assert event.service == ""
        assert event.connector == ""
        assert event.persona == ""

    def test_with_details(self) -> None:
        event = ObjectionEvent(
            company_id="company_1",
            category="no_budget",
            timestamp=datetime.now(UTC),
            industry="healthcare",
            service="ai_automation",
            connector="linkedin",
            persona="founder",
        )
        assert event.industry == "healthcare"
        assert event.service == "ai_automation"
        assert event.connector == "linkedin"
        assert event.persona == "founder"


class TestConnectorRoi:
    def test_creation(self) -> None:
        roi = ConnectorRoi(connector="linkedin")
        assert roi.connector == "linkedin"
        assert roi.signals == 0
        assert roi.revenue == 0.0
        assert roi.reply_rate == 0.0

    def test_with_values(self) -> None:
        roi = ConnectorRoi(
            connector="linkedin",
            signals=100,
            companies=50,
            revenue_ready=25,
            replies=10,
            meetings=5,
            deals=2,
            revenue=50000.0,
            reply_rate=40.0,
            meeting_rate=50.0,
            win_rate=40.0,
        )
        assert roi.signals == 100
        assert roi.revenue == 50000.0
        assert roi.reply_rate == 40.0


class TestIndustryRoi:
    def test_creation(self) -> None:
        roi = IndustryRoi(industry="healthcare")
        assert roi.industry == "healthcare"
        assert roi.companies == 0
        assert roi.revenue == 0.0


class TestServiceRoi:
    def test_creation(self) -> None:
        roi = ServiceRoi(service="ai_automation")
        assert roi.service == "ai_automation"
        assert roi.companies == 0
        assert roi.revenue == 0.0


class TestPersonaRoi:
    def test_creation(self) -> None:
        roi = PersonaRoi(persona="founder")
        assert roi.persona == "founder"
        assert roi.contacted == 0
        assert roi.revenue == 0.0


class TestTriggerRoi:
    def test_creation(self) -> None:
        roi = TriggerRoi(trigger="funding")
        assert roi.trigger == "funding"
        assert roi.companies == 0
        assert roi.revenue == 0.0


class TestFunnelStage:
    def test_creation(self) -> None:
        stage = FunnelStage(stage="REVENUE_READY", count=10)
        assert stage.stage == "REVENUE_READY"
        assert stage.count == 10
        assert stage.conversion_from_previous == 0.0
        assert stage.drop_off == 0.0


class TestValidationDashboard:
    def test_creation(self) -> None:
        dashboard = ValidationDashboard(generated_at=datetime.now(UTC))
        assert dashboard.today_replies == 0
        assert dashboard.today_meetings == 0
        assert dashboard.today_proposals == 0
        assert dashboard.today_wins == 0
        assert dashboard.today_revenue == 0.0
        assert dashboard.reply_rate == 0.0
        assert dashboard.meeting_rate == 0.0
        assert dashboard.win_rate == 0.0
        assert dashboard.avg_sales_cycle_days == 0.0
        assert dashboard.scoring_version == "bvcl-v1"


class TestDailyReport:
    def test_creation(self) -> None:
        report = DailyReport(report_date="2026-07-29")
        assert report.report_date == "2026-07-29"
        assert report.signals == 0
        assert report.replies == 0
        assert report.meetings == 0
        assert report.won == 0
        assert report.lost == 0
        assert report.revenue == 0.0


class TestWeeklyReport:
    def test_creation(self) -> None:
        report = WeeklyReport(week_start="2026-07-22", week_end="2026-07-29")
        assert report.week_start == "2026-07-22"
        assert report.week_end == "2026-07-29"
        assert report.revenue == 0.0
        assert report.meetings == 0
        assert report.deals == 0


class TestMonthlyReport:
    def test_creation(self) -> None:
        report = MonthlyReport(month="2026-07")
        assert report.month == "2026-07"
        assert report.revenue == 0.0
        assert report.avg_deal_size == 0.0
        assert report.win_rate == 0.0
        assert report.revenue_per_connector == {}
        assert report.revenue_per_industry == {}
        assert report.revenue_per_service == {}
