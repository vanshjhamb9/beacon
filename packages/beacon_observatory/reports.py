"""Reports — observatory report generation."""

from datetime import datetime, timezone
from typing import Any


class Reports:
    """Observatory report generation."""

    def __init__(self):
        self._reports: list[dict[str, Any]] = []

    def generate_report(
        self,
        report_type: str,
        title: str,
        data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate report."""
        report = {
            "report_type": report_type,
            "title": title,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data": data,
            "metadata": metadata or {},
        }

        self._reports.append(report)
        return report

    def get_reports(self, report_type: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Get reports."""
        if report_type:
            return [r for r in self._reports if r["report_type"] == report_type][-limit:]
        return self._reports[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        """Get report statistics."""
        types: dict[str, int] = {}
        for r in self._reports:
            types[r["report_type"]] = types.get(r["report_type"], 0) + 1

        return {
            "total_reports": len(self._reports),
            "by_type": types,
        }
