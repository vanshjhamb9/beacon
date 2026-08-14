from __future__ import annotations

from sales_intelligence.reply.engine import ReplyIntelligenceEngine

from live_revenue_execution.analytics.engine import RevenueAnalyticsEngine
from live_revenue_execution.approval.engine import ApprovalCenterEngine
from live_revenue_execution.email.engine import ProductionEmailEngine
from live_revenue_execution.learning.engine import OutcomeLearningComposer
from live_revenue_execution.lifecycle.engine import CampaignLifecycleEngine
from live_revenue_execution.meeting.engine import MeetingAutomationEngine
from live_revenue_execution.models.types import LREDecision, LREInput, LREStage, SCORING_VERSION
from live_revenue_execution.proposal.engine import ProposalCenterEngine
from live_revenue_execution.whatsapp.engine import WhatsAppExecutionEngine


class LiveRevenueExecutionPipeline:
    """Compose existing Beacon engines into a production revenue execution pack."""

    def __init__(self) -> None:
        self.email = ProductionEmailEngine()
        self.whatsapp = WhatsAppExecutionEngine()
        self.approval = ApprovalCenterEngine()
        self.lifecycle = CampaignLifecycleEngine()
        self.meeting = MeetingAutomationEngine()
        self.proposal = ProposalCenterEngine()
        self.analytics = RevenueAnalyticsEngine()
        self.learning = OutcomeLearningComposer()
        self.reply = ReplyIntelligenceEngine()  # reuse Sales Intelligence — no redesign

    def process(self, item: LREInput) -> LREDecision:
        stage = self.lifecycle.infer_stage(item)
        email_plan = self.email.build(item) if (item.email_body or item.to_email or item.email_subject) else None
        whatsapp_plan = self.whatsapp.build(item)
        approval_card = None
        if item.campaign_id is not None:
            approval_card = self.approval.build_card(item, email_plan=email_plan, whatsapp_plan=whatsapp_plan)
            if stage.value in {"strategy_ready", "outreach_ready", "ranked_a_plus"}:
                stage = LREStage.AWAITING_APPROVAL

        meeting_pack = None
        if stage in {LREStage.MEETING_BOOKED, LREStage.MEETING_PACK_READY, LREStage.REPLIED} or item.funnel_counts.get("meeting_booked"):
            meeting_pack = self.meeting.build(item)
            if stage == LREStage.MEETING_BOOKED:
                stage = LREStage.MEETING_PACK_READY

        proposal = None
        if stage in {LREStage.PROPOSAL_READY, LREStage.PROPOSAL_SENT, LREStage.MEETING_PACK_READY} or item.funnel_counts.get("proposals"):
            proposal = self.proposal.build(item)

        analytics = self.analytics.snapshot(item)
        learning = self.learning.hints(item, analytics)

        events = [
            self.lifecycle.event(stage=stage, detail="LRE pack evaluated"),
        ]
        if email_plan:
            events.append(self.lifecycle.event(stage=stage, detail=f"email_plan:{email_plan.tracking_id}"))
        if whatsapp_plan:
            events.append(self.lifecycle.event(stage=stage, detail="whatsapp_plan:ready"))

        # Classify latest reply via existing SI engine
        if item.reply_history:
            latest = item.reply_history[-1]
            classified = self.reply.classify(str(latest.get("body") or ""), subject=str(latest.get("subject") or ""))
            events.append(
                self.lifecycle.event(
                    stage=LREStage.REPLIED if stage != LREStage.WON else stage,
                    detail=f"reply_class:{classified.classification.value}:{classified.confidence}",
                )
            )

        evidence = [
            f"scoring_version:{SCORING_VERSION}",
            f"stage:{stage.value}",
            f"probability:{item.probability}",
            f"grade:{item.priority_grade or 'n/a'}",
            *(item.evidence[:8]),
        ]
        return LREDecision(
            company_id=item.company_id,
            company_name=item.company_name,
            campaign_id=item.campaign_id,
            stage=stage,
            approval_card=approval_card,
            email_plan=email_plan,
            whatsapp_plan=whatsapp_plan,
            meeting_pack=meeting_pack,
            proposal=proposal,
            analytics=analytics,
            learning_hints=learning,
            lifecycle_events=events,
            scoring_version=SCORING_VERSION,
            evidence_chain=evidence,
        )
