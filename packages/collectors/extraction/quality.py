from __future__ import annotations

import re
from html import unescape
from typing import Any
from urllib.parse import urlparse

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_COMPANY_HINT_RE = re.compile(
    r"\b([A-Z][A-Za-z0-9&.\-]{1,40}(?:\s(?:AI|Inc|Labs|Soft|Systems|Technologies|Tech|Software))?)\b"
)
_HINT_STOPWORDS = frozenset(
    {
        "the",
        "this",
        "that",
        "with",
        "from",
        "your",
        "our",
        "new",
        "show",
        "ask",
        "why",
        "how",
        "what",
        "when",
        "discussion",
        "optimize",
        "model",
        "models",
        "weekly",
        "daily",
        "update",
        "updates",
        "launch",
        "product",
        "products",
        "github",
        "reddit",
        "hacker",
        "news",
        "indie",
        "hackers",
        "producthunt",
        "devto",
        "yagni",
        "saas",
        "api",
        "ai",
        "ml",
        "llm",
        "open",
        "source",
        "free",
        "best",
        "top",
        "guide",
        "introducing",
        "announcing",
    }
)
_SIGNAL_TERMS = (
    "hiring",
    "fundrais",
    "series ",
    "launch",
    "raised",
    "expand",
    "automation",
    "ai ",
    "support",
    "ops",
    "saas",
)


def strip_html(value: str) -> str:
    text = _TAG_RE.sub(" ", unescape(value or ""))
    return _WHITESPACE_RE.sub(" ", text).strip()


def extract_domain(url: str) -> str | None:
    try:
        host = urlparse(url).netloc.lower().removeprefix("www.")
    except ValueError:
        return None
    if not host:
        return None
    # Never treat publisher/platform hosts as a company domain (CRE Phase 7).
    try:
        from intelligence.entity_resolution.platform_domains import is_platform_domain

        if is_platform_domain(host):
            return None
    except Exception:  # noqa: BLE001
        pass
    return host


def extract_company_hints(title: str, content: str) -> list[str]:
    corpus = f"{title} {content}"
    hints: list[str] = []
    for match in _COMPANY_HINT_RE.finditer(corpus):
        candidate = match.group(1).strip(" .-")
        lowered = candidate.lower()
        if len(candidate) < 3 or lowered in _HINT_STOPWORDS:
            continue
        if candidate.isupper() and len(candidate) <= 4:
            continue
        if candidate not in hints:
            hints.append(candidate)
        if len(hints) >= 5:
            break
    return hints


def detect_signal_tags(title: str, content: str) -> list[str]:
    lowered = f"{title} {content}".lower()
    return [term.strip() for term in _SIGNAL_TERMS if term in lowered]


def enrichment_metadata(
    *,
    title: str,
    content: str,
    url: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cleaned = strip_html(content)
    metadata: dict[str, Any] = {
        "content_chars": len(cleaned),
        "domain": extract_domain(url),
        "company_hints": extract_company_hints(title, cleaned),
        "signal_tags": detect_signal_tags(title, cleaned),
        "extraction_quality": round(min(100.0, 40.0 + min(len(cleaned), 800) / 10.0), 2),
    }
    if extra:
        metadata.update(extra)
    return metadata
