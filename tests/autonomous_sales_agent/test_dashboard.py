from pathlib import Path


def test_founder_work_queue_page_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "apps" / "dashboard" / "app" / "(workspace)" / "founder-work-queue" / "page.tsx").exists()


def test_morning_brief_page_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "apps" / "dashboard" / "app" / "(workspace)" / "morning-brief" / "page.tsx").exists()


def test_sidebar_links_asa_surfaces() -> None:
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "dashboard" / "components" / "layout" / "sidebar.tsx").read_text(encoding="utf-8")
    assert "/founder-work-queue" in text
    assert "/morning-brief" in text


def test_beacon_client_has_asa_methods() -> None:
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "dashboard" / "lib" / "api" / "beacon.ts").read_text(encoding="utf-8")
    assert "asaWorkQueue" in text
    assert "asaMorningBrief" in text
    assert "asaTimeline" in text
