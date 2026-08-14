"""Aging Engine — tracks opportunity age with color coding.

Every opportunity has age (minutes, hours, days, weeks).
Color coding: Green (fresh), Yellow (needs attention), Orange (getting stale), Red (expired).
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from . import AgingColor, EXPIRATION_RULES, AGING_THRESHOLDS


class AgingInfo:
    """Aging information for an opportunity."""

    def __init__(self, data: dict[str, Any]):
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.created_at: datetime = data.get("created_at", datetime.now(timezone.utc))
        self.signal_type: str = data.get("signal_type", "unknown")
        self.current_stage: str = data.get("current_stage", "new")

    def get_age(self, now: datetime | None = None) -> dict[str, Any]:
        """Get age in multiple units."""
        if now is None:
            now = datetime.now(timezone.utc)

        if self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc)

        delta = now - self.created_at
        total_seconds = int(delta.total_seconds())

        return {
            "total_seconds": total_seconds,
            "minutes": total_seconds // 60,
            "hours": total_seconds // 3600,
            "days": delta.days,
            "weeks": delta.days // 7,
        }

    def get_color(self, now: datetime | None = None) -> AgingColor:
        """Get color coding based on age."""
        age = self.get_age(now)
        days = age["days"]

        if days <= AGING_THRESHOLDS[AgingColor.GREEN]:
            return AgingColor.GREEN
        elif days <= AGING_THRESHOLDS[AgingColor.YELLOW]:
            return AgingColor.YELLOW
        elif days <= AGING_THRESHOLDS[AgingColor.ORANGE]:
            return AgingColor.ORANGE
        else:
            return AgingColor.RED

    def is_expired(self, now: datetime | None = None) -> bool:
        """Check if opportunity has expired."""
        if now is None:
            now = datetime.now(timezone.utc)

        expiration_days = EXPIRATION_RULES.get(self.signal_type, 30)
        age = self.get_age(now)
        return age["days"] > expiration_days

    def get_expiration_date(self) -> datetime:
        """Get expiration date based on signal type."""
        expiration_days = EXPIRATION_RULES.get(self.signal_type, 30)
        return self.created_at + timedelta(days=expiration_days)

    def get_days_until_expiration(self, now: datetime | None = None) -> int:
        """Get days until expiration."""
        if now is None:
            now = datetime.now(timezone.utc)
        expiration = self.get_expiration_date()
        delta = expiration - now
        return max(0, delta.days)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        age = self.get_age()
        color = self.get_color()
        return {
            "opportunity_id": self.opportunity_id,
            "age": age,
            "color": color.value,
            "is_expired": self.is_expired(),
            "expiration_date": self.get_expiration_date().isoformat(),
            "days_until_expiration": self.get_days_until_expiration(),
        }


class AgingEngine:
    """Tracks and manages opportunity aging."""

    def __init__(self):
        self._aging_records: dict[str, AgingInfo] = {}
        self._expired_ids: list[str] = []

    def track_opportunity(
        self,
        opportunity_id: str,
        created_at: datetime,
        signal_type: str,
        current_stage: str = "new",
    ) -> AgingInfo:
        """Start tracking opportunity aging."""
        info = AgingInfo({
            "opportunity_id": opportunity_id,
            "created_at": created_at,
            "signal_type": signal_type,
            "current_stage": current_stage,
        })
        self._aging_records[opportunity_id] = info
        return info

    def get_aging(self, opportunity_id: str) -> AgingInfo | None:
        """Get aging info for opportunity."""
        return self._aging_records.get(opportunity_id)

    def update_stage(self, opportunity_id: str, new_stage: str):
        """Update opportunity stage."""
        info = self._aging_records.get(opportunity_id)
        if info:
            info.current_stage = new_stage

    def check_expiration(self, opportunity_id: str) -> bool:
        """Check and record if opportunity expired."""
        info = self._aging_records.get(opportunity_id)
        if not info:
            return False

        if info.is_expired() and opportunity_id not in self._expired_ids:
            self._expired_ids.append(opportunity_id)
            return True
        return False

    def get_expired(self) -> list[AgingInfo]:
        """Get all expired opportunities."""
        return [
            info for info in self._aging_records.values()
            if info.is_expired()
        ]

    def get_by_color(self, color: AgingColor) -> list[AgingInfo]:
        """Get opportunities by color coding."""
        return [
            info for info in self._aging_records.values()
            if info.get_color() == color
        ]

    def get_expiring_soon(self, days: int = 7) -> list[AgingInfo]:
        """Get opportunities expiring within N days."""
        return [
            info for info in self._aging_records.values()
            if 0 < info.get_days_until_expiration() <= days
        ]

    def get_statistics(self) -> dict[str, Any]:
        """Get aging statistics."""
        total = len(self._aging_records)
        by_color = {color.value: 0 for color in AgingColor}
        expired_count = 0

        for info in self._aging_records.values():
            color = info.get_color()
            by_color[color.value] += 1
            if info.is_expired():
                expired_count += 1

        return {
            "total_tracked": total,
            "by_color": by_color,
            "expired": expired_count,
            "active": total - expired_count,
        }
