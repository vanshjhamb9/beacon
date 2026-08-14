"""Additional comprehensive tests for validation engine — batch 3."""

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

# --- LeadValidator Batch 3 ---

class TestLeadValidatorBatch3:
    def test_funnel_stage_counts(self, lead_validator: LeadValidator) -> None:
        for i in range(10):
            lead_validator.record_transition(f"company_{i}", "REVENUE_READY")
        for i in range(8):
            lead_validator.record_transition(f"company_{i}", "CONTACTED")
        for i in range(6):
            lead_validator.record_transition(f"company_{i}", "EMAIL_OPENED")
        for i in range(4):
            lead_validator.record_transition(f"company_{i}", "REPLIED")
        for i in range(2):
            lead_validator.record_transition(f"company_{i}", "MEETING_BOOKED")
        lead_validator.record_transition("company_0", "PROPOSAL_SENT")
        lead_validator.record_transition("company_0", "WON")
        funnel = lead_validator.get_funnel()
        rr = next(f for f in funnel if f["stage"] == "REVENUE_READY")
        contacted = next(f for f in funnel if f["stage"] == "CONTACTED")
        replied = next(f for f in funnel if f["stage"] == "REPLIED")
        won = next(f for f in funnel if f["stage"] == "WON")
        assert rr["count"] == 10
        assert contacted["count"] == 8
        assert replied["count"] == 4
        assert won["count"] == 1

    def test_events_append_only(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        events = lead_validator.get_events_by_company("company_1")
        assert len(events) == 2
        assert events[0].stage == "REVENUE_READY"
        assert events[1].stage == "CONTACTED"


# --- ReplyTracker Batch 3 ---

class TestReplyTrackerBatch3:
    def test_reply_type_distribution(self, reply_tracker: ReplyTracker) -> None:
        for _ in range(10):
            reply_tracker.record_reply("company_1", "positive")
        for _ in range(5):
            reply_tracker.record_reply("company_2", "negative")
        for _ in range(3):
            reply_tracker.record_reply("company_3", "bounce")
        counts = reply_tracker.get_reply_type_counts()
        assert counts["positive"] == 10
        assert counts["negative"] == 5
        assert counts["bounce"] == 3

    def test_replies_by_connector_multiple(self, reply_tracker: ReplyTracker) -> None:
        for _ in range(5):
            reply_tracker.record_reply("company_1", "positive", source="linkedin")
        for _ in range(3):
            reply_tracker.record_reply("company_2", "positive", source="github")
        linkedin = reply_tracker.get_replies_by_connector("linkedin")
        github = reply_tracker.get_replies_by_connector("github")
        assert len(linkedin) == 5
        assert len(github) == 3


# --- MeetingTracker Batch 3 ---

class TestMeetingTrackerBatch3:
    def test_meeting_type_distribution(self, meeting_tracker: MeetingTracker) -> None:
        for _ in range(10):
            meeting_tracker.record_meeting("company_1", "completed")
        for _ in range(3):
            meeting_tracker.record_meeting("company_2", "cancelled")
        for _ in range(2):
            meeting_tracker.record_meeting("company_3", "no_show")
        counts = meeting_tracker.get_meeting_type_counts()
        assert counts["completed"] == 10
        assert counts["cancelled"] == 3
        assert counts["no_show"] == 2


# --- ProposalTracker Batch 3 ---

class TestProposalTrackerBatch3:
    def test_status_distribution(self, proposal_tracker: ProposalTracker) -> None:
        for _ in range(10):
            proposal_tracker.record_proposal("company_1", "sent")
        for _ in range(5):
            proposal_tracker.record_proposal("company_2", "accepted")
        for _ in range(3):
            proposal_tracker.record_proposal("company_3", "rejected")
        counts = proposal_tracker.get_status_counts()
        assert counts["sent"] == 10
        assert counts["accepted"] == 5
        assert counts["rejected"] == 3


# --- DealTracker Batch 3 ---

class TestDealTrackerBatch3:
    def test_deals_by_status_multiple(self, deal_tracker: DealTracker) -> None:
        for _ in range(10):
            deal_tracker.record_deal("company_1", "won")
        for _ in range(5):
            deal_tracker.record_deal("company_2", "lost")
        for _ in range(3):
            deal_tracker.record_deal("company_3", "paused")
        counts = deal_tracker.get_deals_by_status()
        assert counts["won"] == 10
        assert counts["lost"] == 5
        assert counts["paused"] == 3

    def test_revenue_by_service_multiple(self, deal_tracker: DealTracker) -> None:
        deal_tracker.record_deal("company_1", "won", revenue=100000.0, service_sold="ai_automation")
        deal_tracker.record_deal("company_2", "won", revenue=200000.0, service_sold="crm")
        deal_tracker.record_deal("company_3", "won", revenue=50000.0, service_sold="ai_automation")
        deal_tracker.record_deal("company_4", "won", revenue=75000.0, service_sold="website")
        result = deal_tracker.get_revenue_by_service()
        assert result["ai_automation"] == 150000.0
        assert result["crm"] == 200000.0
        assert result["website"] == 75000.0


# --- TimelineEngine Batch 3 ---

class TestTimelineEngineBatch3:
    def test_stage_summary_with_data(self, timeline_engine: TimelineEngine) -> None:
        for i in range(5):
            timeline_engine.add_event(f"company_{i}", "REVENUE_READY")
        for i in range(3):
            timeline_engine.add_event(f"company_{i}", "CONTACTED")
        timeline_engine.add_event("company_0", "REPLIED")
        summary = timeline_engine.build_stage_summary()
        assert summary["REVENUE_READY"]["current_count"] == 2
        assert summary["REVENUE_READY"]["total_reached"] == 5
        assert summary["CONTACTED"]["current_count"] == 2
        assert summary["CONTACTED"]["total_reached"] == 3
        assert summary["REPLIED"]["current_count"] == 1
        assert summary["REPLIED"]["total_reached"] == 1


# --- ConnectorRoiEngine Batch 3 ---

class TestConnectorRoiEngineBatch3:
    def test_ranking_with_equal_revenue(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_deal("a", revenue=10000.0)
        connector_roi.record_deal("b", revenue=10000.0)
        connector_roi.record_deal("c", revenue=10000.0)
        ranked = connector_roi.rank_by_revenue()
        assert len(ranked) == 3
        assert all(r.revenue == 10000.0 for r in ranked)


# --- IndustryRoiEngine Batch 3 ---

class TestIndustryRoiEngineBatch3:
    def test_ranking_with_equal_revenue(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_deal("a", revenue=10000.0)
        industry_roi.record_deal("b", revenue=10000.0)
        industry_roi.record_deal("c", revenue=10000.0)
        ranked = industry_roi.rank_by_revenue()
        assert len(ranked) == 3
        assert all(r.revenue == 10000.0 for r in ranked)


# --- ServiceRoiEngine Batch 3 ---

class TestServiceRoiEngineBatch3:
    def test_ranking_with_equal_revenue(self, service_roi: ServiceRoiEngine) -> None:
        service_roi.record_deal("a", revenue=10000.0)
        service_roi.record_deal("b", revenue=10000.0)
        service_roi.record_deal("c", revenue=10000.0)
        ranked = service_roi.rank_by_revenue()
        assert len(ranked) == 3
        assert all(r.revenue == 10000.0 for r in ranked)


# --- PersonaRoiEngine Batch 3 ---

class TestPersonaRoiEngineBatch3:
    def test_ranking_with_equal_revenue(self, persona_roi: PersonaRoiEngine) -> None:
        persona_roi.record_deal("a", revenue=10000.0)
        persona_roi.record_deal("b", revenue=10000.0)
        persona_roi.record_deal("c", revenue=10000.0)
        ranked = persona_roi.rank_by_revenue()
        assert len(ranked) == 3
        assert all(r.revenue == 10000.0 for r in ranked)


# --- TriggerRoiEngine Batch 3 ---

class TestTriggerRoiEngineBatch3:
    def test_ranking_with_equal_revenue(self, trigger_roi: TriggerRoiEngine) -> None:
        trigger_roi.record_deal("a", revenue=10000.0)
        trigger_roi.record_deal("b", revenue=10000.0)
        trigger_roi.record_deal("c", revenue=10000.0)
        ranked = trigger_roi.rank_by_revenue()
        assert len(ranked) == 3
        assert all(r.revenue == 10000.0 for r in ranked)


# --- ObjectionEngine Batch 3 ---

class TestObjectionEngineBatch3:
    def test_top_objections_limit(self, objection_engine: ObjectionEngine) -> None:
        for _ in range(10):
            objection_engine.record_objection("company_1", "no_budget")
        for _ in range(5):
            objection_engine.record_objection("company_2", "wrong_timing")
        for _ in range(3):
            objection_engine.record_objection("company_3", "no_need")
        top = objection_engine.get_top_objections(limit=2)
        assert len(top) == 2
        assert top[0]["category"] == "no_budget"
        assert top[1]["category"] == "wrong_timing"


# --- OutcomeTracker Batch 3 ---

class TestOutcomeTrackerBatch3:
    def test_revenue_by_service_with_zero(self, outcome_tracker: OutcomeTracker) -> None:
        outcome_tracker.record_outcome(
            "company_1", "won",
            revenue=0.0, service_sold="ai_automation"
        )
        result = outcome_tracker.get_revenue_by_service()
        assert result["ai_automation"] == 0.0


# --- FunnelEngine Batch 3 ---

class TestFunnelEngineBatch3:
    def test_conversion_summary_with_full_data(
        self,
        funnel_engine: FunnelEngine,
        lead_validator: LeadValidator,
    ) -> None:
        for i in range(20):
            lead_validator.record_transition(f"company_{i}", "REVENUE_READY")
        for i in range(15):
            lead_validator.record_transition(f"company_{i}", "CONTACTED")
        for i in range(10):
            lead_validator.record_transition(f"company_{i}", "REPLIED")
        for i in range(5):
            lead_validator.record_transition(f"company_{i}", "MEETING_BOOKED")
        for i in range(3):
            lead_validator.record_transition(f"company_{i}", "PROPOSAL_SENT")
        for i in range(2):
            lead_validator.record_transition(f"company_{i}", "WON")
        summary = funnel_engine.get_conversion_summary()
        assert summary["total_companies"] == 20
        assert summary["total_won"] == 2
        assert summary["overall_conversion_rate"] == 10.0


# --- ValidationEngine Batch 3 ---

class TestValidationEngineBatch3:
    def test_full_lifecycle_multiple_companies(self, validation_engine: ValidationEngine) -> None:
        for i in range(10):
            validation_engine.record_email_sent(f"company_{i}")
            validation_engine.record_email_opened(f"company_{i}")
            validation_engine.record_reply(f"company_{i}", "positive")
            validation_engine.record_meeting(f"company_{i}", "completed")
            validation_engine.record_proposal(f"company_{i}", "sent")
            validation_engine.record_deal(f"company_{i}", "won", revenue=float(i * 10000))
        dashboard = validation_engine.get_dashboard_data()
        assert dashboard["total_revenue"] == sum(i * 10000 for i in range(10))


# --- CalibrationEngine Batch 3 ---

class TestCalibrationEngineBatch3:
    def test_full_calibration_with_data(self, calibration_engine: CalibrationEngine) -> None:
        calibration_engine.connector_roi.record_deal("linkedin", revenue=100000.0)
        calibration_engine.connector_roi.record_deal("github", revenue=50000.0)
        calibration_engine.industry_roi.record_deal("healthcare", revenue=200000.0)
        calibration_engine.industry_roi.record_deal("fintech", revenue=150000.0)
        calibration_engine.service_roi.record_deal("ai_automation", revenue=100000.0)
        calibration_engine.service_roi.record_deal("crm", revenue=75000.0)
        calibration_engine.persona_roi.record_deal("founder", revenue=100000.0)
        calibration_engine.persona_roi.record_deal("cto", revenue=75000.0)
        calibration_engine.trigger_roi.record_deal("funding", revenue=100000.0)
        calibration_engine.trigger_roi.record_deal("hiring", revenue=75000.0)
        calibration_engine.deal_tracker.record_deal("c1", "won", revenue=100000.0)
        calibration_engine.deal_tracker.record_deal("c2", "won", revenue=75000.0)
        calibration_engine.deal_tracker.record_deal("c3", "lost")
        summary = calibration_engine.get_calibration_summary()
        assert summary["total_revenue"] == 175000.0
        assert summary["win_rate"] == pytest.approx(66.67, rel=0.01)
        assert len(summary["connector_ranking"]) == 2
        assert len(summary["industry_ranking"]) == 2
        assert len(summary["service_ranking"]) == 2
        assert len(summary["persona_ranking"]) == 2
        assert len(summary["trigger_ranking"]) == 2


# --- ValidationMetrics Batch 3 ---

class TestValidationMetricsBatch3:
    def test_metrics_with_all_data(self) -> None:
        metrics = ValidationMetrics()
        for i in range(20):
            metrics.reply_tracker.record_reply(f"company_{i}", "positive")
        for i in range(15):
            metrics.meeting_tracker.record_meeting(f"company_{i}", "completed")
        for i in range(10):
            metrics.proposal_tracker.record_proposal(f"company_{i}", "sent")
        for i in range(5):
            metrics.deal_tracker.record_deal(f"company_{i}", "won", revenue=float(i * 10000))
        for i in range(3):
            metrics.objection_engine.record_objection(f"company_{i}", "no_budget")
        result = metrics.get_all_metrics()
        assert result["total_replies"] == 20
        assert result["total_meetings_completed"] == 15
        assert result["total_proposals_sent"] == 10
        assert result["total_won"] == 5
        assert result["total_revenue"] == 100000.0
        assert result["top_objections"][0]["category"] == "no_budget"
        assert result["top_objections"][0]["count"] == 3
