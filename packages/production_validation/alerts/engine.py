from __future__ import annotations

from production_validation.models.types import (
    AlertSeverity,
    EngineHealthReport,
    HealthStatus,
    LeadReadinessResult,
    ProductionAlert,
    ProductionValidationInput,
)


class AlertEngine:
    def detect(
        self,
        item: ProductionValidationInput,
        *,
        health: EngineHealthReport,
        lead: LeadReadinessResult | None,
    ) -> list[ProductionAlert]:
        alerts: list[ProductionAlert] = []
        if item.reply_rate < 0.05 and int((item.funnel or {}).get("emails") or 0) >= 20:
            alerts.append(
                ProductionAlert(
                    code="low_reply_rate",
                    title="Low reply rate",
                    severity=AlertSeverity.HIGH,
                    recommendation="Tighten ICP, refresh subject lines, and pause weak segments.",
                    evidence=[f"reply_rate:{item.reply_rate}"],
                )
            )
        if item.bounce_rate >= 0.03:
            alerts.append(
                ProductionAlert(
                    code="bounce_spike",
                    title="Bounce spike",
                    severity=AlertSeverity.CRITICAL,
                    recommendation="Stop sends, verify emails, and re-run verification.",
                    owner="ops",
                    evidence=[f"bounce_rate:{item.bounce_rate}"],
                )
            )
        if lead and not lead.checklist.decision_maker:
            alerts.append(
                ProductionAlert(
                    code="no_decision_maker",
                    title="Missing decision maker",
                    severity=AlertSeverity.HIGH,
                    recommendation="Run Decision Discovery before outreach.",
                    evidence=lead.blocking_reasons,
                )
            )
        if lead and not lead.checklist.business_email:
            alerts.append(
                ProductionAlert(
                    code="missing_email",
                    title="Missing business email",
                    severity=AlertSeverity.HIGH,
                    recommendation="Enrich contacts; block campaign until email verified.",
                    evidence=["business_email:missing"],
                )
            )
        if not item.oauth_ok:
            alerts.append(
                ProductionAlert(
                    code="oauth_expired",
                    title="OAuth expired",
                    severity=AlertSeverity.CRITICAL,
                    recommendation="Refresh Gmail/Meta OAuth tokens before sending.",
                    owner="ops",
                    evidence=["oauth_ok:false"],
                )
            )
        if not item.workers_online:
            alerts.append(
                ProductionAlert(
                    code="worker_offline",
                    title="Worker offline",
                    severity=AlertSeverity.CRITICAL,
                    recommendation="Restart Celery workers and verify beat schedule.",
                    owner="ops",
                    evidence=["workers_online:false"],
                )
            )
        if item.queue_depth > 500:
            alerts.append(
                ProductionAlert(
                    code="queue_blocked",
                    title="Queue blocked",
                    severity=AlertSeverity.HIGH,
                    recommendation="Drain outgoing/retry queues; check provider rate limits.",
                    owner="ops",
                    evidence=[f"queue_depth:{item.queue_depth}"],
                )
            )
        if item.duplicate_send_detected:
            alerts.append(
                ProductionAlert(
                    code="duplicate_sends",
                    title="Duplicate send detected",
                    severity=AlertSeverity.CRITICAL,
                    recommendation="Inspect idempotency keys and stop affected campaigns.",
                    owner="ops",
                    evidence=["duplicate_send:true"],
                )
            )
        if item.api_failures >= 5:
            alerts.append(
                ProductionAlert(
                    code="api_failure",
                    title="API failure spike",
                    severity=AlertSeverity.HIGH,
                    recommendation="Check API logs, dependency health, and circuit breakers.",
                    owner="ops",
                    evidence=[f"api_failures:{item.api_failures}"],
                )
            )
        if item.migration_drift:
            alerts.append(
                ProductionAlert(
                    code="migration_drift",
                    title="Migration drift",
                    severity=AlertSeverity.CRITICAL,
                    recommendation="Run alembic upgrade to head before production traffic.",
                    owner="ops",
                    evidence=["migration_drift:true"],
                )
            )
        if item.webhook_failures >= 3:
            alerts.append(
                ProductionAlert(
                    code="webhook_failure",
                    title="Webhook failures",
                    severity=AlertSeverity.HIGH,
                    recommendation="Verify webhook signatures and replay dead-letter events.",
                    owner="ops",
                    evidence=[f"webhook_failures:{item.webhook_failures}"],
                )
            )
        if health.overall_status == HealthStatus.FAIL:
            alerts.append(
                ProductionAlert(
                    code="campaign_failure",
                    title="Platform health failing",
                    severity=AlertSeverity.CRITICAL,
                    recommendation="Open Production Health dashboard and clear FAIL components first.",
                    owner="ops",
                    evidence=[f"health_score:{health.overall_score}"],
                )
            )
        return alerts
