from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from communication_gateway.models.types import QueueName


@dataclass
class QueueItem:
    id: str
    queue: QueueName
    payload: dict[str, Any]
    priority: int = 100
    available_at: float = field(default_factory=time.time)
    attempts: int = 0
    max_attempts: int = 5
    last_error: str | None = None


class InMemoryQueueManager:
    """Production-shaped queue manager with named queues.

    Redis-backed persistence is wired in the API worker layer; this manager is the
    domain contract and sandbox/test backend.
    """

    def __init__(self) -> None:
        self._queues: dict[QueueName, list[QueueItem]] = {name: [] for name in QueueName}

    def enqueue(
        self,
        queue: QueueName,
        payload: dict[str, Any],
        *,
        priority: int = 100,
        delay_seconds: float = 0.0,
        max_attempts: int = 5,
    ) -> QueueItem:
        item = QueueItem(
            id=str(uuid.uuid4()),
            queue=queue,
            payload=payload,
            priority=priority,
            available_at=time.time() + delay_seconds,
            max_attempts=max_attempts,
        )
        self._queues[queue].append(item)
        self._queues[queue].sort(key=lambda row: (row.priority, row.available_at))
        return item

    def dequeue(self, queue: QueueName) -> QueueItem | None:
        now = time.time()
        for idx, item in enumerate(self._queues[queue]):
            if item.available_at <= now:
                return self._queues[queue].pop(idx)
        return None

    def retry(self, item: QueueItem, *, error: str, delay_seconds: float = 30.0) -> QueueItem:
        item.attempts += 1
        item.last_error = error
        if item.attempts >= item.max_attempts:
            item.queue = QueueName.DEAD_LETTER
            self._queues[QueueName.DEAD_LETTER].append(item)
            return item
        item.queue = QueueName.RETRY
        item.available_at = time.time() + delay_seconds
        self._queues[QueueName.RETRY].append(item)
        self._queues[QueueName.RETRY].sort(key=lambda row: (row.priority, row.available_at))
        return item

    def depth(self, queue: QueueName | None = None) -> dict[str, int]:
        if queue is not None:
            return {queue.value: len(self._queues[queue])}
        return {name.value: len(items) for name, items in self._queues.items()}

    def snapshot(self) -> str:
        return json.dumps(self.depth())
