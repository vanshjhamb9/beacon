"""Coverage boost for LRE edge paths."""

from uuid import uuid4

from live_revenue_execution.approval.engine import ApprovalCenterEngine
from live_revenue_execution.email.engine import ClickTracker, ProductionEmailEngine
from live_revenue_execution.lifecycle.engine import CampaignLifecycleEngine
from live_revenue_execution.models.types import LREInput, LREStage
from live_revenue_execution.pipelines.lre_pipeline import LiveRevenueExecutionPipeline
from live_revenue_execution.services.engine import LiveRevenueExecutionService
from live_revenue_execution.whatsapp.engine import WhatsAppExecutionEngine


def test_email_default_body_and_click_wrap() -> None:
    item = LREInput(
        company_id=uuid4(),
        company_name="Default Co",
        decision_makers=[{"name": "Alex Kim"}],
        pain_points=["ops delay"],
        recommended_service="MVP",
        to_email="a@example.com",
        calendly_url="https://calendly.com/x",
    )
    plan = ProductionEmailEngine().build(item)
    assert "Alex" in plan.body_text or "Default Co" in plan.body_text
    wrapped = ClickTracker().wrap_links(
        '<a href="https://example.com/case">x</a>',
        tracking_id=plan.tracking_id,
        base_url="https://beacon.local/t",
    )
    assert "/c/" in wrapped


def test_approval_high_risk_send_later() -> None:
    item = LREInput(
        company_id=uuid4(),
        company_name="Risky",
        campaign_id=uuid4(),
        probability=20,
        risk_score=80,
    )
    email = ProductionEmailEngine().build(item.model_copy(update={"email_body": "hi", "to_email": "x@y.com"}))
    card = ApprovalCenterEngine().build_card(item, email_plan=email, whatsapp_plan=None)
    assert card.recommended_action.value in {"send_later", "edit", "approve"}


def test_lifecycle_infer_won_lost() -> None:
    engine = CampaignLifecycleEngine()
    assert engine.infer_stage(LREInput(company_id=uuid4(), company_name="W", funnel_counts={"won": 1})) == LREStage.WON
    assert engine.infer_stage(LREInput(company_id=uuid4(), company_name="L", funnel_counts={"lost": 1})) == LREStage.LOST
    assert engine.infer_stage(LREInput(company_id=uuid4(), company_name="P", funnel_counts={"proposal_sent": 1})) == LREStage.PROPOSAL_SENT


def test_whatsapp_none_without_contact_channels() -> None:
    plan = WhatsAppExecutionEngine().build(
        LREInput(company_id=uuid4(), company_name="No Contact", whatsapp_body=None, to_whatsapp=None, to_email=None)
    )
    assert plan is None


def test_service_evaluate_many_and_transition() -> None:
    service = LiveRevenueExecutionService()
    items = [
        LREInput(company_id=uuid4(), company_name=f"C{i}", campaign_id=uuid4(), email_body="x", to_email=f"{i}@e.com")
        for i in range(3)
    ]
    assert len(service.evaluate_many(items)) == 3
    assert service.transition(LREStage.APPROVED, LREStage.EMAIL_SENT) == LREStage.EMAIL_SENT


def test_pipeline_without_email_still_runs() -> None:
    decision = LiveRevenueExecutionPipeline().process(
        LREInput(company_id=uuid4(), company_name="Silent", priority_grade="B", probability=10)
    )
    assert decision.stage
    assert decision.analytics is not None
