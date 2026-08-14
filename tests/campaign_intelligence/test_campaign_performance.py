import time
from uuid import uuid4

from campaign_intelligence import CampaignPlanner
from tests.campaign_intelligence.test_campaign_planner import make_input


def test_campaign_planner_latency_budget() -> None:
    planner = CampaignPlanner()
    started = time.perf_counter()
    for _ in range(30):
        planner.plan(make_input(company_id=uuid4(), opportunity_id=uuid4()))
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert elapsed_ms < 2000.0
