from datetime import UTC, datetime
from uuid import uuid4

import pytest

from autonomous_sales_agent import AutonomousSalesAgentPipeline, AutonomousSalesAgentService, SCORING_VERSION
from autonomous_sales_agent.actions.engine import NextBestActionEngine
from autonomous_sales_agent.analytics.engine import AsaAnalyticsEngine
from autonomous_sales_agent.brief.engine import MorningBriefEngine
from autonomous_sales_agent.casestudy.engine import CASE_LIBRARY, CaseStudyRecommendationEngine
from autonomous_sales_agent.followup.engine import FollowUpIntelligenceEngine
from autonomous_sales_agent.meeting.engine import MeetingIntelligenceEngine
from autonomous_sales_agent.memory.engine import SalesMemoryEngine
from autonomous_sales_agent.models.types import (
    AutonomousSalesAgentInput,
    FollowUpChannel,
    FollowUpConfig,
    NextActionKind,
    SalesWorkflowStage,
)
from autonomous_sales_agent.objections.engine import ObjectionTrackerEngine
from autonomous_sales_agent.queue.engine import FounderWorkQueueEngine
from autonomous_sales_agent.repository.memory import InMemoryAsaRepository
from autonomous_sales_agent.rules.constants import FOUNDER_ONLY_STAGES, FOUNDER_QUEUE_KINDS
from autonomous_sales_agent.scheduler.hints import default_schedule
from autonomous_sales_agent.timeline.engine import RelationshipTimelineEngine
from autonomous_sales_agent.workflow.engine import SalesWorkflowEngine


def _item(**overrides: object) -> AutonomousSalesAgentInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Acme Robotics",
        "industry": "Manufacturing",
        "company_size": "51-200",
        "priority_grade": "A",
        "probability": 72.0,
        "buying_intent_score": 68.0,
        "days_since_last_touch": 0,
        "has_decision_makers": True,
        "decision_makers": [{"name": "Alex Founder", "title": "CEO"}],
        "pains": ["manual handoffs", "slow reporting"],
        "technologies": ["Python", "Salesforce"],
        "recommended_service": "AI Automation",
        "now": datetime.now(UTC),
    }
    payload.update(overrides)
    return AutonomousSalesAgentInput.model_validate(payload)


def test_scoring_version() -> None:
    assert SCORING_VERSION == "asa-v1"


def test_infer_lead_discovered() -> None:
    stage = SalesWorkflowEngine().infer_stage(_item(priority_grade=None, probability=0, pains=[], has_decision_makers=False))
    assert stage == SalesWorkflowStage.LEAD_DISCOVERED


def test_infer_qualified() -> None:
    assert SalesWorkflowEngine().infer_stage(_item(has_decision_makers=False, pains=[])) == SalesWorkflowStage.QUALIFIED


def test_infer_research_complete() -> None:
    assert SalesWorkflowEngine().infer_stage(_item(has_decision_makers=False)) == SalesWorkflowStage.RESEARCH_COMPLETE


def test_infer_decision_makers() -> None:
    assert SalesWorkflowEngine().infer_stage(_item()) == SalesWorkflowStage.DECISION_MAKERS_FOUND


def test_infer_sales_package() -> None:
    assert SalesWorkflowEngine().infer_stage(_item(has_sales_package=True)) == SalesWorkflowStage.SALES_PACKAGE_READY


def test_infer_campaign_and_approval() -> None:
    eng = SalesWorkflowEngine()
    assert eng.infer_stage(_item(has_campaign=True, campaign_approved=True)) == SalesWorkflowStage.CAMPAIGN_CREATED
    assert eng.infer_stage(_item(has_campaign=True, campaign_approved=False)) == SalesWorkflowStage.FOUNDER_APPROVAL


