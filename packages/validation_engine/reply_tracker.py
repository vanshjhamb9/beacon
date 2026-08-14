"""Reply tracker — records all reply events for companies.

Append-only. Never overwrites. Every reply has evidence.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from validation_engine import REPLY_TYPES
from validation_engine.models import ReplyEvent


class ReplyTracker:
    """Tracks reply events (positive, negative, bounce, etc.) for companies."""

    def __init__(self) -> None:
        self._replies: dict[str, list[ReplyEvent]] = {}
        self._all_replies: list[ReplyEvent] = []

    def record_reply(
        self,
        company_id: str,
        reply_type: str,
        *,
        evidence: dict[str, Any] | None = None,
        source: str = "",
        confidence: float = 1.0,
        reply_time_seconds: float | None = None,
    ) -> ReplyEvent:
        if reply_type not in REPLY_TYPES:
            raise ValueError(f"Invalid reply type: {reply_type}. Must be one of {REPLY_TYPES}")

        event = ReplyEvent(
            company_id=company_id,
            reply_type=reply_type,
            timestamp=datetime.now(UTC),
            evidence=evidence or {},
            source=source,
            confidence=confidence,
            reply_time_seconds=reply_time_seconds,
        )
        self._replies.setdefault(company_id, []).append(event)
        self._all_replies.append(event)
        return event

    def get_replies_for_company(self, company_id: str) -> list[ReplyEvent]:
        return list(self._replies.get(company_id, []))

    def get_all_replies(self) -> list[ReplyEvent]:
        return list(self._all_replies)

    def get_positive_replies(self) -> list[ReplyEvent]:
        return [r for r in self._all_replies if r.reply_type == "positive"]

    def get_negative_replies(self) -> list[ReplyEvent]:
        return [r for r in self._all_replies if r.reply_type == "negative"]

    def get_bounces(self) -> list[ReplyEvent]:
        return [r for r in self._all_replies if r.reply_type == "bounce"]

    def get_auto_replies(self) -> list[ReplyEvent]:
        return [r for r in self._all_replies if r.reply_type == "auto_reply"]

    def get_no_response(self) -> list[ReplyEvent]:
        return [r for r in self._all_replies if r.reply_type == "no_response"]

    def get_reply_rate(self) -> float:
        if not self._all_replies:
            return 0.0
        responded = len([r for r in self._all_replies if r.reply_type != "no_response"])
        return (responded / len(self._all_replies)) * 100.0

    def get_positive_reply_rate(self) -> float:
        if not self._all_replies:
            return 0.0
        positive = len(self.get_positive_replies())
        return (positive / len(self._all_replies)) * 100.0

    def get_avg_reply_time(self) -> float | None:
        times = [
            r.reply_time_seconds
            for r in self._all_replies
            if r.reply_time_seconds is not None
        ]
        if not times:
            return None
        return sum(times) / len(times)

    def get_reply_type_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for reply in self._all_replies:
            counts[reply.reply_type] = counts.get(reply.reply_type, 0) + 1
        return counts

    def get_replies_by_connector(self, connector: str) -> list[ReplyEvent]:
        return [r for r in self._all_replies if r.source == connector]
