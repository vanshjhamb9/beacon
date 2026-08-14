"""Deterministic daily action — answers: What should Vansh do today?"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from operation_first_customer.models.types import DailyAction, OutreachStatus


class DailyActionEngine:
    def decide(self, records: list[dict[str, Any]]) -> DailyAction:
        if not records:
            return DailyAction(
                action="No Revenue Ready outreach records — run RRP perfect, then sync OFC workspace.",
                why="Empty pipeline cannot produce a first customer.",
                priority=1,
            )

        won = [r for r in records if r.get("status") == OutreachStatus.WON]
        if won:
            return DailyAction(
                action=f"Protect and onboard won account: {won[0].get('company')}",
                company=str(won[0].get("company")),
                company_id=str(won[0].get("company_id") or ""),
                status=OutreachStatus.WON,
                why="First customer closed — confirm delivery kickoff today.",
                priority=1,
            )

        for status, verb, why in (
            (OutreachStatus.NEGOTIATION, "Close or clarify next commercial step with", "Active negotiation needs founder attention"),
            (OutreachStatus.PROPOSAL_SENT, "Follow up on proposal with", "Proposal awaiting response"),
            (OutreachStatus.MEETING_BOOKED, "Send proposal after meeting with", "Meeting booked — convert to proposal"),
            (OutreachStatus.REPLIED, "Book a meeting with", "Reply received — book while warm"),
        ):
            hit = self._first(records, status)
            if hit:
                return self._action(hit, f"{verb} {hit.get('company')}", why)

        stale = self._stale_contacted(records, days=3)
        if stale:
            brief = stale.get("brief") or {}
            return self._action(
                stale,
                f"Follow up with {stale.get('company')}",
                "Contacted ≥3 days ago with no reply — send a short follow-up",
                channel=brief.get("business_email") or brief.get("decision_maker_email"),
            )

        ready = self._best_ready(records)
        if ready:
            brief = ready.get("brief") or {}
            email = brief.get("decision_maker_email") or brief.get("business_email")
            return DailyAction(
                action=f"Contact {ready.get('company')} today",
                company=str(ready.get("company")),
                company_id=str(ready.get("company_id") or ""),
                status=OutreachStatus.READY,
                why=str(brief.get("why_now") or brief.get("recommended_cta") or "Revenue Ready — first outreach"),
                channel=email,
                priority=1,
            )

        return DailyAction(
            action="Review paused/lost records and unpause the strongest READY candidate",
            why="No active READY/CONTACTED work items in the funnel",
            priority=2,
        )

    def _first(self, records: list[dict[str, Any]], status: OutreachStatus) -> dict[str, Any] | None:
        for r in sorted(records, key=lambda x: float((x.get("brief") or {}).get("revenue_ready_score") or 0), reverse=True):
            if r.get("status") == status:
                return r
        return None

    def _best_ready(self, records: list[dict[str, Any]]) -> dict[str, Any] | None:
        ready = [r for r in records if r.get("status") == OutreachStatus.READY]
        if not ready:
            return None
        return sorted(
            ready,
            key=lambda x: float((x.get("brief") or {}).get("revenue_ready_score") or 0),
            reverse=True,
        )[0]

    def _stale_contacted(self, records: list[dict[str, Any]], *, days: int) -> dict[str, Any] | None:
        now = datetime.now(UTC)
        stale: list[tuple[float, dict[str, Any]]] = []
        for r in records:
            if r.get("status") != OutreachStatus.CONTACTED:
                continue
            hist = list(r.get("status_history") or [])
            at = None
            for h in reversed(hist):
                if h.get("status") == OutreachStatus.CONTACTED:
                    at = h.get("at")
                    break
            if not at:
                continue
            try:
                ts = datetime.fromisoformat(str(at).replace("Z", "+00:00"))
            except ValueError:
                continue
            age = (now - ts).total_seconds() / 86400.0
            if age >= days:
                stale.append((age, r))
        if not stale:
            return None
        stale.sort(key=lambda x: x[0], reverse=True)
        return stale[0][1]

    def _action(
        self,
        record: dict[str, Any],
        action: str,
        why: str,
        *,
        channel: str | None = None,
    ) -> DailyAction:
        brief = record.get("brief") or {}
        return DailyAction(
            action=action,
            company=str(record.get("company")),
            company_id=str(record.get("company_id") or ""),
            status=str(record.get("status")),
            why=why,
            channel=channel or brief.get("business_email") or brief.get("decision_maker_email"),
            priority=1,
        )
