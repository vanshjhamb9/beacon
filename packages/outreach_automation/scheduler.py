"""
Outreach Scheduler for Beacon
Schedules and manages outreach across all channels.
"""
from datetime import datetime, timedelta
from typing import Optional

from .queue import OutreachQueue, QueueItem
from .rate_limiter import RateLimiter
from .reply_tracker import ReplyTracker


class OutreachScheduler:
    """Schedules outreach messages across all channels."""

    def __init__(self):
        self.queue = OutreachQueue()
        self.rate_limiter = RateLimiter()
        self.tracker = ReplyTracker()

    def schedule_outreach(
        self,
        channel: str,
        recipient: str,
        body: str,
        subject: str = "",
        opportunity_id: str = "",
        campaign_id: str = "",
        metadata: Optional[dict] = None,
        immediate: bool = False,
    ) -> QueueItem:
        """Schedule an outreach message."""
        if immediate:
            scheduled_at = datetime.now()
        else:
            delay = self.rate_limiter.get_delay(channel)
            scheduled_at = datetime.now() + timedelta(seconds=delay)

        return self.queue.enqueue(
            channel=channel,
            recipient=recipient,
            body=body,
            subject=subject,
            opportunity_id=opportunity_id,
            campaign_id=campaign_id,
            metadata=metadata or {},
            scheduled_at=scheduled_at,
        )

    def process_queue(self):
        """Process the outreach queue."""
        processed = 0
        max_per_run = 5  # Process max 5 messages per run

        while processed < max_per_run:
            item = self.queue.get_next_ready()
            if not item:
                break

            # Mark as sending
            self.queue.mark_sending(item.id)

            # In production, this would call the appropriate sender
            # For now, we'll just mark as sent
            self.queue.mark_sent(item.id)
            processed += 1

        return processed

    def get_stats(self) -> dict:
        """Get comprehensive outreach statistics."""
        queue_stats = self.queue.get_stats()
        reply_stats = self.tracker.get_stats()
        rate_stats = self.rate_limiter.get_stats()

        return {
            "queue": queue_stats,
            "replies": reply_stats,
            "rate_limits": rate_stats,
            "timestamp": datetime.now().isoformat(),
        }

    def cancel_opportunity(self, opportunity_id: str):
        """Cancel all pending outreach for an opportunity."""
        cancelled = 0
        for item in self.queue.queue[:]:
            if item.metadata.get("opportunity_id") == opportunity_id:
                self.queue.cancel(item.id)
                cancelled += 1
        return cancelled
