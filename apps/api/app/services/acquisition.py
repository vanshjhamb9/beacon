from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from app.core.config import Settings, get_settings
from app.repositories.acquisition import AcquisitionRepository
from data_acquisition import AcquisitionAnalyticsPipeline
from data_acquisition.alerting.engine import AlertEngine
from data_acquisition.models.types import AcquisitionDashboard, DailyAcquisitionReport


class AcquisitionService:
    def __init__(
        self,
        repository: AcquisitionRepository,
        pipeline: AcquisitionAnalyticsPipeline | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.repository = repository
        self.settings = settings or get_settings()
        self.pipeline = pipeline or AcquisitionAnalyticsPipeline(
            alerter=AlertEngine(failure_threshold=self.settings.acquisition_alert_failure_threshold)
        )

    async def record_collector_run(
        self,
        *,
        source: str,
        collected: int,
        emitted: int,
        duplicates: int,
        rate_limited: bool,
        success: bool,
        latency_ms: float,
        error: str | None = None,
        trace_id: str | None = None,
    ) -> UUID:
        return await self.repository.record_run(
            source=source,
            collected=collected,
            emitted=emitted,
            duplicates=duplicates,
            rate_limited=rate_limited,
            success=success,
            latency_ms=latency_ms,
            error=error,
            trace_id=trace_id,
        )

    async def dashboard(self) -> AcquisitionDashboard:
        snapshots = await self.repository.build_snapshots()
        latest = await self.repository.latest_daily_report()
        latest_report = None
        if latest is not None:
            latest_report = DailyAcquisitionReport.model_validate(latest.payload)
        return self.pipeline.build_dashboard(snapshots, latest_report=latest_report)

    async def audit(self) -> dict[str, Any]:
        dashboard = await self.dashboard()
        return {
            "connectors": [item.model_dump(mode="json") for item in dashboard.connectors],
            "open_alerts": dashboard.open_alerts,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def benchmarks(self) -> dict[str, Any]:
        dashboard = await self.dashboard()
        return {
            "leaderboard": [item.model_dump(mode="json") for item in dashboard.leaderboard],
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def alerts(self) -> dict[str, Any]:
        open_alerts = await self.repository.open_alerts()
        return {
            "alerts": [
                {
                    "id": str(row.id),
                    "source": row.source,
                    "severity": row.severity,
                    "code": row.code,
                    "message": row.message,
                    "consecutive_failures": row.consecutive_failures,
                    "details": row.details,
                    "created_at": row.created_at.isoformat(),
                }
                for row in open_alerts
            ]
        }

    async def monitor_and_alert(self) -> dict[str, int]:
        snapshots = await self.repository.build_snapshots()
        _audits, alerts = self.pipeline.audit_engine.audit(snapshots)
        stored = await self.repository.store_alerts(alerts)
        healthy = [item.source for item in snapshots if item.health_status == "healthy" and item.consecutive_failures == 0]
        resolved = await self.repository.resolve_alerts_for_healthy_sources(healthy)
        return {"alerts_created": stored, "alerts_resolved": resolved, "open_evaluated": len(alerts)}

    async def generate_daily_report(self, *, report_day: date | None = None) -> DailyAcquisitionReport:
        day = report_day or datetime.now(UTC).date()
        since = datetime.combine(day, datetime.min.time(), tzinfo=UTC)
        until = since + timedelta(days=1)
        # For "today so far" use rolling 24h if generating mid-day for current date.
        if day == datetime.now(UTC).date():
            since = datetime.now(UTC) - timedelta(hours=24)
            until = datetime.now(UTC)

        snapshots = await self.repository.build_snapshots(since=since)
        counts = await self.repository.platform_counts(since=since)
        missing = await self.repository.missing_data_trends()
        report = self.pipeline.build_daily_report(
            snapshots,
            report_date=day,
            new_companies=int(counts["new_companies"]),
            new_opportunities=int(counts["new_opportunities"]),
            high_value_opportunities=int(counts["high_value_opportunities"]),
            signals_collected=int(counts["signals_collected"]),
            signals_persisted=int(counts["signals_persisted"]),
            duplicate_rate=float(counts["duplicate_rate"]),
            previous_companies=int(counts["previous_companies"]),
            missing_data_trends=missing,
        )
        await self.repository.store_daily_report(report)
        await self.repository.store_alerts(report.alerts)
        return report

    async def latest_report(self) -> dict[str, Any] | None:
        row = await self.repository.latest_daily_report()
        if row is None:
            return None
        return dict(row.payload)
