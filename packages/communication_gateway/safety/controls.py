from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any


@dataclass
class SafetyDecision:
    allowed: bool
    reason: str | None = None
    code: str | None = None
    evidence: list[str] = field(default_factory=list)


class SafetyControls:
    """Rate limits, duplicate prevention, and stop-rule helpers (provider-agnostic)."""

    def __init__(self, *, daily_email_quota: int = 500, hourly_email_quota: int = 80) -> None:
        self.daily_email_quota = daily_email_quota
        self.hourly_email_quota = hourly_email_quota
        self._sent_keys: set[str] = set()
        self._webhook_keys: set[str] = set()
        self._daily_counts: dict[str, int] = {}
        self._hourly_counts: dict[str, int] = {}

    def check_send(
        self,
        *,
        idempotency_key: str | None,
        campaign_stopped: bool,
        stop_reason: str | None = None,
        sent_today: int = 0,
        sent_this_hour: int = 0,
        duplicate_exists: bool = False,
    ) -> SafetyDecision:
        evidence: list[str] = []
        if campaign_stopped:
            return SafetyDecision(
                allowed=False,
                reason=f"Campaign stopped ({stop_reason or 'unknown'})",
                code="campaign_stopped",
                evidence=["stop_rule:true"],
            )
        if duplicate_exists:
            return SafetyDecision(
                allowed=False,
                reason="Duplicate send blocked",
                code="duplicate_send",
                evidence=[f"idempotency_key:{idempotency_key or 'n/a'}"],
            )
        if idempotency_key and idempotency_key in self._sent_keys:
            return SafetyDecision(
                allowed=False,
                reason="Idempotency key already used",
                code="duplicate_send",
                evidence=[f"idempotency_key:{idempotency_key}"],
            )
        day = date.today().isoformat()
        hour = datetime.now(UTC).strftime("%Y-%m-%dT%H")
        count = self._daily_counts.get(day, sent_today)
        hour_count = self._hourly_counts.get(hour, sent_this_hour)
        evidence.append(f"sent_today:{count}")
        evidence.append(f"quota:{self.daily_email_quota}")
        evidence.append(f"sent_this_hour:{hour_count}")
        evidence.append(f"hourly_quota:{self.hourly_email_quota}")
        if hour_count >= self.hourly_email_quota:
            return SafetyDecision(
                allowed=False,
                reason="Hourly email quota exceeded",
                code="hourly_quota_exceeded",
                evidence=evidence,
            )
        if count >= self.daily_email_quota:
            return SafetyDecision(
                allowed=False,
                reason="Daily email quota exceeded",
                code="quota_exceeded",
                evidence=evidence,
            )
        return SafetyDecision(allowed=True, evidence=evidence)

    def record_send(self, *, idempotency_key: str | None = None) -> None:
        day = date.today().isoformat()
        hour = datetime.now(UTC).strftime("%Y-%m-%dT%H")
        self._daily_counts[day] = self._daily_counts.get(day, 0) + 1
        self._hourly_counts[hour] = self._hourly_counts.get(hour, 0) + 1
        if idempotency_key:
            self._sent_keys.add(idempotency_key)

    def check_webhook(self, *, fingerprint: str, already_processed: bool = False) -> SafetyDecision:
        if already_processed or fingerprint in self._webhook_keys:
            return SafetyDecision(
                allowed=False,
                reason="Webhook already processed",
                code="duplicate_webhook",
                evidence=[f"fingerprint:{fingerprint}"],
            )
        return SafetyDecision(allowed=True, evidence=[f"fingerprint:{fingerprint}"])

    def record_webhook(self, fingerprint: str) -> None:
        self._webhook_keys.add(fingerprint)

    def webhook_fingerprint(self, provider: str, payload: dict[str, Any]) -> str:
        """Deterministic fingerprint for idempotent webhook ingest."""
        hint = (
            str(payload.get("messageId") or "")
            or str(payload.get("historyId") or "")
            or str((payload.get("message") or {}).get("data") or "")
            or str(payload.get("id") or "")
        )
        return f"{provider}:{hint or hash(str(sorted(payload.items())) % 10_000_000)}"
