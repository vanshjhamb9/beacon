from __future__ import annotations

from datetime import UTC, datetime

from autonomous_sales_agent.models.types import AutonomousSalesAgentInput, TimelineEvent


class RelationshipTimelineEngine:
    """Append-only relationship timeline composed from sales signals."""

    def build(self, item: AutonomousSalesAgentInput) -> list[TimelineEvent]:
        now = item.now or datetime.now(UTC)
        events: list[TimelineEvent] = []
        events.append(
            TimelineEvent(
                event_type="website_discovered",
                title=f"Website/account discovered: {item.company_name}",
                detail=item.industry or "",
                occurred_at=now,
                evidence=["source:discovery"],
            )
        )
        if item.has_decision_makers or item.decision_makers:
            events.append(
                TimelineEvent(
                    event_type="decision_maker_added",
                    title="Decision maker added",
                    detail=str(item.decision_makers[0].get("name") if item.decision_makers else "known"),
                    occurred_at=now,
                    evidence=[f"count:{len(item.decision_makers)}"],
                )
            )
        if item.email_sent:
            events.append(TimelineEvent(event_type="email_sent", title="Email sent", occurred_at=now, evidence=["channel:email"]))
        if "opened" in " ".join(item.recent_activity).lower():
            events.append(TimelineEvent(event_type="email_opened", title="Email opened", occurred_at=now, evidence=["signal:open"]))
        if item.reply_received:
            events.append(TimelineEvent(event_type="reply_received", title="Reply received", occurred_at=now, evidence=["channel:inbound"]))
        if item.meeting_booked:
            events.append(TimelineEvent(event_type="meeting_booked", title="Meeting booked", occurred_at=now, evidence=["channel:calendar"]))
        if item.meeting_completed:
            events.append(TimelineEvent(event_type="meeting_completed", title="Meeting completed", occurred_at=now, evidence=["stage:post_meeting"]))
        if item.proposal_pending:
            events.append(TimelineEvent(event_type="proposal_pending", title="Proposal pending", occurred_at=now, evidence=["founder:write"]))
        if item.proposal_sent:
            events.append(TimelineEvent(event_type="proposal_sent", title="Proposal sent", occurred_at=now, evidence=["channel:proposal"]))
        if item.won:
            events.append(TimelineEvent(event_type="won", title="Deal won", occurred_at=now, evidence=["outcome:won"]))
        if item.lost:
            events.append(TimelineEvent(event_type="lost", title="Deal lost", occurred_at=now, evidence=["outcome:lost"]))
        for note in item.founder_notes:
            events.append(
                TimelineEvent(
                    event_type="founder_note",
                    title="Founder note",
                    detail=note[:400],
                    occurred_at=now,
                    actor="founder",
                    evidence=["actor:founder"],
                )
            )
        for seed in item.timeline_seeds:
            events.append(
                TimelineEvent(
                    event_type=str(seed.get("event_type") or "activity"),
                    title=str(seed.get("title") or "Activity"),
                    detail=str(seed.get("detail") or ""),
                    occurred_at=now,
                    actor=str(seed.get("actor") or "system"),
                    evidence=[f"seed:{seed.get('event_type')}"],
                )
            )
        return events
