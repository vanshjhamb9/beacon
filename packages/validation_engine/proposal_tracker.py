"""Proposal tracker — records all proposal events for companies.

Append-only. Never overwrites. Every proposal state change is recorded.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from validation_engine import PROPOSAL_STATUSES
from validation_engine.models import ProposalEvent


class ProposalTracker:
    """Tracks proposal events (created, sent, viewed, accepted, rejected, expired)."""

    def __init__(self) -> None:
        self._proposals: dict[str, list[ProposalEvent]] = {}
        self._all_proposals: list[ProposalEvent] = []

    def record_proposal(
        self,
        company_id: str,
        status: str,
        *,
        value: float | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> ProposalEvent:
        if status not in PROPOSAL_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {PROPOSAL_STATUSES}")

        event = ProposalEvent(
            company_id=company_id,
            status=status,
            timestamp=datetime.now(UTC),
            value=value,
            evidence=evidence or {},
        )
        self._proposals.setdefault(company_id, []).append(event)
        self._all_proposals.append(event)
        return event

    def get_proposals_for_company(self, company_id: str) -> list[ProposalEvent]:
        return list(self._proposals.get(company_id, []))

    def get_all_proposals(self) -> list[ProposalEvent]:
        return list(self._all_proposals)

    def get_sent_proposals(self) -> list[ProposalEvent]:
        return [p for p in self._all_proposals if p.status == "sent"]

    def get_accepted_proposals(self) -> list[ProposalEvent]:
        return [p for p in self._all_proposals if p.status == "accepted"]

    def get_rejected_proposals(self) -> list[ProposalEvent]:
        return [p for p in self._all_proposals if p.status == "rejected"]

    def get_expired_proposals(self) -> list[ProposalEvent]:
        return [p for p in self._all_proposals if p.status == "expired"]

    def get_proposal_rate(self) -> float:
        if not self._all_proposals:
            return 0.0
        sent = len(self.get_sent_proposals())
        return (sent / len(self._all_proposals)) * 100.0

    def get_acceptance_rate(self) -> float:
        sent = self.get_sent_proposals()
        if not sent:
            return 0.0
        accepted = len(self.get_accepted_proposals())
        return (accepted / len(sent)) * 100.0

    def get_total_proposal_value(self) -> float:
        return sum(p.value or 0.0 for p in self._all_proposals)

    def get_status_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for proposal in self._all_proposals:
            counts[proposal.status] = counts.get(proposal.status, 0) + 1
        return counts

    def get_todays_proposals(self) -> list[ProposalEvent]:
        today = datetime.now(UTC).date()
        return [p for p in self._all_proposals if p.timestamp.date() == today]
