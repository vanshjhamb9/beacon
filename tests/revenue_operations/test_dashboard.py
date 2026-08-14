from pathlib import Path


def test_home_uses_roc_command_center() -> None:
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "dashboard" / "features" / "home" / "home-workspace.tsx").read_text(encoding="utf-8")
    assert "revenue-operations-dashboard" in text
    assert "Revenue Operations Center" in text
    assert "High Priority Queue" in text
    assert "Revenue Score" in text
    assert "rocDashboard" in text or "beaconApi.rocDashboard" in text


def test_beacon_client_roc_methods() -> None:
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "dashboard" / "lib" / "api" / "beacon.ts").read_text(encoding="utf-8")
    for method in ["rocDashboard", "rocRefresh", "rocForecast", "rocAlerts", "rocMemory", "rocReplay", "rocLearning", "rocMetrics"]:
        assert method in text
