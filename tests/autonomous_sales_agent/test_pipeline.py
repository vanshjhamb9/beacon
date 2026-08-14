from uuid import uuid4

from autonomous_sales_agent import AutonomousSalesAgentPipeline
from autonomous_sales_agent.models.types import AutonomousSalesAgentInput, FollowUpChannel, NextActionKind, SalesWorkflowStage


def _item(**overrides: object) -> AutonomousSalesAgentInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Pipeline Co",
        "industry": "SaaS",
        "priority_grade": "A+",
        "probability": 80,
        "buying_intent_score": 75,
        "has_decision_makers": True,
        "decision_makers": [{"name": "Pat"}],
        "pains": ["manual ops"],
        "recommended_service": "Custom SaaS",
    }
    payload.update(overrides)
    return AutonomousSalesAgentInput.model_validate(payload)


def test_pipeline_follow_up_stage_when_silent() -> None:
    d = AutonomousSalesAgentPipeline().process(_item(email_sent=True, days_since_last_touch=4))
    assert d.stage == SalesWorkflowStage.FOLLOW_UP
    assert d.follow_up.due is True
    assert d.next_best_action.action == NextActionKind.SEND_FOLLOW_UP


def test_pipeline_meeting_pack_when_booked() -> None:
    d = AutonomousSalesAgentPipeline().process(_item(meeting_booked=True))
    assert d.meeting_intelligence is not None
    assert d.next_best_action.action == NextActionKind.ATTEND_MEETING


def test_pipeline_value_email_maps_case_study_action() -> None:
    d = AutonomousSalesAgentPipeline().process(_item(email_sent=True, days_since_last_touch=6))
    assert d.follow_up.channel == FollowUpChannel.VALUE_EMAIL
    assert d.next_best_action.action == NextActionKind.SEND_CASE_STUDY


def test_pipeline_archive_maps_close() -> None:
    d = AutonomousSalesAgentPipeline().process(_item(email_sent=True, days_since_last_touch=25))
    assert d.follow_up.channel == FollowUpChannel.ARCHIVE
    assert d.next_best_action.action == NextActionKind.CLOSE_FILE


def test_pipeline_evidence_chain() -> None:
    d = AutonomousSalesAgentPipeline().process(_item())
    assert any(e.startswith("scoring_version:") for e in d.evidence_chain)
    assert any(e.startswith("stage:") for e in d.evidence_chain)


def test_pipeline_deterministic() -> None:
    item = _item(company_id=uuid4(), email_sent=True, days_since_last_touch=2)
    a = AutonomousSalesAgentPipeline().process(item)
    b = AutonomousSalesAgentPipeline().process(item)
    assert a.stage == b.stage
    assert a.next_best_action.action == b.next_best_action.action
    assert a.follow_up.channel == b.follow_up.channel
    assert a.case_study.industry_key == b.case_study.industry_key
