from uuid import uuid4

from live_revenue_execution.approval.engine import ApprovalCenterEngine
from live_revenue_execution.analytics.engine import RevenueAnalyticsEngine
from live_revenue_execution.email.engine import ProductionEmailEngine
from live_revenue_execution.learning.engine import OutcomeLearningComposer
from live_revenue_execution.lifecycle.engine import CampaignLifecycleEngine
from live_revenue_execution.meeting.engine import MeetingAutomationEngine
from live_revenue_execution.models.types import LREInput, LREStage
from live_revenue_execution.proposal.engine import ProposalCenterEngine
from live_revenue_execution.whatsapp.engine import WhatsAppExecutionEngine


def _item(**overrides: object) -> LREInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Apex Robotics",
        "campaign_id": uuid4(),
        "industry": "SaaS",
        "priority_grade": "A+",
        "probability": 78,
        "risk_score": 20,
        "decision_makers": [{"name": "Priya Shah", "title": "COO", "email": "priya@apex.example"}],
        "pain_points": ["manual workflows", "high support cost"],
        "evidence": ["funding:14d", "hiring:ops"],
        "email_subject": "Idea for Apex ops",
        "email_body": "Noticed manual workflows slowing your team.",
        "to_email": "priya@apex.example",
        "to_whatsapp": "+15551234567",
        "calendly_url": "https://calendly.com/inowix/discovery",
        "recommended_service": "AI Automation",
        "expected_budget": "$25k–$45k",
        "buying_intent_score": 88,
        "attachments": [{"filename": "case-study.pdf", "content_type": "application/pdf", "url": "https://cdn.example/cs.pdf"}],
        "funnel_counts": {"emails": 3, "opened": 2, "replies": 1, "meetings": 0},
    }
    payload.update(overrides)
    return LREInput(**payload)  # type: ignore[arg-type]


def test_production_email_has_html_tracking_unsubscribe() -> None:
    plan = ProductionEmailEngine().build(_item())
    assert plan.tracking_id
    assert "Unsubscribe" in plan.body_html or "unsubscribe" in plan.body_html.lower()
    assert plan.open_pixel_url
    assert plan.calendly_url
    assert plan.evidence


def test_whatsapp_requires_founder_approval() -> None:
    plan = WhatsAppExecutionEngine().build(_item())
    assert plan is not None
    assert plan.requires_founder_approval is True
    assert plan.buttons


def test_approval_card_surfaces_previews() -> None:
    item = _item()
    email = ProductionEmailEngine().build(item)
    wa = WhatsAppExecutionEngine().build(item)
    card = ApprovalCenterEngine().build_card(item, email_plan=email, whatsapp_plan=wa)
    assert card.email_preview is not None
    assert card.whatsapp_preview is not None
    assert card.pain_points
    assert 0 <= card.risk_score <= 100


def test_lifecycle_transitions_valid() -> None:
    engine = CampaignLifecycleEngine()
    assert engine.can_transition(LREStage.AWAITING_APPROVAL, LREStage.APPROVED)
    assert engine.transition(LREStage.APPROVED, LREStage.EMAIL_SENT) == LREStage.EMAIL_SENT
    try:
        engine.transition(LREStage.WON, LREStage.EMAIL_SENT)
        raise AssertionError("should fail")
    except ValueError:
        pass


def test_meeting_and_proposal_packs() -> None:
    item = _item(funnel_counts={"meeting_booked": 1, "replies": 1})
    meeting = MeetingAutomationEngine().build(item)
    proposal = ProposalCenterEngine().build(item)
    assert meeting.recommended_questions
    assert meeting.follow_up_tasks
    assert proposal.pdf_base64
    assert proposal.tracking_id
    assert proposal.version == "v1"


def test_analytics_and_learning_require_approval() -> None:
    item = _item(funnel_counts={"emails": 20, "delivered": 20, "opened": 2, "replies": 0, "lost": 1})
    analytics = RevenueAnalyticsEngine().snapshot(item)
    hints = OutcomeLearningComposer().hints(item, analytics)
    assert analytics.emails == 20
    assert hints
    assert all(h.requires_human_approval for h in hints)
