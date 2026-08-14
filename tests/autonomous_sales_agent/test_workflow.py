from uuid import uuid4

from autonomous_sales_agent.models.types import AutonomousSalesAgentInput, NextActionKind, NextBestAction, SalesWorkflowStage
from autonomous_sales_agent.queue.engine import FounderWorkQueueEngine
from autonomous_sales_agent.workflow.engine import ALLOWED, SalesWorkflowEngine


def test_workflow_allowed_map_covers_happy_path() -> None:
    path = [
        SalesWorkflowStage.LEAD_DISCOVERED,
        SalesWorkflowStage.QUALIFIED,
        SalesWorkflowStage.RESEARCH_COMPLETE,
        SalesWorkflowStage.DECISION_MAKERS_FOUND,
        SalesWorkflowStage.SALES_PACKAGE_READY,
        SalesWorkflowStage.CAMPAIGN_CREATED,
        SalesWorkflowStage.FOUNDER_APPROVAL,
        SalesWorkflowStage.EMAIL_SENT,
        SalesWorkflowStage.REPLY_RECEIVED,
        SalesWorkflowStage.MEETING_REQUESTED,
        SalesWorkflowStage.MEETING_BOOKED,
        SalesWorkflowStage.PROPOSAL_PENDING,
        SalesWorkflowStage.PROPOSAL_SENT,
        SalesWorkflowStage.NEGOTIATION,
        SalesWorkflowStage.WON,
    ]
    for cur, nxt in zip(path, path[1:], strict=False):
        assert nxt in ALLOWED[cur] or cur == nxt


def test_workflow_build_transitions_has_actor_and_next() -> None:
    item = AutonomousSalesAgentInput(company_id=uuid4(), company_name="W", email_sent=True)
    stage = SalesWorkflowEngine().infer_stage(item)
    transitions = SalesWorkflowEngine().build_transitions(item, stage)
    assert len(transitions) == 1
    assert transitions[0].actor == "system"
    assert transitions[0].next_action
    assert transitions[0].reason


def test_urgent_follow_up_appears_in_queue() -> None:
    nba = NextBestAction(
        action=NextActionKind.SEND_FOLLOW_UP,
        confidence=90,
        reason="No reply after 2 days",
        evidence=["days:2"],
        expected_impact="Recover",
    )
    items = FounderWorkQueueEngine().build(
        AutonomousSalesAgentInput(company_id=uuid4(), company_name="Urgent Co", email_sent=True, days_since_last_touch=2),
        stage=SalesWorkflowStage.FOLLOW_UP,
        next_action=nba,
    )
    assert any(i.kind == "urgent_follow_up" for i in items)
