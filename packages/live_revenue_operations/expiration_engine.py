"""Expiration Engine — automatic opportunity expiration based on rules.

Signal type expiration rules:
    Hiring: 30 days
    Funding: 90 days
    Launch: 30 days
    Technology Migration: 60 days
    Conference: 15 days
    Award: 30 days
    Press: 30 days
    Government: Until deadline

Expired opportunities automatically leave active queue.
Never delete. Archive only.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from . import EXPIRATION_RULES


class ExpirationRule:
    """Single expiration rule."""

    def __init__(self, signal_type: str, days: int, description: str = ""):
        self.signal_type = signal_type
        self.days = days
        self.description = description or f"Expires after {days} days"


class ExpirationEngine:
    """Manages opportunity expiration rules and checks."""

    def __init__(self):
        self._rules: dict[str, ExpirationRule] = {}
        self._expired_records: list[dict[str, Any]] = []

        # Initialize default rules
        for signal_type, days in EXPIRATION_RULES.items():
            self._rules[signal_type] = ExpirationRule(signal_type, days)

    def add_rule(self, signal_type: str, days: int, description: str = ""):
        """Add or update expiration rule."""
        self._rules[signal_type] = ExpirationRule(signal_type, days, description)

    def remove_rule(self, signal_type: str) -> bool:
        """Remove expiration rule."""
        if signal_type in self._rules:
            del self._rules[signal_type]
            return True
        return False

    def get_rule(self, signal_type: str) -> ExpirationRule | None:
        """Get expiration rule for signal type."""
        return self._rules.get(signal_type)

    def get_all_rules(self) -> list[ExpirationRule]:
        """Get all expiration rules."""
        return list(self._rules.values())

    def calculate_expiration_date(
        self,
        created_at: datetime,
        signal_type: str,
    ) -> datetime:
        """Calculate expiration date for opportunity."""
        rule = self._rules.get(signal_type)
        days = rule.days if rule else 30  # Default 30 days
        return created_at + timedelta(days=days)

    def is_expired(
        self,
        created_at: datetime,
        signal_type: str,
        now: datetime | None = None,
    ) -> bool:
        """Check if opportunity is expired."""
        if now is None:
            now = datetime.now(timezone.utc)

        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        expiration = self.calculate_expiration_date(created_at, signal_type)
        return now > expiration

    def get_days_until_expiration(
        self,
        created_at: datetime,
        signal_type: str,
        now: datetime | None = None,
    ) -> int:
        """Get days until expiration."""
        if now is None:
            now = datetime.now(timezone.utc)

        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        expiration = self.calculate_expiration_date(created_at, signal_type)
        delta = expiration - now
        return max(0, delta.days)

    def check_and_expire(
        self,
        opportunity_id: str,
        created_at: datetime,
        signal_type: str,
        current_stage: str,
    ) -> dict[str, Any] | None:
        """Check if opportunity should be expired and record it."""
        if self.is_expired(created_at, signal_type):
            record = {
                "opportunity_id": opportunity_id,
                "signal_type": signal_type,
                "created_at": created_at.isoformat(),
                "expired_at": datetime.now(timezone.utc).isoformat(),
                "previous_stage": current_stage,
                "expiration_days": self._rules.get(signal_type, ExpirationRule(signal_type, 30)).days,
            }
            self._expired_records.append(record)
            return record
        return None

    def get_expired_records(self) -> list[dict[str, Any]]:
        """Get all expiration records."""
        return list(self._expired_records)

    def get_statistics(self) -> dict[str, Any]:
        """Get expiration statistics."""
        total_rules = len(self._rules)
        total_expired = len(self._expired_records)

        by_signal_type = {}
        for record in self._expired_records:
            signal_type = record.get("signal_type", "unknown")
            by_signal_type[signal_type] = by_signal_type.get(signal_type, 0) + 1

        return {
            "total_rules": total_rules,
            "total_expired": total_expired,
            "by_signal_type": by_signal_type,
            "rules": {rule.signal_type: rule.days for rule in self._rules.values()},
        }
