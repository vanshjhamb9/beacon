from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from account_intelligence.models.types import FieldValue


def field(
    value: Any,
    *,
    confidence: float,
    source: str,
    now: datetime | None = None,
    evidence: list[str] | None = None,
    conflicts: list[str] | None = None,
) -> FieldValue:
    """Build an attributed field. Missing values get confidence 0 and are never invented."""
    if value is None or value == "" or value == []:
        return FieldValue(
            value=None,
            confidence=0.0,
            source=source,
            last_verified=None,
            evidence=["missing:true", "never_fabricate:true", *(evidence or [])],
            conflicts=conflicts or [],
        )
    return FieldValue(
        value=value,
        confidence=max(0.0, min(100.0, confidence)),
        source=source,
        last_verified=now or datetime.now(UTC),
        evidence=evidence or [f"source:{source}"],
        conflicts=conflicts or [],
    )
