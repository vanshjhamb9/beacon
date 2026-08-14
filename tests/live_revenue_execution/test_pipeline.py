from uuid import uuid4

from live_revenue_execution import SCORING_VERSION, LiveRevenueExecutionPipeline, LiveRevenueExecutionService
from live_revenue_execution.models.types import LREInput, LREStage


def _item(**overrides: object) -> LREInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Orbit Health",
        "campaign_id": uuid4(),
        "priority_grade": "A",
        "probability": 70,
        "decision_makers": [{"name": "Lee", "title": "CTO", "email": "lee@orbit.example"}],
        "pain_points": ["compliance", "manual intake"],
        "email_subject": "Orbit idea",
        "email_body": "Quick note on intake automation.",
        "to_email": "lee@orbit.example",
        "to_whatsapp": "+15550001111",
        "recommended_service": "Custom SaaS",
        "buying_intent_score": 75,
        "calendly_url": "https://calendly.com/inowix/discovery",
        "reply_history": [{"body": "Interested — can we meet next week?", "subject": "Re"}],
        "funnel_counts": {"emails": 1, "replies": 1},
    }
    payload.update(overrides)
    return LREInput(**payload)  # type: ignore[arg-type]


def test_pipeline_produces_execution_pack() -> None:
    decision = LiveRevenueExecutionPipeline().process(_item())
    assert decision.scoring_version == SCORING_VERSION
    assert decision.approval_card is not None
    assert decision.email_plan is not None
    assert decision.whatsapp_plan is not None
    assert decision.analytics is not None
    assert decision.lifecycle_events
    assert decision.evidence_chain
    assert decision.stage in {LREStage.AWAITING_APPROVAL, LREStage.REPLIED, LREStage.MEETING_PACK_READY}


def test_pipeline_deterministic() -> None:
    cid = uuid4()
    camp = uuid4()
    a = LiveRevenueExecutionPipeline().process(_item(company_id=cid, campaign_id=camp, company_name="Same"))
    b = LiveRevenueExecutionPipeline().process(_item(company_id=cid, campaign_id=camp, company_name="Same"))
    assert a.email_plan and b.email_plan
    assert a.email_plan.tracking_id == b.email_plan.tracking_id
    assert a.stage == b.stage


def test_service_classify_reply_reuses_si() -> None:
    result = LiveRevenueExecutionService().classify_reply("Please send a proposal with pricing")
    assert "Proposal" in result.classification.value or "Interested" in result.classification.value
    assert result.confidence >= 50


def test_meeting_stage_builds_pack_and_proposal() -> None:
    decision = LiveRevenueExecutionPipeline().process(
        _item(funnel_counts={"meeting_booked": 1, "replies": 1, "emails": 2})
    )
    assert decision.meeting_pack is not None
    assert decision.proposal is not None or decision.stage.value.startswith("meeting")
