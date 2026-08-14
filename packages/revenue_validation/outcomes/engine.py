"""Outcome event helpers — append-only validation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from revenue_validation.models.types import OFC_TO_OUTCOME, OutcomeEvent, OutcomeType


class OutcomeEngine:
    def from_ofc_status(
        self,
        *,
        company_id: str,
        outreach_record_id: str | None,
        status: str,
        previous: str | None = None,
        actor: str = "system",
        source: str = "ofc_sync",
        notes: str | None = None,
    ) -> OutcomeEvent:
        outcome = OFC_TO_OUTCOME.get(status, OutcomeType.READY)
        return OutcomeEvent(
            company_id=company_id,
            outreach_record_id=outreach_record_id,
            outcome=outcome,
            timestamp=datetime.now(UTC).isoformat(),
            actor=actor,
            source=source,
            notes=notes,
            previous_state=previous,
            new_state=status,
        )

    def transition(
        self,
        *,
        company_id: str,
        outreach_record_id: str | None,
        outcome: str,
        previous_state: str | None,
        actor: str = "founder",
        source: str = "clr",
        notes: str | None = None,
    ) -> OutcomeEvent:
        ot = OutcomeType(outcome)
        return OutcomeEvent(
            company_id=company_id,
            outreach_record_id=outreach_record_id,
            outcome=ot,
            timestamp=datetime.now(UTC).isoformat(),
            actor=actor,
            source=source,
            notes=notes,
            previous_state=previous_state,
            new_state=ot.value,
        )

    def latest_state(self, events: list[dict[str, Any]]) -> str | None:
        if not events:
            return None
        ordered = sorted(events, key=lambda e: str(e.get("timestamp") or e.get("created_at") or ""))
        last = ordered[-1]
        return str(last.get("new_state") or last.get("outcome") or "")
