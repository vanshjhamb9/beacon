"""Dashboard contract: company Sales Intelligence tabs consume decision pack shape."""

from pathlib import Path
from uuid import uuid4

from sales_intelligence import SalesIntelligencePipeline
from sales_intelligence.models.types import SalesIntelligenceInput


def test_dashboard_pack_has_required_tabs() -> None:
    decision = SalesIntelligencePipeline().process(
        SalesIntelligenceInput(
            company_id=uuid4(),
            company_name="Dashboard Co",
            industry="Fintech",
            pains=["security", "compliance", "manual workflows"],
            signals=["funding"],
            opportunity_score=70,
            probability=55,
            replies=[{"body": "Need proposal and security review"}],
            recommended_service="Custom SaaS",
        )
    )
    pack = decision.model_dump(mode="json")
    for key in (
        "buying_intent",
        "psychology",
        "objections",
        "offer",
        "proposal",
        "meeting_coach",
        "memory",
        "reply_intelligence",
        "score",
        "trust",
    ):
        assert key in pack
    assert "buying_intent_score" in pack["buying_intent"]
    assert "primary_offer" in pack["offer"]
    assert "deal_probability" in pack["score"]
    assert "relationship_timeline" in pack["memory"]


def test_dashboard_panel_file_exists_with_tabs() -> None:
    root = Path(__file__).resolve().parents[2]
    panel = root / "apps" / "dashboard" / "features" / "companies" / "sales-intelligence-panel.tsx"
    text = panel.read_text(encoding="utf-8")
    for tab in (
        "Buying Intent",
        "Psychology",
        "Objections",
        "Offer",
        "Proposal",
        "Meeting",
        "Relationship",
        "Reply Intelligence",
        "Score",
    ):
        assert tab in text
    assert "SalesIntelligencePanel" in text


def test_company_workspace_embeds_sales_intelligence() -> None:
    root = Path(__file__).resolve().parents[2]
    workspace = root / "apps" / "dashboard" / "features" / "companies" / "company-workspace.tsx"
    text = workspace.read_text(encoding="utf-8")
    assert "SalesIntelligencePanel" in text
    assert "sales-intelligence-panel" in text
