from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from conversation_center.models.types import (
    ConversationChannel,
    ConversationFilter,
    ConversationItem,
    ConversationItemType,
    ConversationThread,
)


class ConversationCenterService:
    """In-memory conversation center used by domain tests; API persists via repository."""

    def __init__(self) -> None:
        self.threads: dict[UUID, ConversationThread] = {}
        self.items: list[ConversationItem] = []

    def upsert_thread(
        self,
        *,
        company_id: UUID,
        subject: str,
        opportunity_id: UUID | None = None,
        campaign_id: UUID | None = None,
        participants: list[str] | None = None,
    ) -> ConversationThread:
        for thread in self.threads.values():
            if thread.company_id == company_id and thread.subject == subject:
                return thread
        thread = ConversationThread(
            id=uuid4(),
            company_id=company_id,
            opportunity_id=opportunity_id,
            campaign_id=campaign_id,
            subject=subject,
            participants=participants or [],
            last_activity_at=datetime.now(UTC),
        )
        self.threads[thread.id] = thread  # type: ignore[index]
        return thread

    def add_item(self, item: ConversationItem) -> ConversationItem:
        thread_id = item.conversation_id
        if thread_id is None:
            thread = self.upsert_thread(
                company_id=item.company_id,
                subject=item.subject or "Conversation",
                opportunity_id=item.opportunity_id,
                campaign_id=item.campaign_id,
                participants=[x for x in [item.from_address, item.to_address] if x],
            )
            thread_id = thread.id
        stored = item.model_copy(
            update={
                "id": item.id or uuid4(),
                "conversation_id": thread_id,
                "occurred_at": item.occurred_at or datetime.now(UTC),
            }
        )
        self.items.append(stored)
        thread = self.threads[thread_id]  # type: ignore[index]
        channels = list(thread.channels)
        if stored.channel not in channels:
            channels.append(stored.channel)
        unread = thread.unread_count + (1 if stored.unread else 0)
        self.threads[thread_id] = thread.model_copy(  # type: ignore[index]
            update={
                "channels": channels,
                "unread_count": unread,
                "last_activity_at": stored.occurred_at,
                "items": [*thread.items, stored],
            }
        )
        return stored

    def timeline(self, conversation_id: UUID) -> list[ConversationItem]:
        return sorted(
            [item for item in self.items if item.conversation_id == conversation_id],
            key=lambda row: row.occurred_at or datetime.min.replace(tzinfo=UTC),
        )

    def search(self, filters: ConversationFilter) -> list[ConversationThread]:
        rows = list(self.threads.values())
        if filters.company_id:
            rows = [row for row in rows if row.company_id == filters.company_id]
        if filters.pinned_only:
            rows = [row for row in rows if row.pinned]
        if filters.unread_only:
            rows = [row for row in rows if row.unread_count > 0]
        if filters.channel:
            rows = [row for row in rows if filters.channel in row.channels]
        if filters.query:
            q = filters.query.lower()
            rows = [
                row
                for row in rows
                if q in row.subject.lower()
                or any(q in (item.body or "").lower() for item in row.items)
            ]
        rows.sort(key=lambda row: row.last_activity_at or datetime.min.replace(tzinfo=UTC), reverse=True)
        return rows[filters.offset : filters.offset + filters.limit]

    def add_note(self, *, company_id: UUID, body: str, conversation_id: UUID | None = None) -> ConversationItem:
        return self.add_item(
            ConversationItem(
                conversation_id=conversation_id,
                company_id=company_id,
                channel=ConversationChannel.NOTE,
                item_type=ConversationItemType.NOTE,
                direction="internal",
                body=body,
                unread=False,
            )
        )

    def add_internal_comment(self, *, company_id: UUID, body: str, conversation_id: UUID) -> ConversationItem:
        return self.add_item(
            ConversationItem(
                conversation_id=conversation_id,
                company_id=company_id,
                channel=ConversationChannel.NOTE,
                item_type=ConversationItemType.INTERNAL_COMMENT,
                direction="internal",
                body=body,
            )
        )

    def ai_summary(self, conversation_id: UUID) -> str:
        items = self.timeline(conversation_id)
        if not items:
            return "Insufficient conversation history."
        subjects = [item.subject for item in items if item.subject]
        channels = sorted({item.channel.value for item in items})
        latest = items[-1].body[:180] if items[-1].body else ""
        summary = (
            f"Conversation across {', '.join(channels)} with {len(items)} events. "
            f"Latest: {latest or 'n/a'}."
        )
        if subjects:
            summary = f"Subject focus: {subjects[-1]}. " + summary
        thread = self.threads.get(conversation_id)
        if thread:
            self.threads[conversation_id] = thread.model_copy(update={"ai_summary": summary})
        return summary

    def pin(self, conversation_id: UUID, *, pinned: bool = True) -> ConversationThread | None:
        thread = self.threads.get(conversation_id)
        if thread is None:
            return None
        updated = thread.model_copy(update={"pinned": pinned})
        self.threads[conversation_id] = updated
        return updated

    def mark_read(self, conversation_id: UUID) -> ConversationThread | None:
        thread = self.threads.get(conversation_id)
        if thread is None:
            return None
        updated_items = [item.model_copy(update={"unread": False}) for item in thread.items]
        updated = thread.model_copy(update={"unread_count": 0, "items": updated_items})
        self.threads[conversation_id] = updated
        self.items = [
            item.model_copy(update={"unread": False}) if item.conversation_id == conversation_id else item
            for item in self.items
        ]
        return updated
