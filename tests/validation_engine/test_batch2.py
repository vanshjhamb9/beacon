"""Additional comprehensive tests for validation engine — batch 2."""

from __future__ import annotations

import pytest

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
from validation_engine.validation_metrics import ValidationMetrics

# --- LeadValidator Batch 2 ---

class TestLeadValidatorBatch2:
    def test_conversion_rate_10_percent(self, lead_validator: LeadValidator) -> None:
        for i in range(10):
            lead_validator.record_transition(f"company_{i}", "REVENUE_READY")
        lead_validator.record_transition("company_0", "CONTACTED")
        rate = lead_validator.calculate_conversion_rate("REVENUE_READY", "CONTACTED")
        assert rate == 10.0

    def test_conversion_rate_90_percent(self, lead_validator: LeadValidator) -> None:
        for i in range(10):
            lead_validator.record_transition(f"company_{i}", "REVENUE_READY")
        for i in range(9):
            lead_validator.record_transition(f"company_{i}", "CONTACTED")
        rate = lead_validator.calculate_conversion_rate("REVENUE_READY", "CONTACTED")
        assert rate == 90.0

    def test_funnel_conversion_chain(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        lead_validator.record_transition("company_1", "EMAIL_OPENED")
        lead_validator.record_transition("company_1", "EMAIL_CLICKED")
        lead_validator.record_transition("company_1", "REPLIED")
        funnel = lead_validator.get_funnel()
        assert len(funnel) > 0

    def test_multiple_companies_different_stages(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_2", "CONTACTED")
        lead_validator.record_transition("company_3", "REPLIED")
        lead_validator.record_transition("company_4", "WON")
        assert lead_validator.get_company_stage("company_1") == "REVENUE_READY"
        assert lead_validator.get_company_stage("company_2") == "CONTACTED"
        assert lead_validator.get_company_stage("company_3") == "REPLIED"
        assert lead_validator.get_company_stage("company_4") == "WON"

    def test_events_timestamps(self, lead_validator: LeadValidator) -> None:
        event1 = lead_validator.record_transition("company_1", "REVENUE_READY")
        event2 = lead_validator.record_transition("company_1", "CONTACTED")
        assert event2.timestamp >= event1.timestamp


# --- ReplyTracker Batch 2 ---

class TestReplyTrackerBatch2:
    def test_reply_rate_25_percent(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive")
        reply_tracker.record_reply("company_2", "no_response")
        reply_tracker.record_reply("company_3", "no_response")
        reply_tracker.record_reply("company_4", "no_response")
        rate = reply_tracker.get_reply_rate()
        assert rate == 25.0

    def test_positive_reply_rate_50_percent(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive")
        reply_tracker.record_reply("company_2", "negative")
        rate = reply_tracker.get_positive_reply_rate()
        assert rate == 50.0

    def test_reply_time_zero(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive", reply_time_seconds=0.0)
        avg = reply_tracker.get_avg_reply_time()
        assert avg == 0.0

    def test_reply_time_mixed(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive", reply_time_seconds=100.0)
        reply_tracker.record_reply("company_2", "positive", reply_time_seconds=None)
        avg = reply_tracker.get_avg_reply_time()
        assert avg == 100.0


# --- MeetingTracker Batch 2 ---

class TestMeetingTrackerBatch2:
    def test_meeting_rate_75_percent(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "completed")
        meeting_tracker.record_meeting("company_2", "completed")
        meeting_tracker.record_meeting("company_3", "completed")
        meeting_tracker.record_meeting("company_4", "cancelled")
        rate = meeting_tracker.get_meeting_rate()
        assert rate == 75.0

    def test_no_show_rate_25_percent(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "completed")
        meeting_tracker.record_meeting("company_2", "no_show")
        meeting_tracker.record_meeting("company_3", "completed")
        meeting_tracker.record_meeting("company_4", "completed")
        rate = meeting_tracker.get_no_show_rate()
        assert rate == 25.0

    def test_duration_zero(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "completed", duration_minutes=0.0)
        avg = meeting_tracker.get_avg_duration()
        assert avg == 0.0


# --- ProposalTracker Batch 2 ---

class TestProposalTrackerBatch2:
    def test_proposal_rate_60_percent(self, proposal_tracker: ProposalTracker) -> None:
        for i in range(6):
            proposal_tracker.record_proposal(f"company_{i}", "sent")
        for i in range(4):
            proposal_tracker.record_proposal(f"company_{i + 6}", "created")
        rate = proposal_tracker.get_proposal_rate()
        assert rate == 60.0

    def test_acceptance_rate_33_percent(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "sent")
        proposal_tracker.record_proposal("company_1", "accepted")
        proposal_tracker.record_proposal("company_2", "sent")
        proposal_tracker.record_proposal("company_2", "rejected")
        proposal_tracker.record_proposal("company_3", "sent")
        proposal_tracker.record_proposal("company_3", "rejected")
        rate = proposal_tracker.get_acceptance_rate()
        assert rate == pytest.approx(33.33, rel=0.01)


# --- DealTracker Batch 2 ---

class TestDealTrackerBatch2:
    def test_win_rate_33_percent(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won")
        deal_tracker.record_deal("company_2", "lost")
        deal_tracker.record_deal("company_3", "lost")
        rate = deal_tracker.get_win_rate()
        assert rate == pytest.approx(33.33, rel=0.01)

    def test_avg_deal_size_with_zero(self, deal_tracker: DealTracker) -> None:
        avg = deal_tracker.get_avg_deal_size()
        assert avg == 0.0

    def test_revenue_by_unknown_service(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won", revenue=50000.0, service_sold="")
        result = deal_tracker.get_revenue_by_service()
        assert result["unknown"] == 50000.0


# --- TimelineEngine Batch 2 ---

class TestTimelineEngineBatch2:
    def test_time_in_stage_none(self, timeline_engine: TimelineEngine) -> None:
        duration = timeline_engine.get_time_in_stage("company_1", "REVENUE_READY")
        assert duration is None

    def test_total_sales_cycle_none(self, timeline_engine: TimelineEngine) -> None:
        cycle = timeline_engine.get_total_sales_cycle("company_1")
        assert cycle is None

    def test_avg_time_to_stage_none(self, timeline_engine: TimelineEngine) -> None:
        avg = timeline_engine.get_avg_time_to_stage("REVENUE_READY")
        assert avg is None

    def test_multiple_companies_at_same_stage(self, timeline_engine: TimelineEngine) -> None:
        for i in range(10):
            timeline_engine.add_event(f"company_{i}", "REVENUE_READY")
        companies = timeline_engine.get_companies_at_stage("REVENUE_READY")
        assert len(companies) == 10


# --- ConnectorRoiEngine Batch 2 ---

class TestConnectorRoiEngineBatch2:
    def test_calculate_with_zeros(self, connector_roi: ConnectorRoiEngine) -> None:
        roi = connector_roi.calculate("nonexistent")
        assert roi.signals == 0
        assert roi.companies == 0
        assert roi.revenue_ready == 0
        assert roi.replies == 0
        assert roi.meetings == 0
        assert roi.deals == 0
        assert roi.revenue == 0.0
        assert roi.reply_rate == 0.0
        assert roi.meeting_rate == 0.0
        assert roi.win_rate == 0.0

    def test_rank_by_replies(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_reply("github")
        connector_roi.record_reply("github")
        connector_roi.record_reply("linkedin")
        ranked = connector_roi.rank_by_replies()
        assert ranked[0].connector == "github"


# --- IndustryRoiEngine Batch 2 ---

class TestIndustryRoiEngineBatch2:
    def test_calculate_with_zeros(self, industry_roi: IndustryRoiEngine) -> None:
        roi = industry_roi.calculate("nonexistent")
        assert roi.companies == 0
        assert roi.revenue_ready == 0
        assert roi.replies == 0
        assert roi.meetings == 0
        assert roi.deals == 0
        assert roi.revenue == 0.0

    def test_rank_by_reply_rate(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_revenue_ready("healthcare")
        industry_roi.record_reply("healthcare")
        industry_roi.record_revenue_ready("fintech")
        ranked = industry_roi.rank_by_reply_rate()
        assert ranked[0].industry == "healthcare"


# --- ServiceRoiEngine Batch 2 ---

class TestServiceRoiEngineBatch2:
    def test_calculate_with_zeros(self, service_roi: ServiceRoiEngine) -> None:
        roi = service_roi.calculate("nonexistent")
        assert roi.companies == 0
        assert roi.replies == 0
        assert roi.meetings == 0
        assert roi.deals == 0
        assert roi.revenue == 0.0


# --- PersonaRoiEngine Batch 2 ---

class TestPersonaRoiEngineBatch2:
    def test_calculate_with_zeros(self, persona_roi: PersonaRoiEngine) -> None:
        roi = persona_roi.calculate("nonexistent")
        assert roi.contacted == 0
        assert roi.replies == 0
        assert roi.meetings == 0
        assert roi.deals == 0
        assert roi.revenue == 0.0


# --- TriggerRoiEngine Batch 2 ---

class TestTriggerRoiEngineBatch2:
    def test_calculate_with_zeros(self, trigger_roi: TriggerRoiEngine) -> None:
        roi = trigger_roi.calculate("nonexistent")
        assert roi.companies == 0
        assert roi.replies == 0
        assert roi.meetings == 0
        assert roi.deals == 0
        assert roi.revenue == 0.0


# --- ObjectionEngine Batch 2 ---

class TestObjectionEngineBatch2:
    def test_objection_rate_by_industry(self, objection_engine: ObjectionEngine) -> None:
        objection_engine.record_objection("company_1", "no_budget", industry="healthcare")
        objection_engine.record_objection("company_2", "no_budget", industry="healthcare")
        objection_engine.record_objection("company_3", "no_budget", industry="fintech")
        rates = objection_engine.get_objection_rate_by_industry()
        assert rates["healthcare"] == 2
        assert rates["fintech"] == 1

    def test_objection_rate_by_service(self, objection_engine: ObjectionEngine) -> None:
        objection_engine.record_objection("company_1", "no_budget", service="ai_automation")
        objection_engine.record_objection("company_2", "no_budget", service="crm")
        rates = objection_engine.get_objection_rate_by_service()
        assert rates["ai_automation"] == 1
        assert rates["crm"] == 1


# --- OutcomeTracker Batch 2 ---

class TestOutcomeTrackerBatch2:
    def test_get_outcomes_by_service(self, outcome_tracker: OutcomeTracker) -> None:
        outcome_tracker.record_outcome("company_1", "won", service_sold="ai_automation")
        outcome_tracker.record_outcome("company_2", "won", service_sold="crm")
        outcome_tracker.record_outcome("company_3", "won", service_sold="ai_automation")
        result = outcome_tracker.get_outcomes_by_service()
        assert len(result["ai_automation"]) == 2
        assert len(result["crm"]) == 1


# --- FunnelEngine Batch 2 ---

class TestFunnelEngineBatch2:
    def test_conversion_with_zero_from_count(self, funnel_engine: FunnelEngine) -> None:
        result = funnel_engine.calculate_conversion("WON", "LOST")
        assert result["from_count"] == 0
        assert result["to_count"] == 0
        assert result["conversion_rate"] == 0.0


# --- ValidationEngine Batch 2 ---

class TestValidationEngineBatch2:
    def test_record_objection(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_objection(
            "company_1", "no_budget",
            industry="healthcare", service="ai_automation",
        )
        assert result["ok"] is True
        assert result["category"] == "no_budget"

    def test_dashboard_after_objection(self, validation_engine: ValidationEngine) -> None:
        validation_engine.record_objection("company_1", "no_budget")
        dashboard = validation_engine.get_dashboard_data()
        assert "funnel" in dashboard


# --- CalibrationEngine Batch 2 ---

class TestCalibrationEngineBatch2:
    def test_empty_calibration_all(self, calibration_engine: CalibrationEngine) -> None:
        connector_cal = calibration_engine.get_connector_calibration()
        industry_cal = calibration_engine.get_industry_calibration()
        service_cal = calibration_engine.get_service_calibration()
        persona_cal = calibration_engine.get_persona_calibration()
        trigger_cal = calibration_engine.get_trigger_calibration()
        assert connector_cal == []
        assert industry_cal == []
        assert service_cal == []
        assert persona_cal == []
        assert trigger_cal == []


# --- ValidationMetrics Batch 2 ---

class TestValidationMetricsBatch2:
    def test_metrics_objection_distribution(self) -> None:
        metrics = ValidationMetrics()
        metrics.objection_engine.record_objection("company_1", "no_budget")
        metrics.objection_engine.record_objection("company_2", "no_budget")
        metrics.objection_engine.record_objection("company_3", "wrong_timing")
        result = metrics.get_all_metrics()
        assert result["top_objections"][0]["category"] == "no_budget"
        assert result["top_objections"][0]["count"] == 2

    def test_metrics_best_connector(self) -> None:
        metrics = ValidationMetrics()
        metrics.connector_roi.record_deal("linkedin", revenue=50000.0)
        result = metrics.get_all_metrics()
        assert result["best_connector"] == "linkedin"