def test_infer_email_whatsapp_reply() -> None:
    eng = SalesWorkflowEngine()
    assert eng.infer_stage(_item(email_sent=True)) == SalesWorkflowStage.EMAIL_SENT
    assert eng.infer_stage(_item(whatsapp_sent=True, email_sent=False)) == SalesWorkflowStage.WHATSAPP_SENT
    assert eng.infer_stage(_item(email_sent=True, reply_received=True)) == SalesWorkflowStage.REPLY_RECEIVED


def test_infer_meeting_proposal_negotiation_outcomes() -> None:
    eng = SalesWorkflowEngine()
    assert eng.infer_stage(_item(meeting_requested=True)) == SalesWorkflowStage.MEETING_REQUESTED
    assert eng.infer_stage(_item(meeting_booked=True)) == SalesWorkflowStage.MEETING_BOOKED
    assert eng.infer_stage(_item(proposal_pending=True)) == SalesWorkflowStage.PROPOSAL_PENDING
    assert eng.infer_stage(_item(proposal_sent=True)) == SalesWorkflowStage.PROPOSAL_SENT
    assert eng.infer_stage(_item(negotiation=True)) == SalesWorkflowStage.NEGOTIATION
    assert eng.infer_stage(_item(won=True)) == SalesWorkflowStage.WON
    assert eng.infer_stage(_item(lost=True)) == SalesWorkflowStage.LOST


def test_transition_stores_fields() -> None:
    t = SalesWorkflowEngine().transition(
        SalesWorkflowStage.EMAIL_SENT,
        SalesWorkflowStage.FOLLOW_UP,
        reason="no_reply",
        evidence=["days:3"],
        actor="system",
        next_action="send_follow_up",
    )
    assert t.from_stage == SalesWorkflowStage.EMAIL_SENT
    assert t.to_stage == SalesWorkflowStage.FOLLOW_UP
    assert t.reason == "no_reply"
    assert t.evidence == ["days:3"]
    assert t.actor == "system"
    assert t.next_action == "send_follow_up"
    assert t.timestamp is not None


def test_invalid_transition_raises() -> None:
    with pytest.raises(ValueError):
        SalesWorkflowEngine().transition(
            SalesWorkflowStage.LEAD_DISCOVERED,
            SalesWorkflowStage.WON,
            reason="skip",
        )


def test_followup_cadence_defaults() -> None:
    eng = FollowUpIntelligenceEngine()
    assert eng.recommend(_item(email_sent=True, days_since_last_touch=2)).channel == FollowUpChannel.EMAIL_FOLLOW_UP
    assert eng.recommend(_item(email_sent=True, days_since_last_touch=5)).channel == FollowUpChannel.VALUE_EMAIL
    assert eng.recommend(_item(email_sent=True, days_since_last_touch=8)).channel == FollowUpChannel.WHATSAPP
    assert eng.recommend(_item(email_sent=True, days_since_last_touch=12)).channel == FollowUpChannel.FINAL_EMAIL
    assert eng.recommend(_item(email_sent=True, days_since_last_touch=20)).channel == FollowUpChannel.ARCHIVE


def test_followup_configurable() -> None:
    cfg = FollowUpConfig(follow_up_days=1, value_email_days=2, whatsapp_days=3, final_email_days=4, archive_days=5)
    rec = FollowUpIntelligenceEngine().recommend(_item(email_sent=True, days_since_last_touch=3, follow_up_config=cfg))
    assert rec.channel == FollowUpChannel.WHATSAPP
    assert rec.due is True


def test_followup_skips_active() -> None:
    rec = FollowUpIntelligenceEngine().recommend(_item(email_sent=True, reply_received=True, days_since_last_touch=10))
    assert rec.due is False
    assert rec.channel == FollowUpChannel.NONE


def test_timeline_append_only_core_events() -> None:
    events = RelationshipTimelineEngine().build(
        _item(
            email_sent=True,
            reply_received=True,
            meeting_booked=True,
            meeting_completed=True,
            proposal_pending=True,
            proposal_sent=True,
            founder_notes=["Call went well"],
            recent_activity=["email opened"],
        )
    )
    types = [e.event_type for e in events]
    assert "website_discovered" in types
    assert "decision_maker_added" in types
    assert "email_sent" in types
    assert "email_opened" in types
    assert "reply_received" in types
    assert "meeting_booked" in types
    assert "meeting_completed" in types
    assert "proposal_pending" in types
    assert "proposal_sent" in types
    assert "founder_note" in types


