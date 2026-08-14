"""Additional comprehensive tests for validation engine — batch 7."""

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

# --- LeadValidator Batch 7 ---

class TestLeadValidatorBatch7:
    def test_record_all_stages(self, lead_validator: LeadValidator) -> None:
        from validation_engine import VALIDATION_STAGES
        for stage in VALIDATION_STAGES:
            event = lead_validator.record_transition("company_1", stage)
            assert event.stage == stage
        assert lead_validator.get_company_stage("company_1") == VALIDATION_STAGES[-1]

    def test_conversion_rate_100(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        rate = lead_validator.calculate_conversion_rate("REVENUE_READY", "CONTACTED")
        assert rate == 100.0

    def test_conversion_rate_0(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        rate = lead_validator.calculate_conversion_rate("REVENUE_READY", "CONTACTED")
        assert rate == 0.0

    def test_conversion_rate_50(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_2", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        rate = lead_validator.calculate_conversion_rate("REVENUE_READY", "CONTACTED")
        assert rate == 50.0

    def test_conversion_rate_33(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_2", "REVENUE_READY")
        lead_validator.record_transition("company_3", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        rate = lead_validator.calculate_conversion_rate("REVENUE_READY", "CONTACTED")
        assert rate == pytest.approx(33.33, rel=0.01)

    def test_conversion_rate_67(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_2", "REVENUE_READY")
        lead_validator.record_transition("company_3", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        lead_validator.record_transition("company_2", "CONTACTED")
        rate = lead_validator.calculate_conversion_rate("REVENUE_READY", "CONTACTED")
        assert rate == pytest.approx(66.67, rel=0.01)

    def test_funnel_7_stages(self, lead_validator: LeadValidator) -> None:
        stages = [
            "REVENUE_READY", "CONTACTED", "EMAIL_OPENED",
            "REPLIED", "MEETING_BOOKED", "PROPOSAL_SENT", "WON",
        ]
        for i, stage in enumerate(stages):
            lead_validator.record_transition(f"company_{i}", stage)
        funnel = lead_validator.get_funnel()
        assert len(funnel) > 0

    def test_events_append_only(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        lead_validator.record_transition("company_1", "REPLIED")
        events = lead_validator.get_events_by_company("company_1")
        assert len(events) == 3
        assert events[0].stage == "REVENUE_READY"
        assert events[1].stage == "CONTACTED"
        assert events[2].stage == "REPLIED"


# --- ReplyTracker Batch 7 ---

class TestReplyTrackerBatch7:
    def test_reply_rate_100(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive")
        reply_tracker.record_reply("company_2", "negative")
        rate = reply_tracker.get_reply_rate()
        assert rate == 100.0

    def test_reply_rate_0(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "no_response")
        rate = reply_tracker.get_reply_rate()
        assert rate == 0.0

    def test_reply_rate_50(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive")
        reply_tracker.record_reply("company_2", "no_response")
        rate = reply_tracker.get_reply_rate()
        assert rate == 50.0

    def test_positive_reply_rate_100(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive")
        rate = reply_tracker.get_positive_reply_rate()
        assert rate == 100.0

    def test_positive_reply_rate_0(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "negative")
        rate = reply_tracker.get_positive_reply_rate()
        assert rate == 0.0

    def test_positive_reply_rate_50(self, reply_tracker: ReplyTracker) -> None:
        reply_tracker.record_reply("company_1", "positive")
        reply_tracker.record_reply("company_2", "negative")
        rate = reply_tracker.get_positive_reply_rate()
        assert rate == 50.0


# --- MeetingTracker Batch 7 ---

class TestMeetingTrackerBatch7:
    def test_meeting_rate_100(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "completed")
        rate = meeting_tracker.get_meeting_rate()
        assert rate == 100.0

    def test_meeting_rate_0(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "cancelled")
        rate = meeting_tracker.get_meeting_rate()
        assert rate == 0.0

    def test_meeting_rate_50(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "completed")
        meeting_tracker.record_meeting("company_2", "cancelled")
        rate = meeting_tracker.get_meeting_rate()
        assert rate == 50.0

    def test_no_show_rate_100(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "no_show")
        rate = meeting_tracker.get_no_show_rate()
        assert rate == 100.0

    def test_no_show_rate_0(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "completed")
        rate = meeting_tracker.get_no_show_rate()
        assert rate == 0.0

    def test_no_show_rate_25(self, meeting_tracker: MeetingTracker) -> None:
        meeting_tracker.record_meeting("company_1", "completed")
        meeting_tracker.record_meeting("company_2", "completed")
        meeting_tracker.record_meeting("company_3", "completed")
        meeting_tracker.record_meeting("company_4", "no_show")
        rate = meeting_tracker.get_no_show_rate()
        assert rate == 25.0


# --- ProposalTracker Batch 7 ---

class TestProposalTrackerBatch7:
    def test_proposal_rate_100(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "sent")
        rate = proposal_tracker.get_proposal_rate()
        assert rate == 100.0

    def test_proposal_rate_0(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "created")
        rate = proposal_tracker.get_proposal_rate()
        assert rate == 0.0

    def test_proposal_rate_50(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "sent")
        proposal_tracker.record_proposal("company_2", "created")
        rate = proposal_tracker.get_proposal_rate()
        assert rate == 50.0

    def test_acceptance_rate_100(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "sent")
        proposal_tracker.record_proposal("company_1", "accepted")
        rate = proposal_tracker.get_acceptance_rate()
        assert rate == 100.0

    def test_acceptance_rate_0(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "sent")
        proposal_tracker.record_proposal("company_1", "rejected")
        rate = proposal_tracker.get_acceptance_rate()
        assert rate == 0.0

    def test_acceptance_rate_50(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "sent")
        proposal_tracker.record_proposal("company_1", "accepted")
        proposal_tracker.record_proposal("company_2", "sent")
        proposal_tracker.record_proposal("company_2", "rejected")
        rate = proposal_tracker.get_acceptance_rate()
        assert rate == 50.0


# --- DealTracker Batch 7 ---

class TestDealTrackerBatch7:
    def test_win_rate_100(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won")
        rate = deal_tracker.get_win_rate()
        assert rate == 100.0

    def test_win_rate_0(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "lost")
        rate = deal_tracker.get_win_rate()
        assert rate == 0.0

    def test_win_rate_50(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won")
        deal_tracker.record_deal("company_2", "lost")
        rate = deal_tracker.get_win_rate()
        assert rate == 50.0

    def test_win_rate_33(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won")
        deal_tracker.record_deal("company_2", "lost")
        deal_tracker.record_deal("company_3", "lost")
        rate = deal_tracker.get_win_rate()
        assert rate == pytest.approx(33.33, rel=0.01)

    def test_avg_deal_size_100(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won", revenue=100000.0)
        avg = deal_tracker.get_avg_deal_size()
        assert avg == 100000.0

    def test_avg_deal_size_50(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won", revenue=100000.0)
        deal_tracker.record_deal("company_2", "won", revenue=50000.0)
        avg = deal_tracker.get_avg_deal_size()
        assert avg == 75000.0

    def test_total_revenue_100(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won", revenue=100000.0)
        total = deal_tracker.get_total_revenue()
        assert total == 100000.0

    def test_total_revenue_150(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won", revenue=100000.0)
        deal_tracker.record_deal("company_2", "won", revenue=50000.0)
        total = deal_tracker.get_total_revenue()
        assert total == 150000.0


# --- TimelineEngine Batch 7 ---

class TestTimelineEngineBatch7:
    def test_latest_stage(self, timeline_engine: TimelineEngine) -> None:
        timeline_engine.add_event("company_1", "REVENUE_READY")
        timeline_engine.add_event("company_1", "CONTACTED")
        assert timeline_engine.get_latest_stage("company_1") == "CONTACTED"

    def test_stage_history(self, timeline_engine: TimelineEngine) -> None:
        timeline_engine.add_event("company_1", "REVENUE_READY")
        timeline_engine.add_event("company_1", "CONTACTED")
        timeline_engine.add_event("company_1", "REPLIED")
        history = timeline_engine.get_stage_history("company_1")
        assert history == ["REVENUE_READY", "CONTACTED", "REPLIED"]

    def test_companies_at_stage(self, timeline_engine: TimelineEngine) -> None:
        timeline_engine.add_event("company_1", "REVENUE_READY")
        timeline_engine.add_event("company_1", "CONTACTED")
        timeline_engine.add_event("company_2", "REVENUE_READY")
        companies = timeline_engine.get_companies_at_stage("REVENUE_READY")
        assert companies == ["company_2"]

    def test_companies_who_reached_stage(self, timeline_engine: TimelineEngine) -> None:
        timeline_engine.add_event("company_1", "REVENUE_READY")
        timeline_engine.add_event("company_1", "CONTACTED")
        timeline_engine.add_event("company_2", "REVENUE_READY")
        companies = timeline_engine.get_companies_who_reached_stage("CONTACTED")
        assert companies == ["company_1"]


# --- ConnectorRoiEngine Batch 7 ---

class TestConnectorRoiEngineBatch7:
    def test_calculate(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_deal("linkedin", revenue=50000.0)
        roi = connector_roi.calculate("linkedin")
        assert roi.revenue == 50000.0
        assert roi.deals == 1

    def test_ranking(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_deal("linkedin", revenue=50000.0)
        connector_roi.record_deal("github", revenue=10000.0)
        ranked = connector_roi.rank_by_revenue()
        assert ranked[0].connector == "linkedin"
        assert ranked[1].connector == "github"

    def test_best_connector(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_deal("linkedin", revenue=50000.0)
        best = connector_roi.get_best_connector()
        assert best is not None
        assert best.connector == "linkedin"

    def test_worst_connector(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_deal("linkedin", revenue=50000.0)
        connector_roi.record_deal("github", revenue=10000.0)
        worst = connector_roi.get_worst_connector()
        assert worst is not None
        assert worst.connector == "github"


# --- IndustryRoiEngine Batch 7 ---

class TestIndustryRoiEngineBatch7:
    def test_calculate(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_deal("healthcare", revenue=100000.0)
        roi = industry_roi.calculate("healthcare")
        assert roi.revenue == 100000.0
        assert roi.deals == 1

    def test_ranking(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_deal("healthcare", revenue=100000.0)
        industry_roi.record_deal("fintech", revenue=200000.0)
        ranked = industry_roi.rank_by_revenue()
        assert ranked[0].industry == "fintech"
        assert ranked[1].industry == "healthcare"

    def test_best_industry(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_deal("healthcare", revenue=100000.0)
        best = industry_roi.get_best_industry()
        assert best is not None
        assert best.industry == "healthcare"


# --- ServiceRoiEngine Batch 7 ---

class TestServiceRoiEngineBatch7:
    def test_calculate(self, service_roi: ServiceRoiEngine) -> None:
        service_roi.record_deal("ai_automation", revenue=75000.0)
        roi = service_roi.calculate("ai_automation")
        assert roi.revenue == 75000.0
        assert roi.deals == 1

    def test_ranking(self, service_roi: ServiceRoiEngine) -> None:
        service_roi.record_deal("ai_automation", revenue=75000.0)
        service_roi.record_deal("crm", revenue=100000.0)
        ranked = service_roi.rank_by_revenue()
        assert ranked[0].service == "crm"
        assert ranked[1].service == "ai_automation"

    def test_best_service(self, service_roi: ServiceRoiEngine) -> None:
        service_roi.record_deal("ai_automation", revenue=75000.0)
        best = service_roi.get_best_service()
        assert best is not None
        assert best.service == "ai_automation"


# --- PersonaRoiEngine Batch 7 ---

class TestPersonaRoiEngineBatch7:
    def test_calculate(self, persona_roi: PersonaRoiEngine) -> None:
        persona_roi.record_deal("founder", revenue=100000.0)
        roi = persona_roi.calculate("founder")
        assert roi.revenue == 100000.0
        assert roi.deals == 1

    def test_ranking(self, persona_roi: PersonaRoiEngine) -> None:
        persona_roi.record_deal("founder", revenue=100000.0)
        persona_roi.record_deal("cto", revenue=200000.0)
        ranked = persona_roi.rank_by_revenue()
        assert ranked[0].persona == "cto"
        assert ranked[1].persona == "founder"

    def test_best_persona(self, persona_roi: PersonaRoiEngine) -> None:
        persona_roi.record_deal("founder", revenue=100000.0)
        best = persona_roi.get_best_persona()
        assert best is not None
        assert best.persona == "founder"


# --- TriggerRoiEngine Batch 7 ---

class TestTriggerRoiEngineBatch7:
    def test_calculate(self, trigger_roi: TriggerRoiEngine) -> None:
        trigger_roi.record_deal("funding", revenue=100000.0)
        roi = trigger_roi.calculate("funding")
        assert roi.revenue == 100000.0
        assert roi.deals == 1

    def test_ranking(self, trigger_roi: TriggerRoiEngine) -> None:
        trigger_roi.record_deal("funding", revenue=100000.0)
        trigger_roi.record_deal("hiring", revenue=200000.0)
        ranked = trigger_roi.rank_by_revenue()
        assert ranked[0].trigger == "hiring"
        assert ranked[1].trigger == "funding"

    def test_best_trigger(self, trigger_roi: TriggerRoiEngine) -> None:
        trigger_roi.record_deal("funding", revenue=100000.0)
        best = trigger_roi.get_best_trigger()
        assert best is not None
        assert best.trigger == "funding"


# --- ObjectionEngine Batch 7 ---

class TestObjectionEngineBatch7:
    def test_record_objection(self, objection_engine: ObjectionEngine) -> None:
        event = objection_engine.record_objection("company_1", "no_budget")
        assert event.company_id == "company_1"
        assert event.category == "no_budget"

    def test_top_objections(self, objection_engine: ObjectionEngine) -> None:
        for _ in range(5):
            objection_engine.record_objection("company_1", "no_budget")
        for _ in range(3):
            objection_engine.record_objection("company_2", "wrong_timing")
        top = objection_engine.get_top_objections()
        assert top[0]["category"] == "no_budget"
        assert top[0]["count"] == 5

    def test_category_counts(self, objection_engine: ObjectionEngine) -> None:
        objection_engine.record_objection("company_1", "no_budget")
        objection_engine.record_objection("company_2", "no_budget")
        objection_engine.record_objection("company_3", "wrong_timing")
        counts = objection_engine.get_category_counts()
        assert counts["no_budget"] == 2
        assert counts["wrong_timing"] == 1


# --- OutcomeTracker Batch 7 ---

class TestOutcomeTrackerBatch7:
    def test_record_outcome(self, outcome_tracker: OutcomeTracker) -> None:
        event = outcome_tracker.record_outcome("company_1", "won", revenue=50000.0)
        assert event.company_id == "company_1"
        assert event.status == "won"
        assert event.revenue == 50000.0

    def test_total_revenue(self, outcome_tracker: OutcomeTracker) -> None:
        outcome_tracker.record_outcome("company_1", "won", revenue=50000.0)
        outcome_tracker.record_outcome("company_2", "won", revenue=75000.0)
        total = outcome_tracker.get_total_revenue()
        assert total == 125000.0

    def test_win_rate(self, outcome_tracker: OutcomeTracker) -> None:
        outcome_tracker.record_outcome("company_1", "won")
        outcome_tracker.record_outcome("company_2", "lost")
        rate = outcome_tracker.get_win_rate()
        assert rate == 50.0


# --- FunnelEngine Batch 7 ---

class TestFunnelEngineBatch7:
    def test_calculate_funnel(self, funnel_engine: FunnelEngine) -> None:
        funnel = funnel_engine.calculate_funnel()
        assert len(funnel) > 0

    def test_calculate_conversion(self, funnel_engine: FunnelEngine) -> None:
        result = funnel_engine.calculate_conversion("REVENUE_READY", "CONTACTED")
        assert result["conversion_rate"] == 0.0

    def test_get_biggest_bottleneck(self, funnel_engine: FunnelEngine) -> None:
        bottleneck = funnel_engine.get_biggest_bottleneck()
        assert "stage" in bottleneck


# --- ValidationEngine Batch 7 ---

class TestValidationEngineBatch7:
    def test_record_email_sent(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_email_sent("company_1")
        assert result["ok"] is True

    def test_record_reply(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_reply("company_1", "positive")
        assert result["ok"] is True

    def test_record_meeting(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_meeting("company_1", "completed")
        assert result["ok"] is True

    def test_record_proposal(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_proposal("company_1", "sent")
        assert result["ok"] is True

    def test_record_deal(self, validation_engine: ValidationEngine) -> None:
        result = validation_engine.record_deal("company_1", "won", revenue=100000.0)
        assert result["ok"] is True

    def test_get_company_timeline(self, validation_engine: ValidationEngine) -> None:
        validation_engine.record_email_sent("company_1")
        timeline = validation_engine.get_company_timeline("company_1")
        assert len(timeline) > 0

    def test_get_funnel(self, validation_engine: ValidationEngine) -> None:
        funnel = validation_engine.get_funnel()
        assert len(funnel) > 0

    def test_get_dashboard_data(self, validation_engine: ValidationEngine) -> None:
        dashboard = validation_engine.get_dashboard_data()
        assert "generated_at" in dashboard
        assert "total_revenue" in dashboard


# --- CalibrationEngine Batch 7 ---

class TestCalibrationEngineBatch7:
    def test_get_calibration_summary(self, calibration_engine: CalibrationEngine) -> None:
        summary = calibration_engine.get_calibration_summary()
        assert "connector_ranking" in summary
        assert "industry_ranking" in summary
        assert "service_ranking" in summary
        assert "persona_ranking" in summary
        assert "trigger_ranking" in summary

    def test_get_connector_calibration(self, calibration_engine: CalibrationEngine) -> None:
        result = calibration_engine.get_connector_calibration()
        assert isinstance(result, list)

    def test_get_industry_calibration(self, calibration_engine: CalibrationEngine) -> None:
        result = calibration_engine.get_industry_calibration()
        assert isinstance(result, list)

    def test_get_service_calibration(self, calibration_engine: CalibrationEngine) -> None:
        result = calibration_engine.get_service_calibration()
        assert isinstance(result, list)

    def test_get_persona_calibration(self, calibration_engine: CalibrationEngine) -> None:
        result = calibration_engine.get_persona_calibration()
        assert isinstance(result, list)

    def test_get_trigger_calibration(self, calibration_engine: CalibrationEngine) -> None:
        result = calibration_engine.get_trigger_calibration()
        assert isinstance(result, list)
