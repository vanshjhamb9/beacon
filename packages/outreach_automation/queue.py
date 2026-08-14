"""
Outreach Queue for Beacon
Manages queued messages across all channels with rate limiting.
"""
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Optional
from uuid import uuid4

from .rate_limiter import RateLimiter


class QueueStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueueItem:
    """A single outreach message in the queue."""
    id: str = field(default_factory=lambda: str(uuid4()))
    channel: str = ""
    recipient: str = ""
    subject: str = ""
    body: str = ""
    opportunity_id: str = ""
    campaign_id: str = ""
    metadata: dict = field(default_factory=dict)
    status: QueueStatus = QueueStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    error: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "channel": self.channel,
            "recipient": self.recipient,
            "subject": self.subject,
            "body": self.body,
            "opportunity_id": self.opportunity_id,
            "campaign_id": self.campaign_id,
            "metadata": self.metadata,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "error": self.error,
            "attempts": self.attempts,
        }


class OutreachQueue:
    """Manages outreach queue with rate limiting."""

    def __init__(self, queue_file: Optional[Path] = None):
        self.rate_limiter = RateLimiter()
        self.queue: list[QueueItem] = []
        self.sent_log: list[QueueItem] = []
        self.queue_file = queue_file or Path("exports/outreach/queue.json")
        self._load_queue()

    def _load_queue(self):
        """Load queue from file if exists."""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, "r") as f:
                    data = json.load(f)
                    for item_data in data.get("queue", []):
                        item = QueueItem(
                            id=item_data["id"],
                            channel=item_data["channel"],
                            recipient=item_data["recipient"],
                            subject=item_data.get("subject", ""),
                            body=item_data.get("body", ""),
                            opportunity_id=item_data.get("opportunity_id", ""),
                            campaign_id=item_data.get("campaign_id", ""),
                            metadata=item_data.get("metadata", {}),
                            status=QueueStatus(item_data["status"]),
                            created_at=datetime.fromisoformat(item_data["created_at"]),
                            scheduled_at=datetime.fromisoformat(item_data["scheduled_at"]) if item_data.get("scheduled_at") else None,
                            sent_at=datetime.fromisoformat(item_data["sent_at"]) if item_data.get("sent_at") else None,
                            error=item_data.get("error"),
                            attempts=item_data.get("attempts", 0),
                        )
                        self.queue.append(item)
            except Exception:
                pass

    def _save_queue(self):
        """Save queue to file."""
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "queue": [item.to_dict() for item in self.queue],
            "sent_log": [item.to_dict() for item in self.sent_log[-100:]],  # Keep last 100
        }
        with open(self.queue_file, "w") as f:
            json.dump(data, f, indent=2)

    def enqueue(
        self,
        channel: str,
        recipient: str,
        body: str,
        subject: str = "",
        opportunity_id: str = "",
        campaign_id: str = "",
        metadata: Optional[dict] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> QueueItem:
        """Add a message to the queue."""
        item = QueueItem(
            channel=channel,
            recipient=recipient,
            subject=subject,
            body=body,
            opportunity_id=opportunity_id,
            campaign_id=campaign_id,
            metadata=metadata or {},
            scheduled_at=scheduled_at,
        )
        self.queue.append(item)
        self._save_queue()
        return item

    def get_next_ready(self) -> Optional[QueueItem]:
        """Get next message ready to send."""
        now = datetime.now()
        for item in self.queue:
            if item.status != QueueStatus.PENDING:
                continue
            if item.scheduled_at and item.scheduled_at > now:
                continue
            if not self.rate_limiter.can_send(item.channel):
                continue
            return item
        return None

    def mark_sending(self, item_id: str):
        """Mark item as sending."""
        for item in self.queue:
            if item.id == item_id:
                item.status = QueueStatus.SENDING
                item.attempts += 1
                self._save_queue()
                return

    def mark_sent(self, item_id: str):
        """Mark item as sent."""
        for i, item in enumerate(self.queue):
            if item.id == item_id:
                item.status = QueueStatus.SENT
                item.sent_at = datetime.now()
                self.rate_limiter.record_send(item.channel)
                self.sent_log.append(item)
                self.queue.pop(i)
                self._save_queue()
                return

    def mark_failed(self, item_id: str, error: str):
        """Mark item as failed."""
        for item in self.queue:
            if item.id == item_id:
                item.status = QueueStatus.FAILED
                item.error = error
                if item.attempts >= item.max_attempts:
                    item.status = QueueStatus.FAILED
                self._save_queue()
                return

    def cancel(self, item_id: str):
        """Cancel an item."""
        for i, item in enumerate(self.queue):
            if item.id == item_id:
                item.status = QueueStatus.CANCELLED
                self.queue.pop(i)
                self._save_queue()
                return

    def get_stats(self) -> dict:
        """Get queue statistics."""
        return {
            "pending": len([i for i in self.queue if i.status == QueueStatus.PENDING]),
            "sending": len([i for i in self.queue if i.status == QueueStatus.SENDING]),
            "sent_today": len(self.sent_log),
            "failed": len([i for i in self.queue if i.status == QueueStatus.FAILED]),
            "rate_limits": self.rate_limiter.get_stats(),
        }
