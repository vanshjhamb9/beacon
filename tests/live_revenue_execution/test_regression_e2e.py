from uuid import uuid4

from communication_gateway.email.health import email_health_score
from communication_gateway.models.types import Attachment, ChannelType, OutboundMessage, ProviderName
from communication_gateway.safety.controls import SafetyControls
from live_revenue_execution import LiveRevenueExecutionPipeline
from live_revenue_execution.models.types import LREInput


def test_e2e_founder_workflow_pack() -> None:
    """Discover→approve→send→reply→meeting→proposal composition path."""
    decision = LiveRevenueExecutionPipeline().process(
        LREInput(
            company_id=uuid4(),
            company_name="First Client Co",
            campaign_id=uuid4(),
            priority_grade="A+",
            probability=85,
            buying_intent_score=92,
            decision_makers=[{"name": "Founder", "title": "CEO", "email": "ceo@first.example"}],
            pain_points=["manual support", "poor conversion"],
            email_subject="Support automation for First Client",
            email_body="Saw your team hiring support — we cut ticket volume with AI.",
            to_email="ceo@first.example",
            to_whatsapp="+15551239999",
            calendly_url="https://calendly.com/inowix/discovery",
            recommended_service="AI Customer Support",
            expected_budget="$35k–$60k",
            reply_history=[{"body": "Interested — let's book a meeting"}],
            funnel_counts={"emails": 1, "opened": 1, "replies": 1, "meeting_booked": 1},
            case_studies=["DTC support deflection"],
        )
    )
    assert decision.approval_card is not None
    assert decision.email_plan is not None
    assert decision.meeting_pack is not None
    assert decision.proposal is not None
    assert decision.learning_hints is not None
    assert decision.scoring_version == "lre-v1"


def test_gmail_raw_supports_attachments_and_unsubscribe_headers() -> None:
    from communication_gateway.email.gmail import GmailProvider

    # Don't call network — only build MIME
    provider = object.__new__(GmailProvider)
    raw = GmailProvider._build_raw(
        provider,
        OutboundMessage(
            channel=ChannelType.EMAIL,
            provider=ProviderName.GMAIL,
            to_address="a@example.com",
            from_address="founder@inowix.example",
            subject="Test",
            body_text="Hello",
            body_html="<p>Hello</p>",
            attachments=[Attachment(filename="brochure.pdf", content_type="application/pdf", content_base64="cGRm")],
            metadata={"tracking_id": "abc123", "unsubscribe_url": "https://beacon.local/unsubscribe/abc123"},
            campaign_id=uuid4(),
        ),
    )
    assert isinstance(raw, str) and len(raw) > 20


def test_hourly_quota_blocks_send() -> None:
    safety = SafetyControls(daily_email_quota=500, hourly_email_quota=2)
    assert safety.check_send(idempotency_key="a", campaign_stopped=False, sent_this_hour=2).allowed is False


def test_email_health_score_deterministic() -> None:
    a = email_health_score(bounce_rate=0.01, open_rate=0.3, dkim_ok=True, spf_ok=True)
    b = email_health_score(bounce_rate=0.01, open_rate=0.3, dkim_ok=True, spf_ok=True)
    assert a == b
    assert a["score"] >= 70


def test_no_gpt_dependency_in_lre_package() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "packages" / "live_revenue_execution"
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "openai" not in text
        assert "gpt-4" not in text
