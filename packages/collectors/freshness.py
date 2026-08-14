"""Lead freshness gate — only recent event signals qualify as outbound leads."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

# Hard SLA for actionable outreach leads
FRESH_HOURS = 48

# Static directories / firmographics — never open a lead by themselves
DIRECTORY_SOURCES = frozenset(
    {
        "yc",
        "app_store",
        "google_play",
        "crunchbase",
        "apollo",
        "clearbit",
        "pdl",
    }
)

# Publishers / platforms — never treat as the prospect company
NEWS_OR_PLATFORM_HOSTS = frozenset(
    {
        "cnbc.com",
        "theconversation.com",
        "techcrunch.com",
        "theverge.com",
        "wired.com",
        "bloomberg.com",
        "reuters.com",
        "nytimes.com",
        "wsj.com",
        "forbes.com",
        "medium.com",
        "substack.com",
        "youtube.com",
        "twitter.com",
        "x.com",
        "linkedin.com",
        "facebook.com",
        "reddit.com",
        "news.ycombinator.com",
        "github.com",
        "gist.github.com",
        "github.io",
        "producthunt.com",
        "wikipedia.org",
        "google.com",
        "apple.com",
        "jfrog.com",
        "microsoft.com",
        "amazon.com",
        "nvidia.com",
        "openai.com",
        "anthropic.com",
        "meta.com",
        "w3.org",
        "grapheneos.org",
        "ietf.org",
        "wikipedia.org",
    }
)

# Event sources that can carry a real content timestamp
EVENT_SOURCES = frozenset(
    {
        "product_hunt",
        "reddit",
        "hacker_news",
        "github_trending",
        "rss",
        "sec_edgar",
        "indie_hackers",
        "devto",
        "techcrunch",
        "the_verge",
        "venturebeat",
        "saastr",
    }
)

STALE_WHY_NOW_MARKERS = (
    "yc portfolio",
    "yc company directory",
    "expansion / growth context",
    "app store product listing",
    "google play listing",
)


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    text = str(value).strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except ValueError:
        return None


def content_occurred_at(
    *,
    published_at: Any = None,
    metadata: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> datetime | None:
    meta = metadata or {}
    row = payload or {}
    for candidate in (
        published_at,
        row.get("published_at"),
        row.get("content_occurred_at"),
        row.get("launch_date"),
        row.get("created_at"),
        meta.get("content_occurred_at"),
        meta.get("launch_date"),
        meta.get("created_at"),
        meta.get("posted_at"),
        meta.get("currentVersionReleaseDate"),
        meta.get("releaseDate"),
    ):
        dt = parse_datetime(candidate)
        if dt is not None:
            return dt
    return None


def age_hours(occurred_at: datetime, *, now: datetime | None = None) -> float:
    current = now or datetime.now(UTC)
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=UTC)
    return max(0.0, (current - occurred_at.astimezone(UTC)).total_seconds() / 3600.0)


def source_kind(source: str, metadata: dict[str, Any] | None = None) -> str:
    meta = metadata or {}
    explicit = str(meta.get("source_kind") or "").strip().lower()
    if explicit in {"event", "directory", "enrichment"}:
        return explicit
    src = str(source or "").strip().lower()
    if src in DIRECTORY_SOURCES:
        return "directory"
    if meta.get("lead_eligible") is False:
        return "enrichment"
    if src in EVENT_SOURCES:
        return "event"
    return "event" if src else "enrichment"


def is_directory_source(source: str, metadata: dict[str, Any] | None = None) -> bool:
    return source_kind(source, metadata) == "directory"


def why_now_is_stale(why_now: str | None) -> bool:
    text = str(why_now or "").lower()
    return any(marker in text for marker in STALE_WHY_NOW_MARKERS)


def passes_freshness_gate(
    *,
    source: str,
    published_at: Any = None,
    metadata: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    max_age_hours: float = FRESH_HOURS,
    now: datetime | None = None,
    allow_directory: bool = False,
) -> tuple[bool, str, float | None]:
    """Return (ok, reason, age_hours)."""
    meta = dict(metadata or {})
    if payload:
        meta = {**dict(payload.get("metadata") or {}), **meta}
    kind = source_kind(source, meta)
    if kind == "directory" and not allow_directory:
        return False, "directory_source_not_lead", None
    if meta.get("lead_eligible") is False and not allow_directory:
        return False, "not_lead_eligible", None

    occurred = content_occurred_at(published_at=published_at, metadata=meta, payload=payload)
    if occurred is None:
        return False, "missing_content_timestamp", None

    hours = age_hours(occurred, now=now)
    if hours > max_age_hours:
        return False, "stale_signal", hours
    return True, "fresh", hours


def filter_fresh_events(events: list[Any], *, max_age_hours: float = FRESH_HOURS) -> list[Any]:
    """Filter NormalizedEvent-like objects (attrs: source, published_at, metadata)."""
    kept: list[Any] = []
    now = datetime.now(UTC)
    for event in events:
        ok, _reason, _age = passes_freshness_gate(
            source=getattr(event, "source", "") or "",
            published_at=getattr(event, "published_at", None),
            metadata=getattr(event, "metadata", None) or {},
            max_age_hours=max_age_hours,
            now=now,
        )
        if ok:
            kept.append(event)
    return kept


def cutoff_datetime(*, max_age_hours: float = FRESH_HOURS, now: datetime | None = None) -> datetime:
    current = now or datetime.now(UTC)
    return current - timedelta(hours=max_age_hours)
