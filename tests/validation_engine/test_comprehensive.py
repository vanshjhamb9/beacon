"""Additional comprehensive tests for validation engine — targeting 700+ total."""

from __future__ import annotations

import pytest

from validation_engine import (
    DEAL_STATUSES,
    KNOWN_CONNECTORS,
    KNOWN_INDUSTRIES,
    KNOWN_PERSONAS,
    KNOWN_SERVICES,
    KNOWN_TRIGGERS,
    MEETING_TYPES,
    OBJECTION_CATEGORIES,
    PROPOSAL_STATUSES,
    REPLY_TYPES,
    SCORING_VERSION,
    VALIDATION_STAGES,
)
from validation_engine.calibration_engine import CalibrationEngine
from validation_engine.connector_roi import ConnectorRoiEngine
from validation_engine.deal_tracker import DealTracker
from validation_engine.funnel_engine import FunnelEngine
from validation_engine.industry_roi import IndustryRoiEngine
from validation_engine.lead_validator import LeadValidator
from validation_engine.meeting_tracker import MeetingTracker
from validation_engine.objection_engine import ObjectionEngine
from validation_engine.outcome_tracker import OutcomeTracker
from validation_engine.persona_roi import PersonaRoiEngine
from validation_engine.proposal_tracker import ProposalTracker
from validation_engine.reply_tracker import ReplyTracker
from validation_engine.service_roi import ServiceRoiEngine
from validation_engine.timeline_engine import TimelineEngine
from validation_engine.trigger_roi import TriggerRoiEngine
from validation_engine.validation_engine import ValidationEngine
from validation_engine.validation_scheduler import ValidationScheduler

# --- Constants Tests ---

class TestConstants:
    def test_scoring_version(self) -> None:
        assert SCORING_VERSION == "bvcl-v1"

    def test_validation_stages_count(self) -> None:
        assert len(VALIDATION_STAGES) == 13

    def test_validation_stages_unique(self) -> None:
        assert len(set(VALIDATION_STAGES)) == len(VALIDATION_STAGES)

    def test_reply_types_count(self) -> None:
        assert len(REPLY_TYPES) == 7

    def test_reply_types_unique(self) -> None:
        assert len(set(REPLY_TYPES)) == len(REPLY_TYPES)

    def test_meeting_types_count(self) -> None:
        assert len(MEETING_TYPES) == 5

    def test_meeting_types_unique(self) -> None:
        assert len(set(MEETING_TYPES)) == len(MEETING_TYPES)

    def test_proposal_statuses_count(self) -> None:
        assert len(PROPOSAL_STATUSES) == 6

    def test_proposal_statuses_unique(self) -> None:
        assert len(set(PROPOSAL_STATUSES)) == len(PROPOSAL_STATUSES)

    def test_deal_statuses_count(self) -> None:
        assert len(DEAL_STATUSES) == 3

    def test_deal_statuses_unique(self) -> None:
        assert len(set(DEAL_STATUSES)) == len(DEAL_STATUSES)

    def test_objection_categories_count(self) -> None:
        assert len(OBJECTION_CATEGORIES) == 9

    def test_objection_categories_unique(self) -> None:
        assert len(set(OBJECTION_CATEGORIES)) == len(OBJECTION_CATEGORIES)

    def test_known_connectors_count(self) -> None:
        assert len(KNOWN_CONNECTORS) >= 10

    def test_known_industries_count(self) -> None:
        assert len(KNOWN_INDUSTRIES) >= 5

    def test_known_services_count(self) -> None:
        assert len(KNOWN_SERVICES) >= 5

    def test_known_personas_count(self) -> None:
        assert len(KNOWN_PERSONAS) >= 5

    def test_known_triggers_count(self) -> None:
        assert len(KNOWN_TRIGGERS) >= 10


# --- LeadValidator Extended Tests ---

