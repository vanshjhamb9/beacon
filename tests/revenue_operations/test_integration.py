"""Integration-style compose checks across ROC modules."""

from uuid import uuid4

from revenue_operations import RevenueOperationsService
from revenue_operations.models.types import OpportunitySignal, RevenueOperationsInput


def test_end_to_end_morning_answers() -> None:
    """Founder morning questions answered from one decision pack."""
    decision = RevenueOperationsService().evaluate(
        RevenueOperationsInput(
            opportunities=[
                OpportunitySignal(
                    company_id=uuid4(),
                    company_name="Hot Co",
                    probability=90,
                    pipeline_value=60000,
                    reply_waiting=True,
                    meeting_today=True,
                    proposal_pending=True,
                    radar_hints=["funding", "hiring AI engineers"],
                    decision_makers=["CEO"],
                    industry="SaaS",
                    service="AI Automation",
                ),
                OpportunitySignal(
                    company_id=uuid4(),
                    company_name="Risk Co",
                    probability=25,
                    pipeline_value=35000,
                    at_risk=True,
                    days_in_stage=14,
                ),
            ],
            campaigns_running=4,
            revenue_target_week=50000,
            founder_name="Founder",
        )
    )
    # What should I do?
    assert decision.founder_assistant.todays_mission
    assert decision.command_center.todays_mission
    # Who should I contact / who replied?
    assert decision.founder_assistant.replies or decision.command_center.replies
    # Which companies are hot?
    assert decision.founder_assistant.highest_probability_deals
    # Which opportunities are at risk?
    assert decision.control_tower.deals_at_risk >= 1
    # What revenue can I close this week?
    assert decision.forecast.this_week.amount >= 0
    assert decision.command_center.forecast.get("this_week") is not None
