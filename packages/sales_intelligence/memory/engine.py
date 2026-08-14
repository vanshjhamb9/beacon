from __future__ import annotations

from datetime import UTC, datetime

from sales_intelligence.models.types import MemoryEvent, MemoryEventType, SalesIntelligenceInput, SalesMemory


def _parse_dt(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            return None
    return None


class SalesMemoryEngine:
    def build(self, item: SalesIntelligenceInput) -> SalesMemory:
        events: list[MemoryEvent] = []
        for i, email in enumerate(item.emails):
            events.append(
                MemoryEvent(
                    event_type=MemoryEventType.EMAIL,
                    title=str(email.get("subject") or f"Email {i + 1}"),
                    detail=str(email.get("body") or email.get("snippet") or "")[:500],
                    occurred_at=_parse_dt(email.get("occurred_at") or email.get("sent_at")),
                    refs={"index": i},
                    evidence=[f"email_index:{i}"],
                )
            )
        for i, reply in enumerate(item.replies):
            events.append(
                MemoryEvent(
                    event_type=MemoryEventType.REPLY,
                    title=str(reply.get("subject") or f"Reply {i + 1}"),
                    detail=str(reply.get("body") or reply.get("snippet") or "")[:500],
                    occurred_at=_parse_dt(reply.get("occurred_at") or reply.get("received_at")),
                    refs={"index": i},
                    evidence=[f"reply_index:{i}"],
                )
            )
        for i, meeting in enumerate(item.meetings):
            events.append(
                MemoryEvent(
                    event_type=MemoryEventType.MEETING,
                    title=str(meeting.get("title") or f"Meeting {i + 1}"),
                    detail=str(meeting.get("notes") or meeting.get("summary") or "")[:500],
                    occurred_at=_parse_dt(meeting.get("occurred_at") or meeting.get("scheduled_at")),
                    refs={"index": i},
                    evidence=[f"meeting_index:{i}"],
                )
            )
        for i, proposal in enumerate(item.proposals):
            events.append(
                MemoryEvent(
                    event_type=MemoryEventType.PROPOSAL,
                    title=str(proposal.get("title") or f"Proposal {i + 1}"),
                    detail=str(proposal.get("status") or proposal.get("summary") or "")[:500],
                    occurred_at=_parse_dt(proposal.get("occurred_at") or proposal.get("sent_at")),
                    refs={"index": i},
                    evidence=[f"proposal_index:{i}"],
                )
            )
        for i, obj in enumerate(item.objections_seen):
            events.append(
                MemoryEvent(
                    event_type=MemoryEventType.OBJECTION,
                    title=f"Objection: {obj}",
                    detail=obj,
                    refs={"index": i},
                    evidence=[f"objection:{obj}"],
                )
            )
        for i, note in enumerate(item.notes):
            events.append(
                MemoryEvent(
                    event_type=MemoryEventType.NOTE,
                    title=f"Note {i + 1}",
                    detail=note[:500],
                    refs={"index": i},
                    evidence=[f"note_index:{i}"],
                )
            )
        for i, outcome in enumerate(item.outcomes):
            events.append(
                MemoryEvent(
                    event_type=MemoryEventType.OUTCOME,
                    title=str(outcome.get("type") or outcome.get("name") or f"Outcome {i + 1}"),
                    detail=str(outcome.get("detail") or outcome.get("status") or "")[:500],
                    occurred_at=_parse_dt(outcome.get("occurred_at")),
                    refs={"index": i},
                    evidence=[f"outcome_index:{i}"],
                )
            )
        for i, fu in enumerate(item.follow_ups):
            events.append(
                MemoryEvent(
                    event_type=MemoryEventType.FOLLOW_UP,
                    title=str(fu.get("title") or f"Follow-up {i + 1}"),
                    detail=str(fu.get("detail") or fu.get("status") or "")[:500],
                    occurred_at=_parse_dt(fu.get("occurred_at") or fu.get("due_at")),
                    refs={"index": i},
                    evidence=[f"follow_up_index:{i}"],
                )
            )

        events.sort(key=lambda e: ((e.occurred_at or datetime.min.replace(tzinfo=UTC)).isoformat(), e.event_type.value, e.title))
        timeline = [
            {
                "type": e.event_type.value,
                "title": e.title,
                "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
                "detail": e.detail[:160],
            }
            for e in events
        ]
        return SalesMemory(events=events, relationship_timeline=timeline, buying_journey=self._journey(item, events))

    def _journey(self, item: SalesIntelligenceInput, events: list[MemoryEvent]) -> list[dict]:
        return [
            {"stage": "outreach", "done": any(e.event_type == MemoryEventType.EMAIL for e in events)},
            {"stage": "engagement", "done": any(e.event_type == MemoryEventType.REPLY for e in events)},
            {"stage": "discovery", "done": any(e.event_type == MemoryEventType.MEETING for e in events)},
            {"stage": "proposal", "done": any(e.event_type == MemoryEventType.PROPOSAL for e in events)},
            {"stage": "objection_handling", "done": any(e.event_type == MemoryEventType.OBJECTION for e in events)},
            {
                "stage": "close",
                "done": any(
                    "won" in str(o).lower() or "closed" in str(o).lower() for o in item.outcomes
                ),
            },
        ]
