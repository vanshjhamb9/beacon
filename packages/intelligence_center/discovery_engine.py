"""Discovery feed helpers — filter, serialize, headline generation."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from intelligence_center.models import DiscoveryCard, DiscoveryEventType


def make_headline(event_type: str, *, company: str | None = None, detail: str | None = None) -> str:
    company = company or ""
    detail = detail or ""
    if event_type == DiscoveryEventType.SIGNAL_COLLECTED:
        return f"Found {company}".strip() if company else "Signal collected"
    if event_type == DiscoveryEventType.DUPLICATE_REMOVED:
        return f"Removed {detail}" if detail else "Duplicate removed"
    if event_type == DiscoveryEventType.WEBSITE_VERIFIED:
        return f"Verified {detail or 'company website'}"
    if event_type == DiscoveryEventType.EMAIL_FOUND:
        return f"Recovered {detail}" if detail else "Email recovered"
    if event_type == DiscoveryEventType.DECISION_MAKER_FOUND:
        return f"Founder {detail}".strip() if detail else "Decision maker found"
    if event_type == DiscoveryEventType.REVENUE_READY:
        return f"Score {detail}" if detail else "Revenue Ready"
    if event_type == DiscoveryEventType.OUTREACH_STARTED:
        return "Outreach started"
    if event_type == DiscoveryEventType.REPLY_RECEIVED:
        return "Reply received"
    if event_type == DiscoveryEventType.MEETING_BOOKED:
        return "Meeting booked"
    if event_type == DiscoveryEventType.WON:
        return "Won"
    if event_type == DiscoveryEventType.LOST:
        return "Lost"
    return event_type


def filter_discoveries(
    cards: list[DiscoveryCard],
    *,
    collector: str | None = None,
    industry: str | None = None,
    status: str | None = None,
    connector: str | None = None,
    company: str | None = None,
    revenue_ready_only: bool = False,
    errors_only: bool = False,
) -> list[DiscoveryCard]:
    out: list[DiscoveryCard] = []
    company_q = (company or "").strip().lower()
    for card in cards:
        if collector and (card.collector or "").lower() != collector.lower():
            continue
        if industry and (card.industry or "").lower() != industry.lower():
            continue
        if status and (card.status or "").lower() != status.lower():
            continue
        if connector and (card.connector or "").lower() != connector.lower():
            continue
        if company_q and company_q not in (card.company_name or "").lower():
            continue
        if revenue_ready_only and not card.is_revenue_ready:
            continue
        if errors_only and not card.is_error:
            continue
        out.append(card)
    return out


def serialize_card(card: DiscoveryCard) -> dict[str, Any]:
    payload = asdict(card)
    ts = payload.get("timestamp")
    if isinstance(ts, datetime):
        payload["timestamp"] = ts.isoformat()
    return payload
