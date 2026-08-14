from __future__ import annotations

from data_acquisition.models.types import (
    AcquisitionSnapshotInput,
    AlertSeverity,
    ConnectorAlert,
    ConnectorAuditItem,
)


class AlertEngine:
    def __init__(self, *, failure_threshold: int = 3) -> None:
        self.failure_threshold = failure_threshold

    def evaluate(
        self,
        snapshot: AcquisitionSnapshotInput,
        audit: ConnectorAuditItem,
    ) -> list[ConnectorAlert]:
        alerts: list[ConnectorAlert] = []
        if not snapshot.enabled:
            return alerts

        if snapshot.health_status == "down" or snapshot.consecutive_failures >= self.failure_threshold:
            alerts.append(
                ConnectorAlert(
                    source=snapshot.source,
                    severity=AlertSeverity.CRITICAL,
                    code="connector_down",
                    message=f"{snapshot.source} is down after {snapshot.consecutive_failures} consecutive failures.",
                    consecutive_failures=snapshot.consecutive_failures,
                    details={"last_error": snapshot.last_error},
                )
            )
        elif snapshot.health_status == "degraded" or snapshot.consecutive_failures > 0:
            alerts.append(
                ConnectorAlert(
                    source=snapshot.source,
                    severity=AlertSeverity.WARNING,
                    code="connector_degraded",
                    message=f"{snapshot.source} is degraded ({snapshot.consecutive_failures} consecutive failures).",
                    consecutive_failures=snapshot.consecutive_failures,
                    details={"last_error": snapshot.last_error},
                )
            )

        if audit.failure_rate_24h >= 40.0:
            alerts.append(
                ConnectorAlert(
                    source=snapshot.source,
                    severity=AlertSeverity.WARNING,
                    code="high_failure_rate",
                    message=f"{snapshot.source} failure rate is {audit.failure_rate_24h:.1f}% over 24h.",
                    consecutive_failures=snapshot.consecutive_failures,
                    details={"failure_rate_24h": audit.failure_rate_24h},
                )
            )

        if audit.duplicate_rate_24h >= 80.0 and audit.signals_collected_24h >= 10:
            alerts.append(
                ConnectorAlert(
                    source=snapshot.source,
                    severity=AlertSeverity.INFO,
                    code="high_duplicate_rate",
                    message=f"{snapshot.source} duplicate rate is {audit.duplicate_rate_24h:.1f}%.",
                    consecutive_failures=snapshot.consecutive_failures,
                    details={"duplicate_rate_24h": audit.duplicate_rate_24h},
                )
            )

        if snapshot.enabled and snapshot.emitted_24h == 0 and snapshot.runs_24h > 0:
            alerts.append(
                ConnectorAlert(
                    source=snapshot.source,
                    severity=AlertSeverity.WARNING,
                    code="zero_emit_yield",
                    message=f"{snapshot.source} ran but emitted zero new signals in 24h.",
                    consecutive_failures=snapshot.consecutive_failures,
                )
            )
        return alerts
