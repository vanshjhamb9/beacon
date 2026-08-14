from pathlib import Path


def test_dashboard_page_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    page = root / "apps" / "dashboard" / "app" / "(workspace)" / "revenue-optimization" / "page.tsx"
    workspace = root / "apps" / "dashboard" / "features" / "roip" / "revenue-optimization-workspace.tsx"
    assert page.exists()
    assert workspace.exists()
    text = workspace.read_text(encoding="utf-8")
    for tab in [
        "Overview",
        "Email Analytics",
        "WhatsApp Analytics",
        "Industry Analytics",
        "Founder Analytics",
        "Offer Performance",
        "Reply Intelligence",
        "Subject Intelligence",
        "CTA Intelligence",
        "Benchmarks",
        "Learning",
        "Recommendations",
    ]:
        assert tab in text


def test_sidebar_link() -> None:
    root = Path(__file__).resolve().parents[2]
    sidebar = (root / "apps" / "dashboard" / "components" / "layout" / "sidebar.tsx").read_text(encoding="utf-8")
    assert "/revenue-optimization" in sidebar
    assert "Revenue Optimization" in sidebar


def test_beacon_client_methods() -> None:
    root = Path(__file__).resolve().parents[2]
    beacon = (root / "apps" / "dashboard" / "lib" / "api" / "beacon.ts").read_text(encoding="utf-8")
    for method in [
        "roipDashboard",
        "roipFounder",
        "roipIndustry",
        "roipOffers",
        "roipRecommendations",
        "roipBenchmarks",
        "roipLearning",
        "roipReplies",
        "roipSearch",
        "roipRefresh",
    ]:
        assert method in beacon
