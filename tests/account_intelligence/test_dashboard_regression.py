from pathlib import Path

import pytest

from account_intelligence import AccountIntelligencePipeline
from account_intelligence.models.types import AccountIntelligenceInput, ObservedContact, LICENSED_PROVIDERS_DISABLED


@pytest.mark.parametrize(
    "kwargs,min_score",
    [
        ({}, 0),
        (
            {
                "buying_intent": 90,
                "funding": "Series C",
                "latest_funding_round": "series_c",
                "employee_count": 400,
                "hiring_trend": 80,
                "expansion_score": 80,
                "html_hints": ["react", "https", "viewport", "hubspot", "stripe", "careers"],
                "observed_contacts": [
                    ObservedContact(
                        full_name="A",
                        role="CEO",
                        business_email="a@x.com",
                        linkedin_url="https://linkedin.com/in/a",
                        source="s",
                        evidence=[],
                    )
                ],
                "domain": "x.com",
            },
            40,
        ),
    ],
)
def test_readiness_smoke(kwargs: dict, min_score: float) -> None:
    d = AccountIntelligencePipeline().process(AccountIntelligenceInput(company_name="S", **kwargs))
    assert d.sales_readiness.score >= min_score


def test_dashboard_and_wiring() -> None:
    root = Path(__file__).resolve().parents[2]
    feature = (root / "apps" / "dashboard" / "features" / "aip" / "account-intelligence-workspace.tsx").read_text(encoding="utf-8")
    sidebar = (root / "apps" / "dashboard" / "components" / "layout" / "sidebar.tsx").read_text(encoding="utf-8")
    celery = (root / "apps" / "worker" / "worker" / "celery_app.py").read_text(encoding="utf-8")
    tasks = (root / "apps" / "worker" / "worker" / "account_intelligence_tasks.py").read_text(encoding="utf-8")
    ci = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for label in [
        "Overview",
        "Company",
        "Buying Committee",
        "Verified Contacts",
        "Technology",
        "Website",
        "Business Profile",
        "AI Readiness",
        "Sales Readiness",
        "Relationship Graph",
        "Verification",
        "Confidence",
        "Timeline",
    ]:
        assert label in feature
    assert "/account-intelligence" in sidebar
    assert "worker.account_intelligence_tasks" in celery
    for name in [
        "account.refresh_profiles",
        "account.refresh_contacts",
        "account.refresh_technology",
        "account.refresh_websites",
        "account.refresh_ai_scores",
        "account.refresh_sales_scores",
        "account.refresh_relationship_graph",
        "account.daily_validation",
    ]:
        assert name in celery
        assert name in tasks
    assert "tests/account_intelligence" in ci


def test_docs_exist() -> None:
    root = Path(__file__).resolve().parents[2] / "docs"
    for name in [
        "account-intelligence.md",
        "contact-validation.md",
        "buying-committee.md",
        "relationship-graph.md",
        "ai-readiness.md",
        "sales-readiness.md",
        "confidence-engine.md",
        "sprint-26-engineering-report.md",
    ]:
        assert (root / name).exists()


def test_licensed_providers_disabled() -> None:
    assert set(LICENSED_PROVIDERS_DISABLED) >= {"apollo", "people_data_labs", "zoominfo", "clearbit", "crunchbase"}


def test_no_gpt_imports() -> None:
    root = Path(__file__).resolve().parents[2] / "packages" / "account_intelligence"
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "import openai" not in text
        assert "from openai" not in text
