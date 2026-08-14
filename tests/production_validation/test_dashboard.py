from pathlib import Path
from uuid import uuid4

from production_validation import ProductionValidationPipeline
from production_validation.models.types import ProductionValidationInput


def test_dashboard_pages_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "apps" / "dashboard" / "app" / "(workspace)" / "production-health" / "page.tsx").exists()
    assert (root / "apps" / "dashboard" / "app" / "(workspace)" / "revenue-dashboard" / "page.tsx").exists()
    sidebar = (root / "apps" / "dashboard" / "components" / "layout" / "sidebar.tsx").read_text(encoding="utf-8")
    assert "/production-health" in sidebar
    assert "/revenue-dashboard" in sidebar


def test_founder_board_answers_core_questions() -> None:
    decision = ProductionValidationPipeline().process(
        ProductionValidationInput(
            company_id=uuid4(),
            company_name="Board Co",
            website="b.com",
            business_email="a@b.com",
            decision_makers=[{"name": "A"}],
            industry="SaaS",
            pain_points=["x"],
            buying_triggers=["y"],
            technologies=["z"],
            linkedin_url="https://linkedin.com/b",
            revenue_estimate="$10k",
            service_match="MVP",
            confidence=80,
            freshness_days=2,
            verification_score=80,
            founder_queues={
                "contact_now": [{"company_name": "Contact Me"}],
                "replied": [{"company_name": "Replied"}],
                "booked": [{"company_name": "Booked"}],
                "needs_proposal": [{"company_name": "Proposal"}],
                "needs_follow_up": [{"company_name": "Follow"}],
                "revenue_stuck": [{"company_name": "Stuck"}],
            },
            security_flags={k: True for k in (
                "oauth_tokens", "secrets", "encryption", "webhook_signatures", "rbac",
                "audit_logs", "rate_limits", "csrf", "jwt", "api_keys",
            )},
        )
    )
    board = decision.founder_board
    assert board.contact_now and board.replied and board.booked
    assert board.needs_proposal and board.needs_follow_up and board.revenue_stuck
    assert board.do_now
