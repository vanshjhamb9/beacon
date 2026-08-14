"""RDAP recovery queue reasons."""

from __future__ import annotations

from typing import Any

from revenue_data_acquisition.models.types import RecoveryReason


class RdapRecoveryEngine:
    def reasons(self, *, website: str | None, emails: list, dms: list, confidence: float) -> list[RecoveryReason]:
        out: list[RecoveryReason] = []
        if not website:
            out.append(RecoveryReason.WEBSITE_MISSING)
        if website and not emails:
            out.append(RecoveryReason.EMAIL_MISSING)
        if website and not dms:
            out.append(RecoveryReason.DECISION_MAKER_MISSING)
        if confidence and confidence < 50:
            out.append(RecoveryReason.LOW_CONFIDENCE)
        return out

    def from_payload(self, payload: dict[str, Any], *, website: str | None, emails: list, dms: list) -> list[RecoveryReason]:
        return self.reasons(
            website=website,
            emails=emails,
            dms=dms,
            confidence=float(payload.get("confidence") or 0),
        )