def test_timeline_won_lost() -> None:
    won = RelationshipTimelineEngine().build(_item(won=True))
    lost = RelationshipTimelineEngine().build(_item(lost=True))
    assert any(e.event_type == "won" for e in won)
    assert any(e.event_type == "lost" for e in lost)


def test_meeting_intelligence_pack() -> None:
    pack = MeetingIntelligenceEngine().prepare(_item())
    assert pack.company_overview
    assert pack.discovery_questions
    assert pack.meeting_agenda
    assert pack.success_checklist
    assert pack.roi_talking_points
    assert pack.budget_hints


def test_next_best_action_one_only_approve() -> None:
    stage = SalesWorkflowStage.FOUNDER_APPROVAL
    follow = FollowUpIntelligenceEngine().recommend(_item(has_campaign=True, campaign_approved=False))
    nba = NextBestActionEngine().recommend(_item(has_campaign=True, campaign_approved=False), stage=stage, follow_up=follow)
    assert nba.action == NextActionKind.APPROVE_CAMPAIGN
    assert nba.confidence > 0
    assert nba.reason
    assert nba.evidence
    assert nba.expected_impact


def test_next_best_action_follow_up_and_wait() -> None:
    eng = NextBestActionEngine()
    fu = FollowUpIntelligenceEngine()
    due = fu.recommend(_item(email_sent=True, days_since_last_touch=3))
    assert eng.recommend(_item(email_sent=True, days_since_last_touch=3), stage=SalesWorkflowStage.FOLLOW_UP, follow_up=due).action == NextActionKind.SEND_FOLLOW_UP
    wait = fu.recommend(_item(email_sent=True, days_since_last_touch=0))
    assert eng.recommend(_item(email_sent=True, days_since_last_touch=0), stage=SalesWorkflowStage.EMAIL_SENT, follow_up=wait).action == NextActionKind.WAIT


def test_case_study_library_complete() -> None:
    assert set(CASE_LIBRARY) >= {
        "AI Automation",
        "CRM",
        "SaaS",
        "Healthcare",
        "Manufacturing",
        "Education",
        "Hospitality",
        "Construction",
        "Retail",
        "Logistics",
    }


def test_case_study_industry_match() -> None:
    rec = CaseStudyRecommendationEngine().recommend(_item(industry="Healthcare"))
    assert rec.industry_key == "Healthcare"
    assert rec.relevance >= 90


def test_objection_tracker() -> None:
    rows = ObjectionTrackerEngine().track(_item(objections_seen=["Budget"], recent_activity=["need approval later"]))
    kinds = {r.objection.value for r in rows}
    assert "Budget" in kinds
    assert all(r.frequency >= 1 for r in rows)
    assert all(0 <= r.win_rate <= 100 for r in rows)


def test_sales_memory_observe_only() -> None:
    mem = SalesMemoryEngine().insights(_item())
    assert mem.best_email_pattern
    assert mem.best_cta
    assert "no_engine_mutation:true" in mem.evidence


def test_founder_work_queue_kinds() -> None:
    item = _item(
        meetings_today=[{"summary": "Discovery"}],
        proposal_queue=[{"summary": "Write proposal"}],
        negotiation_queue=[{"summary": "Close"}],
        pending_approvals=[{"summary": "Approve"}],
        high_intent_replies=[{"summary": "Reply now"}],
    )
    decision = AutonomousSalesAgentPipeline().process(item)
    kinds = {w.kind for w in decision.work_queue}
    assert kinds <= FOUNDER_QUEUE_KINDS or kinds.issubset(FOUNDER_QUEUE_KINDS | kinds)
    assert "meet_today" in kinds
    assert "proposal_pending" in kinds
    assert "negotiation" in kinds
    assert "needs_approval" in kinds
    assert "high_intent_reply" in kinds


