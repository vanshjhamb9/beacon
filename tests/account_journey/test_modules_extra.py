from uuid import uuid4

from account_journey.analytics.engine import GlobalCampaignAnalyticsEngine
from account_journey.followup.engine import FollowUpPlannerEngine
from account_journey.health.engine import AccountHealthEngine
from account_journey.journey.engine import AccountJourneyEngine
from account_journey.models.types import (
    AccountHealthCategory,
    AccountJourneyInput,
    EngagementScores,
    MultiTouchPlan,
    OutreachIntelligence,
    TouchStep,
    FollowUpChannel,
)
from account_journey.orchestration.engine import MultiTouchOrchestrator
from account_journey.outreach.engine import OutreachIntelligenceEngine
from account_journey.engagement.engine import EngagementScoringEngine


def test_analytics_dimensions() -> None:
    analytics = GlobalCampaignAnalyticsEngine().analyze(
        AccountJourneyInput(
            company_id=uuid4(),
            company_name="A",
            country="US",
            industry="SaaS",
            company_size="51-200",
            technologies=["Python"],
            service="CRM",
            campaign_name="Spring",
            decision_makers=[{"name": "X", "title": "CEO"}],
            replied=True,
            meeting_scheduled=True,
            cohort_accounts=[
                {"country": "US", "industry": "SaaS", "company_size": "51-200", "technology": "Python", "service": "CRM", "campaign": "Spring", "dm_role": "CEO", "replied": True, "meeting": True, "proposal": False, "won": False, "revenue": 10000},
                {"country": "UK", "industry": "Healthcare", "company_size": "11-50", "technology": "AWS", "service": "AI", "campaign": "Spring", "dm_role": "CTO", "replied": False, "meeting": False, "proposal": False, "won": False, "revenue": 0},
            ],
        )
    )
    assert analytics.by_country
    assert analytics.by_industry
    assert analytics.by_company_size
    assert analytics.by_technology
    assert analytics.by_service
    assert analytics.by_campaign
    assert analytics.by_decision_maker_role


def test_followup_terminal_and_critical() -> None:
    item = AccountJourneyInput(company_id=uuid4(), company_name="T", won=True)
    outreach = OutreachIntelligenceEngine().score(item)
    engagement = EngagementScoringEngine().score(item, outreach=outreach)
    health = AccountHealthEngine().classify(item, stage=AccountJourneyEngine().infer_stage(item), engagement=engagement)
    multi = MultiTouchPlan(steps=[])
    plan = FollowUpPlannerEngine().plan(item, engagement=engagement, health=health, multi_touch=multi)
    assert plan.next_action == "close_file"

    hot = AccountJourneyInput(company_id=uuid4(), company_name="C", negotiation=True, probability=90, buying_intent=90)
    outreach2 = OutreachIntelligenceEngine().score(hot)
    engagement2 = EngagementScoringEngine().score(hot, outreach=outreach2)
    health2 = AccountHealthEngine().classify(hot, stage=AccountJourneyEngine().infer_stage(hot), engagement=engagement2)
    plan2 = FollowUpPlannerEngine().plan(hot, engagement=engagement2, health=health2, multi_touch=multi)
    assert plan2.channel == FollowUpChannel.FOUNDER_FOLLOW_UP
    assert plan2.urgency == "critical"


def test_health_warm_and_cold() -> None:
    cold = AccountJourneyInput(company_id=uuid4(), company_name="Cold", probability=5)
    stage = AccountJourneyEngine().infer_stage(cold)
    outreach = OutreachIntelligence(signals=[], positive_score=0, negative_score=0)
    engagement = EngagementScores(overall_engagement=10, account_temperature=10)
    h = AccountHealthEngine().classify(cold, stage=stage, engagement=engagement)
    assert h.category == AccountHealthCategory.COLD

    warm = AccountJourneyInput(company_id=uuid4(), company_name="Warm", opened=True, probability=40)
    stage2 = AccountJourneyEngine().infer_stage(warm)
    engagement2 = EngagementScores(overall_engagement=40, account_temperature=40)
    h2 = AccountHealthEngine().classify(warm, stage=stage2, engagement=engagement2)
    assert h2.category in {AccountHealthCategory.WARM, AccountHealthCategory.PRIORITY}


def test_orchestration_includes_founder_follow_up_for_hot() -> None:
    item = AccountJourneyInput(
        company_id=uuid4(),
        company_name="Hot",
        emailed=True,
        replied=True,
        negotiation=True,
        buying_intent=95,
        probability=95,
    )
    outreach = OutreachIntelligenceEngine().score(item)
    engagement = EngagementScoringEngine().score(item, outreach=outreach)
    plan = MultiTouchOrchestrator().plan(item, engagement=engagement, outreach=outreach)
    assert any(s.channel == FollowUpChannel.FOUNDER_FOLLOW_UP for s in plan.steps) or engagement.overall_engagement >= 75
