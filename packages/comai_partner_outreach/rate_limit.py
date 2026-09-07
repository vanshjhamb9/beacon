"""Rate limits, business hours, and kill-switch helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from comai_partner_outreach.config import PartnerOutreachConfig

try:
    from zoneinfo import ZoneInfo

    IST = ZoneInfo("Asia/Kolkata")
except Exception:  # noqa: BLE001
    IST = timezone(timedelta(hours=5, minutes=30))


@dataclass
class RateLimitState:
    send_timestamps: list[str] = field(default_factory=list)
    last_send_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "send_timestamps": self.send_timestamps,
            "last_send_at": self.last_send_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RateLimitState:
        data = data or {}
        return cls(
            send_timestamps=list(data.get("send_timestamps") or []),
            last_send_at=data.get("last_send_at"),
        )


@dataclass
class SendGateResult:
    allowed: bool
    reason: str = ""
    code: str = "ok"
    retry_after_seconds: int = 0


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        return None


def prune_timestamps(state: RateLimitState, *, now: datetime | None = None) -> RateLimitState:
    now = now or datetime.now(UTC)
    cutoff = now - timedelta(hours=24)
    kept: list[str] = []
    for ts in state.send_timestamps:
        dt = _parse_ts(ts)
        if dt and dt >= cutoff:
            kept.append(ts)
    state.send_timestamps = kept
    return state


def within_business_hours(config: PartnerOutreachConfig, *, now: datetime | None = None) -> bool:
    now_ist = (now or datetime.now(UTC)).astimezone(IST)
    if config.weekdays_only and now_ist.weekday() >= 5:
        return False
    return config.business_start_hour <= now_ist.hour < config.business_end_hour


def check_send_gate(
    config: PartnerOutreachConfig,
    state: RateLimitState,
    *,
    campaign_killed: bool = False,
    now: datetime | None = None,
) -> SendGateResult:
    now = now or datetime.now(UTC)
    if campaign_killed:
        return SendGateResult(False, "Campaign kill switch active", "campaign_killed")
    if not config.enabled and not config.dry_run:
        # enabled=false forces dry_run via config.dry_run property; this is belt-and-suspenders
        return SendGateResult(False, "Global kill switch COMAI_PARTNER_OUTREACH_ENABLED is off", "kill_switch")

    state = prune_timestamps(state, now=now)
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(hours=24)
    hour_count = sum(1 for ts in state.send_timestamps if (dt := _parse_ts(ts)) and dt >= hour_ago)
    day_count = sum(1 for ts in state.send_timestamps if (dt := _parse_ts(ts)) and dt >= day_ago)

    if hour_count >= config.max_per_hour:
        return SendGateResult(False, "Hourly send cap reached", "rate_hour", retry_after_seconds=300)
    if day_count >= config.max_per_day:
        return SendGateResult(False, "Daily send cap reached", "rate_day", retry_after_seconds=1800)

    last = _parse_ts(state.last_send_at)
    if last:
        elapsed = (now - last).total_seconds()
        if elapsed < config.min_seconds_between_sends:
            wait = int(config.min_seconds_between_sends - elapsed) + 1
            return SendGateResult(False, "Inter-send delay", "rate_gap", retry_after_seconds=wait)

    if not within_business_hours(config, now=now):
        return SendGateResult(False, "Outside IST business hours", "business_hours", retry_after_seconds=600)

    return SendGateResult(True, "ok", "ok")


def record_send(state: RateLimitState, *, now: datetime | None = None) -> RateLimitState:
    now = now or datetime.now(UTC)
    ts = now.isoformat()
    state.send_timestamps.append(ts)
    state.last_send_at = ts
    return prune_timestamps(state, now=now)
