"""DSIP: Queue Manager.

Manages discovery queues with priority scheduling.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class QueueName(str, Enum):
    """Queue names."""
    NEW_DISCOVERY = "new_discovery"
    REVALIDATION = "revalidation"
    TECH_REFRESH = "tech_refresh"
    FRESHNESS_REFRESH = "freshness_refresh"
    EVIDENCE_REFRESH = "evidence_refresh"
    PRIORITY = "priority"
    MANUAL_REVIEW = "manual_review"
    REJECTED = "rejected"
    RETRY = "retry"


@dataclass
class QueueItem:
    """An item in a discovery queue."""
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    queue_name: str = QueueName.NEW_DISCOVERY
    priority: int = 50  # 0-100, higher = more urgent

    # References
    canonical_company_id: str | None = None
    discovered_company_id: str | None = None
    job_id: str | None = None

    # Status
    status: str = "pending"  # pending, processing, completed, failed
    attempts: int = 0
    max_attempts: int = 3

    # Timing
    queued_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Error
    last_error: str | None = None

    # Worker
    worker_id: str | None = None


class QueueManager:
    """Manages discovery queues with priority scheduling.

    Queues:
    - new_discovery: New companies to process
    - revalidation: Companies needing validation
    - tech_refresh: Technology stack refresh
    - freshness_refresh: Stale companies to re-crawl
    - evidence_refresh: Evidence to refresh
    - priority: High-priority companies
    - manual_review: Needs human review
    - rejected: Rejected companies
    - retry: Failed items to retry

    Usage:
        manager = QueueManager()
        manager.enqueue(company_id, QueueName.NEW_DISCOVERY, priority=80)
        item = manager.dequeue(QueueName.NEW_DISCOVERY, worker_id="worker-1")
        manager.complete(item.item_id)
    """

    def __init__(self):
        self._queues: dict[str, list[QueueItem]] = {
            q.value: [] for q in QueueName
        }
        self._items: dict[str, QueueItem] = {}  # item_id -> QueueItem
        self._processing: dict[str, QueueItem] = {}  # worker_id -> QueueItem

    def enqueue(
        self,
        queue_name: str | QueueName,
        priority: int = 50,
        canonical_company_id: str = None,
        discovered_company_id: str = None,
        job_id: str = None,
    ) -> QueueItem:
        """Add an item to a queue."""
        if isinstance(queue_name, QueueName):
            queue_name = queue_name.value

        item = QueueItem(
            queue_name=queue_name,
            priority=priority,
            canonical_company_id=canonical_company_id,
            discovered_company_id=discovered_company_id,
            job_id=job_id,
        )

        self._queues.setdefault(queue_name, []).append(item)
        self._items[item.item_id] = item

        # Sort queue by priority (descending)
        self._queues[queue_name].sort(key=lambda x: x.priority, reverse=True)

        logger.debug(f"Enqueued {item.item_id} to {queue_name} (priority={priority})")
        return item

    def dequeue(
        self,
        queue_name: str | QueueName,
        worker_id: str = None,
    ) -> QueueItem | None:
        """Get the highest priority item from a queue."""
        if isinstance(queue_name, QueueName):
            queue_name = queue_name.value

        queue = self._queues.get(queue_name, [])

        for item in queue:
            if item.status == "pending" and item.attempts < item.max_attempts:
                item.status = "processing"
                item.started_at = datetime.utcnow()
                item.worker_id = worker_id

                if worker_id:
                    self._processing[worker_id] = item

                logger.debug(f"Dequeued {item.item_id} from {queue_name}")
                return item

        return None

    def complete(self, item_id: str) -> None:
        """Mark an item as completed."""
        item = self._items.get(item_id)
        if item:
            item.status = "completed"
            item.completed_at = datetime.utcnow()
            if item.worker_id:
                self._processing.pop(item.worker_id, None)
            logger.debug(f"Completed {item_id}")

    def fail(self, item_id: str, error: str = None) -> None:
        """Mark an item as failed."""
        item = self._items.get(item_id)
        if item:
            item.attempts += 1
            item.last_error = error

            if item.attempts >= item.max_attempts:
                item.status = "failed"
                logger.warning(f"Failed permanently {item_id}: {error}")
            else:
                item.status = "pending"  # Will be retried
                logger.debug(f"Failed {item_id} (attempt {item.attempts}): {error}")

            if item.worker_id:
                self._processing.pop(item.worker_id, None)

    def get_queue_size(self, queue_name: str | QueueName) -> int:
        """Get the size of a queue."""
        if isinstance(queue_name, QueueName):
            queue_name = queue_name.value
        return len([i for i in self._queues.get(queue_name, []) if i.status == "pending"])

    def get_queue_stats(self) -> dict:
        """Get statistics for all queues."""
        stats = {}
        for queue_name, items in self._queues.items():
            pending = len([i for i in items if i.status == "pending"])
            processing = len([i for i in items if i.status == "processing"])
            completed = len([i for i in items if i.status == "completed"])
            failed = len([i for i in items if i.status == "failed"])

            stats[queue_name] = {
                "total": len(items),
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
            }

        return stats

    def get_priority_items(
        self,
        queue_name: str | QueueName,
        limit: int = 10,
    ) -> list[QueueItem]:
        """Get top priority items from a queue."""
        if isinstance(queue_name, QueueName):
            queue_name = queue_name.value

        queue = self._queues.get(queue_name, [])
        pending = [i for i in queue if i.status == "pending"]
        pending.sort(key=lambda x: x.priority, reverse=True)
        return pending[:limit]

    def move_to_queue(
        self,
        item_id: str,
        target_queue: str | QueueName,
    ) -> bool:
        """Move an item to a different queue."""
        item = self._items.get(item_id)
        if not item:
            return False

        if isinstance(target_queue, QueueName):
            target_queue = target_queue.value

        # Remove from current queue
        if item.queue_name in self._queues:
            self._queues[item.queue_name] = [
                i for i in self._queues[item.queue_name] if i.item_id != item_id
            ]

        # Add to new queue
        item.queue_name = target_queue
        item.status = "pending"
        self._queues.setdefault(target_queue, []).append(item)
        self._queues[target_queue].sort(key=lambda x: x.priority, reverse=True)

        return True

    def cleanup_old_items(self, max_age_hours: int = 168) -> int:
        """Clean up old completed/failed items."""
        now = datetime.utcnow()
        removed = 0

        for queue_name in self._queues:
            queue = self._queues[queue_name]
            to_remove = []

            for item in queue:
                if item.status in ["completed", "failed"]:
                    age = (now - (item.completed_at or item.queued_at)).total_seconds() / 3600
                    if age > max_age_hours:
                        to_remove.append(item)

            for item in to_remove:
                queue.remove(item)
                self._items.pop(item.item_id, None)
                removed += 1

        return removed
