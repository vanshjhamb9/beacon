"""Deterministic validation for connector evidence events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from opportunity_connector_platform.connector_events import EvidenceEvent, SUPPORTED_EVENT_TYPES

SUPPORTED_LANGUAGES = {"en", "unknown"}
MIN_CONFIDENCE = 40.0
MAX_EVENT_AGE_DAYS = 45


@dataclass(frozen=True, slots=True)
class ValidationResult:
    accepted: bool
    reason: str = "accepted"


class SignalValidator:
    """Deterministic event validation — no AI scoring."""

    def __init__(self) -> None:
        self._seen: set[tuple[str, str, str]] = set()

    def validate(self, event: EvidenceEvent, *, now: datetime | None = None) -> ValidationResult:
        current = now or datetime.now(UTC)
        if event.published_at.tzinfo is None:
            published = event.published_at.replace(tzinfo=UTC)
        else:
            published = event.published_at

        if not event.company_name or not event.company_name.strip():
            return ValidationResult(False, "missing_company")
        if not event.url or not event.url.strip():
            return ValidationResult(False, "missing_url")
        key = (event.connector_id.lower(), event.url.lower(), event.headline.lower())
        if key in self._seen:
            return ValidationResult(False, "duplicate_evidence")
        if published < current - timedelta(days=MAX_EVENT_AGE_DAYS):
            return ValidationResult(False, "expired")
        if event.language.lower() not in SUPPORTED_LANGUAGES:
            return ValidationResult(False, "unsupported_language")
        if event.event_type not in SUPPORTED_EVENT_TYPES:
            return ValidationResult(False, "unsupported_source")
        if event.confidence < MIN_CONFIDENCE:
            return ValidationResult(False, "low_confidence")
        if not event.headline.strip() or not event.evidence.strip():
            return ValidationResult(False, "malformed")
        self._seen.add(key)
        return ValidationResult(True)

    def reset(self) -> None:
        self._seen.clear()

    def seen_count(self) -> int:
        return len(self._seen)