class TestLeadValidatorExtended:
    def test_record_all_valid_stages(self, lead_validator: LeadValidator) -> None:
        for stage in VALIDATION_STAGES:
            event = lead_validator.record_transition("company_1", stage)
            assert event.stage == stage

    def test_multiple_companies_parallel(self, lead_validator: LeadValidator) -> None:
        for i in range(10):
            lead_validator.record_transition(f"company_{i}", "REVENUE_READY")
        assert lead_validator.get_stage_count("REVENUE_READY") == 10

    def test_funnel_conversion_100_percent(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        rate = lead_validator.calculate_conversion_rate("REVENUE_READY", "CONTACTED")
        assert rate == 100.0

    def test_funnel_conversion_0_percent(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        rate = lead_validator.calculate_conversion_rate("REVENUE_READY", "CONTACTED")
        assert rate == 0.0

    def test_companies_in_multiple_stages(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        lead_validator.record_transition("company_1", "REPLIED")
        assert lead_validator.get_company_stage("company_1") == "REPLIED"
        assert len(lead_validator.get_events_by_company("company_1")) == 3

    def test_empty_company_stage(self, lead_validator: LeadValidator) -> None:
        assert lead_validator.get_company_stage("nonexistent") is None

    def test_events_by_stage_multiple(self, lead_validator: LeadValidator) -> None:
        for i in range(5):
            lead_validator.record_transition(f"company_{i}", "REVENUE_READY")
        assert lead_validator.get_stage_count("REVENUE_READY") == 5

    def test_conversion_rate_rounding(self, lead_validator: LeadValidator) -> None:
        for i in range(3):
            lead_validator.record_transition(f"company_{i}", "REVENUE_READY")
        lead_validator.record_transition("company_0", "CONTACTED")
        rate = lead_validator.calculate_conversion_rate("REVENUE_READY", "CONTACTED")
        assert rate == pytest.approx(33.33, rel=0.01)


# --- ReplyTracker Extended Tests ---

class TestReplyTrackerExtended:
    def test_record_all_reply_types(self, reply_tracker: ReplyTracker) -> None:
        for reply_type in REPLY_TYPES:
            reply_tracker.record_reply("company_1", reply_type)
        assert len(reply_tracker.get_all_replies()) == len(REPLY_TYPES)

    def test_reply_rate_100_percent(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive")
        reply_tracker.record_reply("company_2", "negative")
        rate = reply_tracker.get_reply_rate()
        assert rate == 100.0

    def test_reply_rate_0_percent(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "no_response")
        rate = reply_tracker.get_reply_rate()
        assert rate == 0.0

    def test_positive_reply_rate_100_percent(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive")
        rate = reply_tracker.get_positive_reply_rate()
        assert rate == 100.0

    def test_multiple_replies_same_company(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive")
        reply_tracker.record_reply("company_1", "negative")
        replies = reply_tracker.get_replies_for_company("company_1")
        assert len(replies) == 2

    def test_reply_time_average(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive", reply_time_seconds=100.0)
        reply_tracker.record_reply("company_2", "positive", reply_time_seconds=300.0)
        avg = reply_tracker.get_avg_reply_time()
        assert avg == 200.0


# --- MeetingTracker Extended Tests ---

class TestMeetingTrackerExtended:
    def test_record_all_meeting_types(self, meeting_tracker: MeetingTracker) -> None:
        for meeting_type in MEETING_TYPES:
            meeting_tracker.record_meeting("company_1", meeting_type)
        assert len(meeting_tracker.get_all_meetings()) == len(MEETING_TYPES)

    def test_meeting_rate_100_percent(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "completed")
        rate = meeting_tracker.get_meeting_rate()
        assert rate == 100.0

    def test_meeting_rate_0_percent(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "cancelled")
        rate = meeting_tracker.get_meeting_rate()
        assert rate == 0.0

    def test_no_show_rate_100_percent(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "no_show")
        rate = meeting_tracker.get_no_show_rate()
        assert rate == 100.0

    def test_duration_average(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "completed", duration_minutes=30.0)
        meeting_tracker.record_meeting("company_2", "completed", duration_minutes=60.0)
        avg = meeting_tracker.get_avg_duration()
        assert avg == 45.0


# --- ProposalTracker Extended Tests ---

class TestProposalTrackerExtended:
    def test_record_all_statuses(self, proposal_tracker: ProposalTracker) -> None:
        for status in PROPOSAL_STATUSES:
            proposal_tracker.record_proposal("company_1", status)
        assert len(proposal_tracker.get_all_proposals()) == len(PROPOSAL_STATUSES)

    def test_acceptance_rate_100_percent(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "sent")
        proposal_tracker.record_proposal("company_1", "accepted")
        rate = proposal_tracker.get_acceptance_rate()
        assert rate == 100.0

    def test_acceptance_rate_0_percent(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "sent")
        proposal_tracker.record_proposal("company_1", "rejected")
        rate = proposal_tracker.get_acceptance_rate()
        assert rate == 0.0

    def test_total_value_multiple(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "sent", value=50000.0)
        proposal_tracker.record_proposal("company_2", "sent", value=75000.0)
        proposal_tracker.record_proposal("company_3", "sent", value=100000.0)
        total = proposal_tracker.get_total_proposal_value()
        assert total == 225000.0


# --- DealTracker Extended Tests ---

class TestDealTrackerExtended:
    def test_record_all_statuses(self, deal_tracker: DealTracker) -> None:
        for status in DEAL_STATUSES:
            deal_tracker.record_deal("company_1", status)
        assert len(deal_tracker.get_all_deals()) == len(DEAL_STATUSES)

    def test_win_rate_100_percent(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won")
        rate = deal_tracker.get_win_rate()
        assert rate == 100.0

    def test_win_rate_0_percent(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "lost")
        rate = deal_tracker.get_win_rate()
        assert rate == 0.0

    def test_revenue_multiple_services(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won", revenue=50000.0, service_sold="ai_automation")
        deal_tracker.record_deal("company_2", "won", revenue=75000.0, service_sold="crm")
        deal_tracker.record_deal("company_3", "won", revenue=25000.0, service_sold="ai_automation")
        result = deal_tracker.get_revenue_by_service()
        assert result["ai_automation"] == 75000.0
        assert result["crm"] == 75000.0

    def test_deals_by_status_multiple(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won")
        deal_tracker.record_deal("company_2", "won")
        deal_tracker.record_deal("company_3", "lost")
        deal_tracker.record_deal("company_4", "paused")
        counts = deal_tracker.get_deals_by_status()
        assert counts["won"] == 2
        assert counts["lost"] == 1
        assert counts["paused"] == 1


# --- TimelineEngine Extended Tests ---

class TestTimelineEngineExtended:
    def test_add_all_stages(self, timeline_engine: TimelineEngine) -> None:
        for stage in VALIDATION_STAGES:
            timeline_engine.add_event("company_1", stage)
        assert len(timeline_engine.get_timeline("company_1")) == len(VALIDATION_STAGES)

    def test_multiple_companies(self, timeline_engine: TimelineEngine) -> None:
        for i in range(10):
            timeline_engine.add_event(f"company_{i}", "REVENUE_READY")
        assert len(timeline_engine.get_companies_at_stage("REVENUE_READY")) == 10

    def test_stage_history_order(self, timeline_engine: TimelineEngine) -> None:
        timeline_engine.add_event("company_1", "REVENUE_READY")
        timeline_engine.add_event("company_1", "CONTACTED")
        timeline_engine.add_event("company_1", "REPLIED")
        history = timeline_engine.get_stage_history("company_1")
        assert history == ["REVENUE_READY", "CONTACTED", "REPLIED"]

    def test_companies_who_reached_stage(self, timeline_engine: TimelineEngine) -> None:
        timeline_engine.add_event("company_1", "REVENUE_READY")
        timeline_engine.add_event("company_1", "CONTACTED")
        timeline_engine.add_event("company_2", "REVENUE_READY")
        companies = timeline_engine.get_companies_who_reached_stage("CONTACTED")
        assert companies == ["company_1"]


# --- ConnectorRoiEngine Extended Tests ---

class TestConnectorRoiEngineExtended:
    def test_multiple_connectors(self, connector_roi: ConnectorRoiEngine) -> None:
        for connector in KNOWN_CONNECTORS[:5]:
            connector_roi.record_deal(connector, revenue=10000.0)
        assert len(connector_roi.calculate_all()) == 5

    def test_ranking_order(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_deal("github", revenue=10000.0)
        connector_roi.record_deal("linkedin", revenue=50000.0)
        connector_roi.record_deal("twitter", revenue=25000.0)
        ranked = connector_roi.rank_by_revenue()
        assert ranked[0].connector == "linkedin"
        assert ranked[-1].connector == "github"

    def test_calculate_all_empty(self, connector_roi: ConnectorRoiEngine) -> None:
        result = connector_roi.calculate_all()
        assert result == []


# --- IndustryRoiEngine Extended Tests ---

class TestIndustryRoiEngineExtended:
    def test_multiple_industries(self, industry_roi: IndustryRoiEngine) -> None:
        for industry in KNOWN_INDUSTRIES[:5]:
            industry_roi.record_deal(industry, revenue=10000.0)
        assert len(industry_roi.calculate_all()) == 5

    def test_ranking_by_revenue(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_deal("healthcare", revenue=100000.0)
        industry_roi.record_deal("fintech", revenue=200000.0)
        ranked = industry_roi.rank_by_revenue()
        assert ranked[0].industry == "fintech"


# --- ServiceRoiEngine Extended Tests ---

class TestServiceRoiEngineExtended:
    def test_multiple_services(self, service_roi: ServiceRoiEngine) -> None:
        for service in KNOWN_SERVICES[:5]:
            service_roi.record_deal(service, revenue=10000.0)
        assert len(service_roi.calculate_all()) == 5


# --- PersonaRoiEngine Extended Tests ---

class TestPersonaRoiEngineExtended:
    def test_multiple_personas(self, persona_roi: PersonaRoiEngine) -> None:
        for persona in KNOWN_PERSONAS[:5]:
            persona_roi.record_deal(persona, revenue=10000.0)
        assert len(persona_roi.calculate_all()) == 5


# --- TriggerRoiEngine Extended Tests ---

class TestTriggerRoiEngineExtended:
    def test_multiple_triggers(self, trigger_roi: TriggerRoiEngine) -> None:
        for trigger in KNOWN_TRIGGERS[:5]:
            trigger_roi.record_deal(trigger, revenue=10000.0)
        assert len(trigger_roi.calculate_all()) == 5


# --- ObjectionEngine Extended Tests ---

class TestObjectionEngineExtended:
    def test_record_all_categories(self, objection_engine: ObjectionEngine) -> None:
        for category in OBJECTION_CATEGORIES:
            objection_engine.record_objection("company_1", category)
        assert len(objection_engine.get_all_objections()) == len(OBJECTION_CATEGORIES)

    def test_top_objections_ordering(self, objection_engine: ObjectionEngine) -> None:
        for _ in range(5):
            objection_engine.record_objection("company_1", "no_budget")
        for _ in range(3):
            objection_engine.record_objection("company_2", "wrong_timing")
        top = objection_engine.get_top_objections()
        assert top[0]["category"] == "no_budget"
        assert top[0]["count"] == 5

    def test_objections_by_multiple_dimensions(self, objection_engine: ObjectionEngine) -> None:
        objection_engine.record_objection(
            "company_1", "no_budget",
            industry="healthcare", service="ai_automation",
            connector="linkedin", persona="founder",
        )
        assert len(objection_engine.get_by_industry("healthcare")) == 1
        assert len(objection_engine.get_by_service("ai_automation")) == 1
        assert len(objection_engine.get_by_connector("linkedin")) == 1
        assert len(objection_engine.get_by_persona("founder")) == 1


# --- OutcomeTracker Extended Tests ---

class TestOutcomeTrackerExtended:
    def test_multiple_outcomes(self, outcome_tracker: OutcomeTracker) -> None:
        outcome_tracker.record_outcome("company_1", "won", revenue=50000.0)
        outcome_tracker.record_outcome("company_2", "won", revenue=75000.0)
        outcome_tracker.record_outcome("company_3", "lost")
        assert outcome_tracker.get_total_revenue() == 125000.0
        assert outcome_tracker.get_win_rate() == pytest.approx(66.67, rel=0.01)


# --- FunnelEngine Extended Tests ---

class TestFunnelEngineExtended:
    def test_conversion_summary(
        self,
        funnel_engine: FunnelEngine,
        lead_validator: LeadValidator,
    ) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        lead_validator.record_transition("company_1", "REPLIED")
        summary = funnel_engine.get_conversion_summary()
        assert summary["total_companies"] == 1
        assert len(summary["stage_conversions"]) > 0

    def test_stage_conversions_count(self, funnel_engine: FunnelEngine) -> None:
        conversions = funnel_engine.get_stage_conversions()
        assert len(conversions) == len(VALIDATION_STAGES) - 1


# --- ValidationEngine Extended Tests ---

class TestValidationEngineExtended:
    def test_full_lifecycle(self, validation_engine: ValidationEngine) -> None:
        validation_engine.record_email_sent("company_1")
        validation_engine.record_email_opened("company_1")
        validation_engine.record_email_clicked("company_1")
        validation_engine.record_reply("company_1", "positive")
        validation_engine.record_meeting("company_1", "scheduled")
        validation_engine.record_meeting("company_1", "completed")
        validation_engine.record_proposal("company_1", "sent")
        validation_engine.record_proposal("company_1", "accepted")
        validation_engine.record_deal("company_1", "won", revenue=100000.0)
        timeline = validation_engine.get_company_timeline("company_1")
        assert len(timeline) > 0

    def test_dashboard_after_lifecycle(self, validation_engine: ValidationEngine) -> None:
        validation_engine.record_email_sent("company_1")
        validation_engine.record_reply("company_1", "positive")
        validation_engine.record_meeting("company_1", "completed")
        validation_engine.record_deal("company_1", "won", revenue=50000.0)
        dashboard = validation_engine.get_dashboard_data()
        assert dashboard["total_revenue"] == 50000.0

    def test_record_objection(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_objection("company_1", "no_budget")
        assert result["ok"] is True


# --- CalibrationEngine Extended Tests ---

class TestCalibrationEngineExtended:
    def test_full_calibration(self, calibration_engine: CalibrationEngine) -> None:
        calibration_engine.connector_roi.record_deal("linkedin", revenue=50000.0)
        calibration_engine.connector_roi.record_deal("github", revenue=10000.0)
        calibration_engine.industry_roi.record_deal("healthcare", revenue=100000.0)
        calibration_engine.service_roi.record_deal("ai_automation", revenue=75000.0)
        calibration_engine.persona_roi.record_deal("founder", revenue=100000.0)
        calibration_engine.trigger_roi.record_deal("funding", revenue=100000.0)
        calibration_engine.deal_tracker.record_deal("company_1", "won", revenue=100000.0)
        summary = calibration_engine.get_calibration_summary()
        assert summary["total_revenue"] == 100000.0
        assert len(summary["connector_ranking"]) == 2
        assert len(summary["industry_ranking"]) == 1
        assert len(summary["service_ranking"]) == 1
        assert len(summary["persona_ranking"]) == 1
        assert len(summary["trigger_ranking"]) == 1


# --- ValidationScheduler Extended Tests ---

class TestValidationSchedulerExtended:
    def test_all_report_types(self) -> None:
        scheduler = ValidationScheduler()
        daily = scheduler.get_daily_report()
        weekly = scheduler.get_weekly_report()
        monthly = scheduler.get_monthly_report()
        assert "report_date" in daily
        assert "week_end" in weekly
        assert "month" in monthly

    def test_caching_behavior(self) -> None:
        scheduler = ValidationScheduler()
        d1 = scheduler.get_daily_report()
        d2 = scheduler.get_daily_report()
        w1 = scheduler.get_weekly_report()
        w2 = scheduler.get_weekly_report()
        m1 = scheduler.get_monthly_report()
        m2 = scheduler.get_monthly_report()
        assert d1 is d2
        assert w1 is w2
        assert m1 is m2


# --- Cross-Module Integration Tests ---

class TestCrossModuleIntegration:
    def test_lead_to_deal_flow(self) -> None:
        engine = ValidationEngine()
        engine.record_email_sent("company_1")
        engine.record_reply("company_1", "positive")
        engine.record_meeting("company_1", "completed")
        engine.record_proposal("company_1", "sent")
        engine.record_deal("company_1", "won", revenue=100000.0)
        dashboard = engine.get_dashboard_data()
        assert dashboard["total_revenue"] == 100000.0
        assert dashboard["win_rate"] > 0

    def test_multiple_companies_flow(self) -> None:
        engine = ValidationEngine()
        for i in range(5):
            engine.record_email_sent(f"company_{i}")
            engine.record_reply(f"company_{i}", "positive")
            engine.record_meeting(f"company_{i}", "completed")
            engine.record_deal(f"company_{i}", "won", revenue=10000.0 * (i + 1))
        dashboard = engine.get_dashboard_data()
        assert dashboard["total_revenue"] == 150000.0

    def test_connector_roi_with_validation(self) -> None:
        connector_roi = ConnectorRoiEngine()
        connector_roi.record_signal("linkedin", companies=10, revenue_ready=5)
        connector_roi.record_reply("linkedin")
        connector_roi.record_meeting("linkedin")
        connector_roi.record_deal("linkedin", revenue=50000.0)
        roi = connector_roi.calculate("linkedin")
        assert roi.revenue == 50000.0
        assert roi.reply_rate == 20.0
        assert roi.meeting_rate == 100.0
        assert roi.win_rate == 100.0

    def test_industry_roi_with_validation(self) -> None:
        industry_roi = IndustryRoiEngine()
        industry_roi.record_company("healthcare")
        industry_roi.record_revenue_ready("healthcare")
        industry_roi.record_reply("healthcare")
        industry_roi.record_meeting("healthcare")
        industry_roi.record_deal("healthcare", revenue=100000.0)
        roi = industry_roi.calculate("healthcare")
        assert roi.revenue == 100000.0
        assert roi.reply_rate == 100.0
        assert roi.win_rate == 100.0

    def test_service_roi_with_validation(self) -> None:
        service_roi = ServiceRoiEngine()
        service_roi.record_company("ai_automation")
        service_roi.record_reply("ai_automation")
        service_roi.record_meeting("ai_automation")
        service_roi.record_proposal("ai_automation")
        service_roi.record_deal("ai_automation", revenue=75000.0)
        roi = service_roi.calculate("ai_automation")
        assert roi.revenue == 75000.0
        assert roi.reply_rate == 100.0

    def test_persona_roi_with_validation(self) -> None:
        persona_roi = PersonaRoiEngine()
        persona_roi.record_contacted("founder")
        persona_roi.record_reply("founder")
        persona_roi.record_meeting("founder")
        persona_roi.record_deal("founder", revenue=100000.0)
        roi = persona_roi.calculate("founder")
        assert roi.revenue == 100000.0
        assert roi.reply_rate == 100.0

    def test_trigger_roi_with_validation(self) -> None:
        trigger_roi = TriggerRoiEngine()
        trigger_roi.record_company("funding")
        trigger_roi.record_reply("funding")
        trigger_roi.record_meeting("funding")
        trigger_roi.record_deal("funding", revenue=100000.0)
        roi = trigger_roi.calculate("funding")
        assert roi.revenue == 100000.0
        assert roi.reply_rate == 100.0

    def test_objection_with_validation(self) -> None:
        objection_engine = ObjectionEngine()
        objection_engine.record_objection(
            "company_1", "no_budget",
            industry="healthcare", service="ai_automation",
        )
        assert len(objection_engine.get_by_industry("healthcare")) == 1
        assert len(objection_engine.get_by_service("ai_automation")) == 1

    def test_timeline_with_validation(self) -> None:
        timeline_engine = TimelineEngine()
        timeline_engine.add_event("company_1", "REVENUE_READY")
        timeline_engine.add_event("company_1", "CONTACTED")
        timeline_engine.add_event("company_1", "REPLIED")
        timeline_engine.add_event("company_1", "MEETING_BOOKED")
        timeline_engine.add_event("company_1", "PROPOSAL_SENT")
        timeline_engine.add_event("company_1", "WON")
        assert timeline_engine.get_latest_stage("company_1") == "WON"
        assert len(timeline_engine.get_timeline("company_1")) == 6

    def test_funnel_with_full_lifecycle(self) -> None:
        lead_validator = LeadValidator()
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        lead_validator.record_transition("company_1", "REPLIED")
        lead_validator.record_transition("company_1", "MEETING_BOOKED")
        lead_validator.record_transition("company_1", "PROPOSAL_SENT")
        lead_validator.record_transition("company_1", "WON")
        funnel_engine = FunnelEngine(lead_validator)
        summary = funnel_engine.get_conversion_summary()
        assert summary["total_companies"] == 1
        assert summary["total_won"] == 1
        assert summary["overall_conversion_rate"] == 100.0

    def test_reports_with_full_data(self) -> None:
        from validation_engine.validation_reports import ValidationReportService
        service = ValidationReportService()
        service.reply_tracker.record_reply("company_1", "positive")
        service.meeting_tracker.record_meeting("company_1", "completed")
        service.proposal_tracker.record_proposal("company_1", "sent")
        service.deal_tracker.record_deal("company_1", "won", revenue=100000.0)
        daily = service.generate_daily_report()
        weekly = service.generate_weekly_report()
        monthly = service.generate_monthly_report()
        assert daily.replies == 1
        assert daily.meetings == 1
        assert daily.won == 1
        assert daily.revenue == 100000.0
        assert weekly.revenue == 100000.0
        assert monthly.revenue == 100000.0
