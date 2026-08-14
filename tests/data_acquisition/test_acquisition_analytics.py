from datetime import UTC, datetime

from data_acquisition import AcquisitionAnalyticsPipeline
from data_acquisition.models.types import AcquisitionSnapshotInput, AlertSeverity


def make_snapshot(**overrides: object) -> AcquisitionSnapshotInput:
    payload: dict[str, object] = {
        "source": "reddit",
        "enabled": True,
        "health_status": "healthy",
        "consecutive_failures": 0,
        "average_latency_ms": 120.0,
        "last_success_at": datetime.now(UTC),
        "runs_24h": 10,
        "successful_runs_24h": 9,
        "failed_runs_24h": 1,
        "collected_24h": 100,
        "emitted_24h": 80,
        "duplicates_24h": 20,
        "companies_discovered_24h": 12,
        "opportunities_produced_24h": 6,
        "high_value_opportunities_24h": 3,
        "extraction_quality_avg": 78.0,
    }
    payload.update(overrides)
    return AcquisitionSnapshotInput(**payload)  # type: ignore[arg-type]


def test_dashboard_and_benchmarks_rank_high_yield_sources() -> None:
    pipeline = AcquisitionAnalyticsPipeline()
    dashboard = pipeline.build_dashboard(
        [
            make_snapshot(source="reddit", high_value_opportunities_24h=5),
            make_snapshot(
                source="rss",
                high_value_opportunities_24h=1,
                companies_discovered_24h=2,
                opportunities_produced_24h=1,
            ),
        ]
    )
    assert dashboard.active_connectors == 2
    assert dashboard.leaderboard[0].source == "reddit"
    assert dashboard.high_value_opportunities_24h == 6


def test_alerts_for_down_connector() -> None:
    pipeline = AcquisitionAnalyticsPipeline()
    _audits, alerts = pipeline.audit_engine.audit(
        [
            make_snapshot(
                source="sec_edgar",
                health_status="down",
                consecutive_failures=4,
                failed_runs_24h=4,
                successful_runs_24h=0,
                runs_24h=4,
            )
        ]
    )
    assert any(alert.severity == AlertSeverity.CRITICAL for alert in alerts)
