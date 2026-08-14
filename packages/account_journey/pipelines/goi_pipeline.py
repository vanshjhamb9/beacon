from __future__ import annotations

from datetime import UTC, datetime

from account_journey.analytics.engine import GlobalCampaignAnalyticsEngine
from account_journey.committee.engine import BuyingCommitteeEngine
from account_journey.engagement.engine import EngagementScoringEngine
from account_journey.followup.engine import FollowUpPlannerEngine
from account_journey.health.engine import AccountHealthEngine
from account_journey.journey.engine import AccountJourneyEngine
from account_journey.models.types import SCORING_VERSION, AccountJourneyDecision, AccountJourneyInput
from account_journey.orchestration.engine import MultiTouchOrchestrator
from account_journey.outreach.engine import OutreachIntelligenceEngine
from account_journey.replies.engine import ReplyIntelligenceV2Engine
from account_journey.timeline.engine import AccountTimelineEngine


class AccountJourneyPipeline:
    """Compose-only Global Outreach Intelligence — deterministic, no redesign."""

    def __init__(self) -> None:
        self.journey = AccountJourneyEngine()
        self.outreach = OutreachIntelligenceEngine()
        self.engagement = EngagementScoringEngine()
        self.orchestration = MultiTouchOrchestrator()
        self.health = AccountHealthEngine()
        self.committee = BuyingCommitteeEngine()
        self.followup = FollowUpPlannerEngine()
        self.analytics = GlobalCampaignAnalyticsEngine()
        self.replies = ReplyIntelligenceV2Engine()
        self.timeline = AccountTimelineEngine()

    def process(self, item: AccountJourneyInput) -> AccountJourneyDecision:
        stage = self.journey.infer_stage(item)
        transitions = self.journey.build_transitions(item, stage)
        outreach = self.outreach.score(item)
        engagement = self.engagement.score(item, outreach=outreach)
        multi_touch = self.orchestration.plan(item, engagement=engagement, outreach=outreach)
        health = self.health.classify(item, stage=stage, engagement=engagement)
        committee = self.committee.build(item)
        follow_up = self.followup.plan(item, engagement=engagement, health=health, multi_touch=multi_touch)
        analytics = self.analytics.analyze(item)
        reply = self.replies.classify(item)
        timeline = self.timeline.build(item)
        evidence = [
            f"scoring_version:{SCORING_VERSION}",
            f"stage:{stage.value}",
            f"health:{health.category.value}",
            f"engagement:{engagement.overall_engagement}",
            f"follow_up:{follow_up.channel.value}",
            f"founder_approval:{follow_up.requires_founder_approval}",
            "compose_only:true",
            "no_gpt:true",
        ]
        return AccountJourneyDecision(
            company_id=item.company_id,
            company_name=item.company_name,
            stage=stage,
            transitions=transitions,
            outreach=outreach,
            multi_touch=multi_touch,
            engagement=engagement,
            health=health,
            buying_committee=committee,
            follow_up=follow_up,
            analytics=analytics,
            reply=reply,
            timeline=timeline,
            scoring_version=SCORING_VERSION,
            evidence_chain=evidence,
            evaluated_at=item.now or datetime.now(UTC),
        )
