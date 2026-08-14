from __future__ import annotations

from data_acquisition.models.types import AcquisitionSnapshotInput, ConnectorAlert, ConnectorAuditItem
from data_acquisition.alerting.engine import AlertEngine


class ConnectorAuditEngine:
    def __init__(self, *, alerter: AlertEngine | None = None) -> None:
        self.alerter = alerter or AlertEngine()

    def audit(self, snapshots: list[AcquisitionSnapshotInput]) -> tuple[list[ConnectorAuditItem], list[ConnectorAlert]]:
        items: list[ConnectorAuditItem] = []
        alerts: list[ConnectorAlert] = []
        for snapshot in snapshots:
            total_runs = max(1, snapshot.runs_24h)
            failure_rate = round((snapshot.failed_runs_24h / total_runs) * 100.0, 2)
            processed = snapshot.emitted_24h + snapshot.duplicates_24h
            duplicate_rate = round((snapshot.duplicates_24h / processed) * 100.0, 2) if processed else 0.0
            coverage = self._coverage(snapshot)
            item = ConnectorAuditItem(
                source=snapshot.source,
                enabled=snapshot.enabled,
                health_status=snapshot.health_status,
                consecutive_failures=snapshot.consecutive_failures,
                average_latency_ms=snapshot.average_latency_ms,
                last_success_at=snapshot.last_success_at,
                last_failure_at=snapshot.last_failure_at,
                last_error=snapshot.last_error,
                signals_collected_24h=snapshot.collected_24h,
                companies_discovered_24h=snapshot.companies_discovered_24h,
                opportunities_produced_24h=snapshot.opportunities_produced_24h,
                high_value_opportunities_24h=snapshot.high_value_opportunities_24h,
                duplicate_rate_24h=duplicate_rate,
                failure_rate_24h=failure_rate,
                coverage_score=coverage,
                extraction_quality_avg=round(snapshot.extraction_quality_avg, 2),
            )
            items.append(item)
            alerts.extend(self.alerter.evaluate(snapshot, item))
        items.sort(key=lambda row: (row.coverage_score, row.high_value_opportunities_24h), reverse=True)
        return items, alerts

    def _coverage(self, snapshot: AcquisitionSnapshotInput) -> float:
        if not snapshot.enabled:
            return 0.0
        signal_score = min(40.0, snapshot.emitted_24h * 2.0)
        company_score = min(25.0, snapshot.companies_discovered_24h * 5.0)
        opportunity_score = min(25.0, snapshot.opportunities_produced_24h * 5.0)
        quality_score = min(10.0, snapshot.extraction_quality_avg / 10.0)
        return round(signal_score + company_score + opportunity_score + quality_score, 2)
