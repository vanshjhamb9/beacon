from pathlib import Path


def test_account_journey_page_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "apps" / "dashboard" / "app" / "(workspace)" / "account-journey" / "page.tsx").exists()


def test_sidebar_and_workspace_tabs() -> None:
    root = Path(__file__).resolve().parents[2]
    sidebar = (root / "apps" / "dashboard" / "components" / "layout" / "sidebar.tsx").read_text(encoding="utf-8")
    workspace = (root / "apps" / "dashboard" / "features" / "goi" / "account-journey-workspace.tsx").read_text(encoding="utf-8")
    assert "/account-journey" in sidebar
    for label in [
        "Account Journey",
        "Company Health",
        "Buying Committee",
        "Engagement",
        "Reply Intelligence",
        "Timeline",
        "Follow-up Planner",
        "Global Analytics",
    ]:
        assert label in workspace


def test_beacon_goi_methods() -> None:
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "dashboard" / "lib" / "api" / "beacon.ts").read_text(encoding="utf-8")
    for method in ["goiCompany", "goiDashboard", "goiFollowups", "goiAnalytics", "goiReplies", "goiHealth", "goiRefresh"]:
        assert method in text
