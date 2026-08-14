"""Verification Engine — verifies dashboard data is live."""

from datetime import datetime, timezone
from typing import Any

from . import DataType


class VerificationRecord:
    """Single verification record."""

    def __init__(self, data: dict[str, Any]):
        self.widget_name: str = data.get("widget_name", "unknown")
        self.source_query: str = data.get("source_query", "")
        self.rows_returned: int = data.get("rows_returned", 0)
        self.timestamp: datetime = data.get("timestamp", datetime.now(timezone.utc))
        self.data_type: str = data.get("data_type", DataType.UNKNOWN.value)
        self.is_live: bool = data.get("is_live", False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "widget_name": self.widget_name,
            "source_query": self.source_query,
            "rows_returned": self.rows_returned,
            "timestamp": self.timestamp.isoformat(),
            "data_type": self.data_type,
            "is_live": self.is_live,
        }


class VerificationEngine:
    """Verifies dashboard data is live."""

    def __init__(self):
        self._records: list[VerificationRecord] = []
        self._widget_status: dict[str, dict[str, Any]] = {}

    def verify_widget(
        self,
        widget_name: str,
        source_query: str,
        rows_returned: int,
        data_type: str = DataType.LIVE.value,
    ) -> VerificationRecord:
        """Verify a dashboard widget."""
        record = VerificationRecord({
            "widget_name": widget_name,
            "source_query": source_query,
            "rows_returned": rows_returned,
            "data_type": data_type,
            "is_live": data_type == DataType.LIVE.value,
        })

        self._records.append(record)
        self._widget_status[widget_name] = record.to_dict()

        return record

    def get_widget_status(self, widget_name: str) -> dict[str, Any] | None:
        """Get widget verification status."""
        return self._widget_status.get(widget_name)

    def get_all_status(self) -> dict[str, dict[str, Any]]:
        """Get all widget statuses."""
        return dict(self._widget_status)

    def get_live_widgets(self) -> list[str]:
        """Get widgets with live data."""
        return [
            name for name, status in self._widget_status.items()
            if status.get("is_live", False)
        ]

    def get_cached_widgets(self) -> list[str]:
        """Get widgets with cached data."""
        return [
            name for name, status in self._widget_status.items()
            if status.get("data_type") == DataType.CACHED.value
        ]

    def get_statistics(self) -> dict[str, Any]:
        """Get verification statistics."""
        total = len(self._widget_status)
        live = len(self.get_live_widgets())
        cached = len(self.get_cached_widgets())

        return {
            "total_widgets": total,
            "live": live,
            "cached": cached,
            "unknown": total - live - cached,
        }
