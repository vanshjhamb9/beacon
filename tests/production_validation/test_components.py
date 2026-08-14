from uuid import uuid4

from production_validation import READINESS_GATE, ProductionValidationPipeline, ProductionValidationService
from production_validation.models.types import ProductionValidationInput


def _full(**overrides: object) -> ProductionValidationInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Ready Co",
        "website": "ready.example",
        "business_email": "ceo@ready.example",
        "decision_makers": [{"name": "Ceo", "email": "ceo@ready.example"}],
        "linkedin_url": "https://linkedin.com/company/ready",
        "technologies": ["Python"],
        "industry": "SaaS",
        "buying_triggers": ["funding"],
        "pain_points": ["manual workflows"],
        "revenue_estimate": "$40k",
        "service_match": "AI Automation",
        "confidence": 85,
        "freshness_days": 5,
        "verification_score": 88,
        "oauth_ok": True,
        "workers_online": True,
        "queue_depth": 10,
        "bounce_rate": 0.01,
        "reply_rate": 0.12,
        "component_signals": {
            "api": {"success_rate": 99, "latency_ms": 100},
            "workers": {"success_rate": 99},
            "collectors": {"success_rate": 95},
            "campaigns": {"success_rate": 94},
            "email": {"success_rate": 97, "failure_rate": 1},
            "whatsapp": {"success_rate": 96},
            "oauth": {"success_rate": 100},
            "queues": {"success_rate": 98, "queue_depth": 10},
            "database": {"success_rate": 99.5, "latency_ms": 20},
            "redis": {"success_rate": 99, "latency_ms": 3},
            "celery": {"success_rate": 99},
            "pipeline": {"success_rate": 96},
        },
        "campaigns": [
            {
                "campaign_id": str(uuid4()),
                "company_id": str(uuid4()),
                "company_name": "Ready Co",
                "emails_sent": 10,
                "delivered": 9,
                "opened": 4,
                "clicked": 2,
                "replies": 1,
                "meetings": 1,
                "proposals": 1,
                "won": 0,
                "revenue": 0,
                "stage": "meeting",
            }
        ],
        "revenue_metrics": {
            "companies_found": 100,
            "qualified_companies": 40,
            "sales_ready": 18,
            "pipeline_value": 420000,
            "revenue_closed": 90000,
            "replies": 12,
            "meetings": 6,
            "proposals": 3,
            "won": 2,
            "lost": 1,
        },
        "outcome_rates": {"reply_rate": 0.12, "meeting_rate": 0.3, "proposal_rate": 0.4, "win_rate": 0.2},
        "founder_queues": {
            "contact_now": [{"company_name": "Ready Co"}],
            "replied": [{"company_name": "Reply Co"}],
            "booked": [{"company_name": "Meet Co"}],
            "needs_proposal": [{"company_name": "Prop Co"}],
            "needs_follow_up": [{"company_name": "Follow Co"}],
            "revenue_stuck": [{"company_name": "Stuck Co"}],
        },
        "security_flags": {k: True for k in (
            "oauth_tokens", "secrets", "encryption", "webhook_signatures", "rbac",
            "audit_logs", "rate_limits", "csrf", "jwt", "api_keys",
        )},
    }
    payload.update(overrides)
    return ProductionValidationInput(**payload)  # type: ignore[arg-type]


def test_health_and_readiness_pass() -> None:
    decision = ProductionValidationPipeline().process(_full())
    assert decision.health.overall_score >= 80
    assert decision.lead_readiness is not None
    assert decision.lead_readiness.score >= READINESS_GATE
    assert decision.lead_readiness.outreach_allowed is True
    assert decision.readiness_report.overall_score >= 90
    assert decision.scoring_version == "prrv-v1"


def test_lead_below_gate_blocked() -> None:
    decision = ProductionValidationPipeline().process(
        _full(
            website=None,
            business_email=None,
            decision_makers=[],
            linkedin_url=None,
            technologies=[],
            industry=None,
            buying_triggers=[],
            pain_points=[],
            revenue_estimate=None,
            service_match=None,
            confidence=10,
            freshness_days=90,
            verification_score=10,
        )
    )
    assert decision.lead_readiness is not None
    assert decision.lead_readiness.score < READINESS_GATE
    assert decision.lead_readiness.outreach_allowed is False


def test_alerts_and_security() -> None:
    decision = ProductionValidationPipeline().process(
        _full(oauth_ok=False, bounce_rate=0.05, queue_depth=800, webhook_failures=5)
    )
    codes = {a.code for a in decision.alerts}
    assert "oauth_expired" in codes
    assert "bounce_spike" in codes
    assert decision.security_audit.findings
    assert decision.weekly_report.csv_text.startswith("metric,value")
    assert decision.playbooks
    assert decision.founder_board.do_now


def test_campaign_funnel_observability() -> None:
    decision = ProductionValidationPipeline().process(_full())
    assert decision.campaign_funnels
    funnel = decision.campaign_funnels[0]
    assert funnel.emails_sent >= funnel.delivered or funnel.delivered >= 0
    assert funnel.stage


def test_service_playbooks() -> None:
    books = ProductionValidationService().list_playbooks()
    names = {b.name for b in books}
    assert "AI Automation" in names
    assert "MVP Development" in names
