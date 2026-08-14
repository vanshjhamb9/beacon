"""Top-level E2E composition of the Beacon revenue workflow (deterministic, no live providers)."""

from uuid import uuid4

from live_revenue_execution import LiveRevenueExecutionPipeline
from live_revenue_execution.models.types import LREInput
from production_validation import ProductionValidationPipeline
from production_validation.models.types import ProductionValidationInput
from sales_intelligence import SalesIntelligencePipeline
from sales_intelligence.models.types import SalesIntelligenceInput


def test_discovery_to_proposal_composed_workflow() -> None:
    company_id = uuid4()
    campaign_id = uuid4()

    si = SalesIntelligencePipeline().process(
        SalesIntelligenceInput(
            company_id=company_id,
            company_name="Prospect One",
            industry="SaaS",
            pains=["manual workflows"],
            signals=["funding"],
            opportunity_score=88,
            probability=75,
            priority_grade="A+",
            recommended_service="AI Automation",
            decision_makers=[{"name": "Alex", "title": "COO"}],
            replies=[{"body": "Interested — let's meet"}],
        )
    )
    assert si.buying_intent.buying_intent_score >= 0
    assert si.offer.primary_offer

    lre = LiveRevenueExecutionPipeline().process(
        LREInput(
            company_id=company_id,
            company_name="Prospect One",
            campaign_id=campaign_id,
            priority_grade="A+",
            probability=75,
            buying_intent_score=si.buying_intent.buying_intent_score,
            email_subject="Automation idea",
            email_body="Saw your hiring signal.",
            to_email="alex@prospect.example",
            to_whatsapp="+15550001111",
            pain_points=["manual workflows"],
            recommended_service="AI Automation",
            calendly_url="https://calendly.com/inowix/discovery",
            reply_history=[{"body": "Interested — let's meet"}],
            funnel_counts={"emails": 1, "opened": 1, "replies": 1, "meeting_booked": 1},
        )
    )
    assert lre.approval_card is not None
    assert lre.meeting_pack is not None
    assert lre.proposal is not None

    prv = ProductionValidationPipeline().process(
        ProductionValidationInput(
            company_id=company_id,
            company_name="Prospect One",
            website="prospect.example",
            business_email="alex@prospect.example",
            decision_makers=[{"name": "Alex", "email": "alex@prospect.example"}],
            linkedin_url="https://linkedin.com/in/alex",
            technologies=["Python"],
            industry="SaaS",
            buying_triggers=["funding"],
            pain_points=["manual workflows"],
            revenue_estimate="$35k",
            service_match="AI Automation",
            confidence=88,
            freshness_days=3,
            verification_score=90,
            oauth_ok=True,
            workers_online=True,
            campaigns=[{
                "campaign_id": str(campaign_id),
                "company_id": str(company_id),
                "company_name": "Prospect One",
                "emails_sent": 1,
                "delivered": 1,
                "opened": 1,
                "clicked": 0,
                "replies": 1,
                "meetings": 1,
                "proposals": 1,
                "won": 0,
                "revenue": 0,
                "stage": "proposal",
            }],
            security_flags={k: True for k in (
                "oauth_tokens", "secrets", "encryption", "webhook_signatures", "rbac",
                "audit_logs", "rate_limits", "csrf", "jwt", "api_keys",
            )},
        )
    )
    assert prv.lead_readiness and prv.lead_readiness.outreach_allowed
    assert prv.campaign_funnels[0].proposals == 1
    assert prv.readiness_report.overall_score >= 90
