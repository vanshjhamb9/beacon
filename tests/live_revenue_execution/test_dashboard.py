from pathlib import Path
from uuid import uuid4

from live_revenue_execution import LiveRevenueExecutionPipeline
from live_revenue_execution.models.types import LREInput


def test_dashboard_pack_shape() -> None:
    decision = LiveRevenueExecutionPipeline().process(
        LREInput(
            company_id=uuid4(),
            company_name="UI Co",
            campaign_id=uuid4(),
            email_subject="Hi",
            email_body="Body",
            to_email="a@example.com",
            pain_points=["cost"],
            probability=60,
        )
    )
    pack = decision.model_dump(mode="json")
    assert "approval_card" in pack
    assert "email_plan" in pack
    assert "analytics" in pack
    assert pack["approval_card"]["company_name"] == "UI Co"


def test_approval_and_proposal_pages_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "apps" / "dashboard" / "app" / "(workspace)" / "approval-center" / "page.tsx").exists()
    assert (root / "apps" / "dashboard" / "app" / "(workspace)" / "proposals" / "page.tsx").exists()
    sidebar = (root / "apps" / "dashboard" / "components" / "layout" / "sidebar.tsx").read_text(encoding="utf-8")
    assert "/approval-center" in sidebar
    assert "/proposals" in sidebar
