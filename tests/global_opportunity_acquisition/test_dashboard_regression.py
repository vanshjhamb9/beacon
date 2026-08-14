from pathlib import Path

import pytest

from global_opportunity_acquisition.community_intelligence.engine import NEED_PATTERNS, CommunityIntelligenceEngine
from global_opportunity_acquisition.models.types import OpportunityIntent


@pytest.mark.parametrize("label,patterns", NEED_PATTERNS)
def test_each_community_need(label: str, patterns: tuple[str, ...]) -> None:
    c = CommunityIntelligenceEngine().detect([patterns[0]])
    assert label in c.needs


def test_all_opportunity_intents_enum() -> None:
    expected = {
        "hiring",
        "funding",
        "expansion",
        "ai_adoption",
        "digital_transformation",
        "website_rebuild",
        "crm_migration",
        "erp_migration",
        "cloud_migration",
        "automation",
        "customer_support_scaling",
        "marketing_scaling",
        "startup_launch",
        "acquisition",
        "ipo",
        "product_launch",
        "technology_migration",
        "infrastructure_upgrades",
        "international_expansion",
        "compliance_changes",
        "security_investment",
        "platform_modernization",
    }
    assert {i.value for i in OpportunityIntent} == expected


def test_dashboard_page_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    page = root / "apps" / "dashboard" / "app" / "(workspace)" / "opportunity-acquisition" / "page.tsx"
    feature = root / "apps" / "dashboard" / "features" / "goap" / "global-opportunity-workspace.tsx"
    assert page.exists()
    text = feature.read_text(encoding="utf-8")
    for label in [
        "Overview",
        "Connectors",
        "Hiring Intelligence",
        "Funding Intelligence",
        "Technology Intelligence",
        "Website Intelligence",
        "Community Intelligence",
        "Review Intelligence",
        "Opportunity Graph",
        "Benchmarks",
        "Freshness",
        "Analytics",
    ]:
        assert label in text


def test_sidebar_and_workers_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    sidebar = (root / "apps" / "dashboard" / "components" / "layout" / "sidebar.tsx").read_text(encoding="utf-8")
    celery = (root / "apps" / "worker" / "worker" / "celery_app.py").read_text(encoding="utf-8")
    tasks = (root / "apps" / "worker" / "worker" / "global_opportunity_acquisition_tasks.py").read_text(encoding="utf-8")
    assert "/opportunity-acquisition" in sidebar
    assert "Global Opportunity" in sidebar
    assert "worker.global_opportunity_acquisition_tasks" in celery
    for name in [
        "collector.refresh_sources",
        "collector.score_sources",
        "collector.build_graph",
        "collector.update_benchmarks",
        "collector.detect_new_intent",
        "collector.refresh_websites",
        "collector.refresh_jobs",
        "collector.refresh_reviews",
        "collector.refresh_funding",
        "collector.daily_report",
    ]:
        assert name in celery
        assert name in tasks


def test_no_gpt_and_no_scrape_stack() -> None:
    root = Path(__file__).resolve().parents[2] / "packages" / "global_opportunity_acquisition"
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "import openai" not in text
        assert "from openai" not in text
        assert "chatgpt" not in text
        assert "beautifulsoup" not in text
        assert "playwright" not in text
        assert "selenium" not in text


def test_docs_exist() -> None:
    root = Path(__file__).resolve().parents[2] / "docs"
    for name in [
        "global-opportunity-acquisition.md",
        "source-connectors.md",
        "opportunity-graph.md",
        "website-intelligence.md",
        "hiring-intelligence.md",
        "review-intelligence.md",
        "technology-intelligence.md",
        "sprint-25-engineering-report.md",
    ]:
        assert (root / name).exists()


def test_ci_includes_goap() -> None:
    ci = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "tests/global_opportunity_acquisition" in ci
    assert "packages/global_opportunity_acquisition" in ci
