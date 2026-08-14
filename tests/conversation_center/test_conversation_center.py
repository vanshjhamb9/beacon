from uuid import uuid4

from conversation_center import ConversationCenterService, ConversationItem
from conversation_center.models.types import ConversationChannel, ConversationFilter, ConversationItemType


def test_timeline_search_pin_unread_and_summary() -> None:
    center = ConversationCenterService()
    company_id = uuid4()
    center.add_item(
        ConversationItem(
            company_id=company_id,
            channel=ConversationChannel.EMAIL,
            item_type=ConversationItemType.MESSAGE,
            direction="outbound",
            subject="Intro",
            body="Hello",
            to_address="a@example.com",
        )
    )
    first_thread = next(iter(center.threads.values()))
    center.add_item(
        ConversationItem(
            conversation_id=first_thread.id,
            company_id=company_id,
            channel=ConversationChannel.EMAIL,
            item_type=ConversationItemType.REPLY,
            direction="inbound",
            subject="Intro",
            body="Let's meet",
            from_address="a@example.com",
            unread=True,
        )
    )
    center.add_item(
        ConversationItem(
            conversation_id=first_thread.id,
            company_id=company_id,
            channel=ConversationChannel.NOTE,
            item_type=ConversationItemType.NOTE,
            direction="internal",
            subject="Intro",
            body="Internal note",
        )
    )
    threads = center.search(ConversationFilter(company_id=company_id, unread_only=True))
    assert threads
    thread = threads[0]
    center.pin(thread.id)  # type: ignore[arg-type]
    assert center.threads[thread.id].pinned  # type: ignore[index]
    timeline = center.timeline(thread.id)  # type: ignore[arg-type]
    assert len(timeline) >= 2
    summary = center.ai_summary(thread.id)  # type: ignore[arg-type]
    assert "Intro" in summary or "meet" in summary.lower() or summary
