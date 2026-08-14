"""Queue Engine — manages opportunity queues for founder review.

Priority-based queue system for opportunities awaiting review.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class QueueItem:
    """Single item in the review queue."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.company_name: str = data.get("company_name", "unknown")
        self.priority: int = data.get("priority", 0)
        self.quality_score: int = data.get("quality_score", 0)
        self.signal_type: str = data.get("signal_type", "unknown")
        self.connector: str = data.get("connector", "unknown")
        self.created_at: datetime = data.get("created_at", datetime.now(timezone.utc))
        self.added_to_queue: datetime = data.get("added_to_queue", datetime.now(timezone.utc))
        self.status: str = data.get("status", "pending")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "company_name": self.company_name,
            "priority": self.priority,
            "quality_score": self.quality_score,
            "signal_type": self.signal_type,
            "connector": self.connector,
            "created_at": self.created_at.isoformat(),
            "added_to_queue": self.added_to_queue.isoformat(),
            "status": self.status,
        }


class QueueEngine:
    """Opportunity queue management engine."""

    def __init__(self):
        self._queues: dict[str, list[QueueItem]] = {
            "default": [],
            "high_priority": [],
            "low_priority": [],
        }
        self._processed: list[dict[str, Any]] = []

    def enqueue(
        self,
        opportunity_id: str,
        company_name: str,
        quality_score: int,
        signal_type: str,
        connector: str,
        priority: int = 0,
        queue: str = "default",
    ) -> QueueItem:
        """Add opportunity to queue."""
        item = QueueItem({
            "opportunity_id": opportunity_id,
            "company_name": company_name,
            "priority": priority,
            "quality_score": quality_score,
            "signal_type": signal_type,
            "connector": connector,
        })

        if queue not in self._queues:
            self._queues[queue] = []

        self._queues[queue].append(item)

        # Sort by priority (higher = more important)
        self._queues[queue].sort(key=lambda x: x.priority, reverse=True)

        return item

    def dequeue(self, queue: str = "default") -> QueueItem | None:
        """Remove and return next item from queue."""
        if queue not in self._queues or not self._queues[queue]:
            return None

        item = self._queues[queue].pop(0)
        item.status = "processing"
        return item

    def peek(self, queue: str = "default", count: int = 1) -> list[QueueItem]:
        """Preview next items without removing."""
        if queue not in self._queues:
            return []

        return self._queues[queue][:count]

    def get_queue(self, queue: str = "default") -> list[QueueItem]:
        """Get all items in queue."""
        return self._queues.get(queue, [])

    def get_queue_size(self, queue: str = "default") -> int:
        """Get queue size."""
        return len(self._queues.get(queue, []))

    def process_item(self, item: QueueItem, result: str):
        """Mark item as processed."""
        item.status = "completed"
        self._processed.append({
            "item": item.to_dict(),
            "result": result,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        })

    def get_processed(self) -> list[dict[str, Any]]:
        """Get all processed items."""
        return list(self._processed)

    def get_statistics(self) -> dict[str, Any]:
        """Get queue statistics."""
        queue_sizes = {q: len(items) for q, items in self._queues.items()}
        total = sum(queue_sizes.values())
        total_processed = len(self._processed)

        return {
            "total_in_queues": total,
            "queue_sizes": queue_sizes,
            "total_processed": total_processed,
        }
