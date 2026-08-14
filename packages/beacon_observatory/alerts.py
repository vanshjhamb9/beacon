"""Alerts — observatory alerting system."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from . import AlertSeverity


class Alert:
    """Single alert."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.severity: str = data.get("severity", AlertSeverity.INFO.value)
        self.title: str = data.get("title", "")
        self.message: str = data.get("message", "")
        self.created_at: datetime = data.get("created_at", datetime.now(timezone.utc))
        self.resolved: bool = data.get("resolved", False)
        self.resolved_at: datetime | None = data.get("resolved_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class Alerting:
    """Observatory alerting system."""

    def __init__(self):
        self._alerts: list[Alert] = []

    def create_alert(
        self,
        severity: str,
        title: str,
        message: str,
    ) -> Alert:
        """Create alert."""
        alert = Alert({
            "severity": severity,
            "title": title,
            "message": message,
        })

        self._alerts.append(alert)
        return alert

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve alert."""
        for alert in self._alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now(timezone.utc)
                return True
        return False

    def get_active_alerts(self) -> list[Alert]:
        """Get unresolved alerts."""
        return [a for a in self._alerts if not a.resolved]

    def get_all_alerts(self, limit: int = 100) -> list[Alert]:
        """Get all alerts."""
        return self._alerts[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        """Get alert statistics."""
        total = len(self._alerts)
        active = sum(1 for a in self._alerts if not a.resolved)
        resolved = total - active

        by_severity: dict[str, int] = {}
        for a in self._alerts:
            by_severity[a.severity] = by_severity.get(a.severity, 0) + 1

        return {
            "total_alerts": total,
            "active": active,
            "resolved": resolved,
            "by_severity": by_severity,
        }
