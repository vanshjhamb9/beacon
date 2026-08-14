from __future__ import annotations

from datetime import UTC, datetime

from autonomous_sales_agent.actions.engine import NextBestActionEngine
from autonomous_sales_agent.brief.engine import MorningBriefEngine
from autonomous_sales_agent.casestudy.engine import CaseStudyRecommendationEngine
from autonomous_sales_agent.followup.engine import FollowUpIntelligenceEngine
from autonomous_sales_agent.meeting.engine import MeetingIntelligenceEngine
from autonomous_sales_agent.memory.engine import SalesMemoryEngine
from autonomous_sales_agent.models.types import (
    SCORING_VERSION,
    AutonomousSalesAgentDecision,
    AutonomousSalesAgentInput,
    SalesWorkflowStage,
)
from autonomous_sales_agent.objections.engine import ObjectionTrackerEngine
from autonomous_sales_agent.queue.engine import FounderWorkQueueEngine
from autonomous_sales_agent.timeline.engine import RelationshipTimelineEngine
from autonomous_sales_agent.workflow.engine import SalesWorkflowEngine


class AutonomousSalesAgentPipeline:
    """Compose-only BDM layer — deterministic, no GPT, no engine redesign."""

    def __init__(self) -> None:
        self.workflow = SalesWorkflowEngine()
        self.followup = FollowUpIntelligenceEngine()
        self.timeline = RelationshipTimelineEngine()
        self.meeting = MeetingIntelligenceEngine()
        self.actions = NextBestActionEngine()
        self.casestudy = CaseStudyRecommendationEngine()
        self.objections = ObjectionTrackerEngine()
        self.memory = SalesMemoryEngine()
        self.queue = FounderWorkQueueEngine()
        self.brief = MorningBriefEngine()

    def process(self, item: AutonomousSalesAgentInput) -> AutonomousSalesAgentDecision:
        stage = self.workflow.infer_stage(item)
        if item.days_since_last_touch >= item.follow_up_config.follow_up_days and item.email_sent and not item.reply_received:
            if stage in {
                SalesWorkflowStage.EMAIL_SENT,
                SalesWorkflowStage.WHATSAPP_SENT,
                SalesWorkflowStage.FOLLOW_UP,
            }:
                stage = SalesWorkflowStage.FOLLOW_UP

        transitions = self.workflow.build_transitions(item, stage)
        follow_up = self.followup.recommend(item)
        timeline = self.timeline.build(item)
        next_best = self.actions.recommend(item, stage=stage, follow_up=follow_up)
        meeting_pack = None
        if stage in {
            SalesWorkflowStage.MEETING_REQUESTED,
            SalesWorkflowStage.MEETING_BOOKED,
            SalesWorkflowStage.PROPOSAL_PENDING,
            SalesWorkflowStage.NEGOTIATION,
        } or item.meeting_booked:
            meeting_pack = self.meeting.prepare(item)
        case_study = self.casestudy.recommend(item)
        objections = self.objections.track(item)
        sales_memory = self.memory.insights(item)
        work_queue = self.queue.build(item, stage=stage, next_action=next_best)
        morning_brief = self.brief.generate(
            item,
            work_queue=work_queue,
            follow_up=follow_up,
            next_action=next_best,
        )
        evidence = [
            f"scoring_version:{SCORING_VERSION}",
            f"stage:{stage.value}",
            f"next:{next_best.action.value}",
            f"follow_up:{follow_up.channel.value}",
            f"timeline_events:{len(timeline)}",
            f"work_items:{len(work_queue)}",
        ]
        return AutonomousSalesAgentDecision(
            company_id=item.company_id,
            company_name=item.company_name,
            stage=stage,
            transitions=transitions,
            follow_up=follow_up,
            timeline=timeline,
            meeting_intelligence=meeting_pack,
            next_best_action=next_best,
            case_study=case_study,
            objections=objections,
            sales_memory=sales_memory,
            work_queue=work_queue,
            morning_brief=morning_brief,
            scoring_version=SCORING_VERSION,
            evidence_chain=evidence,
            evaluated_at=item.now or datetime.now(UTC),
        )