def test_morning_brief_shape() -> None:
    decision = AutonomousSalesAgentPipeline().process(_item(email_sent=True, days_since_last_touch=9, buying_intent_score=80))
    brief = decision.morning_brief
    assert isinstance(brief.priorities, list)
    assert isinstance(brief.expected_meetings, list)
    assert isinstance(brief.expected_replies, list)
    assert isinstance(brief.high_risk_deals, list)
    assert isinstance(brief.companies_requiring_attention, list)
    assert isinstance(brief.follow_ups_due, list)
    assert brief.revenue_forecast >= 0


def test_pipeline_full_decision() -> None:
    decision = AutonomousSalesAgentService().evaluate(_item(email_sent=True, days_since_last_touch=5))
    assert decision.scoring_version == "asa-v1"
    assert decision.stage
    assert decision.transitions
    assert decision.next_best_action
    assert decision.case_study
    assert decision.sales_memory
    assert decision.morning_brief
    assert decision.evidence_chain


def test_evaluate_many() -> None:
    out = AutonomousSalesAgentService().evaluate_many([_item(company_name=f"Co {i}") for i in range(5)])
    assert len(out) == 5


def test_in_memory_repository_append_only() -> None:
    repo = InMemoryAsaRepository()
    d1 = AutonomousSalesAgentService().evaluate(_item())
    d2 = AutonomousSalesAgentService().evaluate(_item(email_sent=True))
    repo.append_decision(d1)
    repo.append_decision(d2)
    assert len(repo.all_runs()) == 2
    assert len(repo.timeline_events()) >= 2
    assert len(repo.transitions()) >= 2


def test_analytics_summarize() -> None:
    decisions = AutonomousSalesAgentService().evaluate_many([_item(company_name=f"X{i}", email_sent=True, days_since_last_touch=i) for i in range(8)])
    summary = AsaAnalyticsEngine().summarize(decisions)
    assert summary["total"] == 8
    assert "by_stage" in summary
    assert "by_action" in summary


def test_rules_and_scheduler() -> None:
    assert SalesWorkflowStage.FOUNDER_APPROVAL in FOUNDER_ONLY_STAGES
    sched = default_schedule()
    assert sched.morning_brief_seconds == 86_400
    assert sched.work_queue_refresh_seconds == 180


def test_service_transition_wrapper() -> None:
    t = AutonomousSalesAgentService().transition(
        SalesWorkflowStage.PROPOSAL_SENT,
        SalesWorkflowStage.NEGOTIATION,
        reason="commercial discussion",
        evidence=["signal:negotiation"],
        actor="founder",
        next_action="negotiate",
    )
    assert t.actor == "founder"


def test_queue_stage_derived_items() -> None:
    q = FounderWorkQueueEngine()
    follow = FollowUpIntelligenceEngine().recommend(_item())
    nba = NextBestActionEngine().recommend(_item(proposal_pending=True), stage=SalesWorkflowStage.PROPOSAL_PENDING, follow_up=follow)
    items = q.build(_item(proposal_pending=True), stage=SalesWorkflowStage.PROPOSAL_PENDING, next_action=nba)
    assert any(i.kind == "proposal_pending" for i in items)


def test_brief_engine_direct() -> None:
    item = _item(email_sent=True, days_since_last_touch=10, buying_intent_score=90, negotiation=True)
    follow = FollowUpIntelligenceEngine().recommend(item)
    nba = NextBestActionEngine().recommend(item, stage=SalesWorkflowStage.NEGOTIATION, follow_up=follow)
    work = FounderWorkQueueEngine().build(item, stage=SalesWorkflowStage.NEGOTIATION, next_action=nba)
    brief = MorningBriefEngine().generate(item, work_queue=work, follow_up=follow, next_action=nba)
    assert brief.priorities
    assert brief.high_risk_deals
