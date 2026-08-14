"""Integration: Sales Intelligence composes inputs that mirror sibling engines."""

from uuid import uuid4

from sales_intelligence import SalesIntelligenceService
from sales_intelligence.models.types import SalesIntelligenceInput


def test_integration_with_revenue_hunter_shaped_fields() -> None:
    decision = SalesIntelligenceService().evaluate(
        SalesIntelligenceInput(
            company_id=uuid4(),
            company_name="RH Compose Co",
            industry="Healthcare",
            country="United States",
            employee_count=150,
            funding_stage="series_a",
            funding_days_ago=20,
            revenue_band="mid",
            recommended_service="AI Automation",
            expected_budget="$45k–$90k",
            opportunity_score=88,
            priority_grade="A+",
            probability=74,
            pains=["manual workflows", "compliance"],
            signals=["funding", "hiring"],
            website_opportunities=["slow LCP", "broken forms"],
            decision_makers=[{"name": "Dr. Kim", "title": "CTO"}],
        )
    )
    assert decision.offer.primary_offer
    assert decision.meeting_coach.decision_makers
    assert decision.buying_intent.buying_stage


def test_integration_with_communication_replies() -> None:
    decision = SalesIntelligenceService().evaluate(
        SalesIntelligenceInput(
            company_id=uuid4(),
            company_name="Reply Co",
            opportunity_score=60,
            probability=40,
            emails=[
                {"subject": "Intro", "body": "Would love to help", "sent_at": "2026-07-01T10:00:00+00:00"},
            ],
            replies=[
                {
                    "id": "msg-1",
                    "subject": "Re: Intro",
                    "body": "Budget is tight but interested — send proposal",
                    "received_at": "2026-07-02T10:00:00+00:00",
                }
            ],
        )
    )
    assert decision.reply_intelligence
    assert any(
        r.classification.value in {"Interested", "Need Proposal", "Budget Concern"}
        for r in decision.reply_intelligence
    )
    assert any(e.event_type.value == "reply" for e in decision.memory.events)


def test_integration_worker_task_module_importable() -> None:
    from worker.sales_intelligence_tasks import refresh_from_replies, refresh_company

    assert refresh_from_replies.name == "sales_intelligence.refresh_from_replies"
    assert refresh_company.name == "sales_intelligence.refresh_company"


def test_integration_celery_schedule_includes_si() -> None:
    from worker.celery_app import celery_app

    assert "worker.sales_intelligence_tasks" in (celery_app.conf.include or [])
    schedule = celery_app.conf.beat_schedule or {}
    assert "refresh-sales-intelligence-from-replies" in schedule
    assert schedule["refresh-sales-intelligence-from-replies"]["task"] == "sales_intelligence.refresh_from_replies"
