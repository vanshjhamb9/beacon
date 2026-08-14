"""Publisher / platform hosts that must not become company identities."""

from __future__ import annotations

PLATFORM_DOMAINS: frozenset[str] = frozenset(
    {
        "reddit.com",
        "old.reddit.com",
        "github.com",
        "gist.github.com",
        "news.ycombinator.com",
        "hnrss.org",
        "ycombinator.com",
        "producthunt.com",
        "www.producthunt.com",
        "techcrunch.com",
        "theverge.com",
        "venturebeat.com",
        "saastr.com",
        "feeds.feedburner.com",
        "dev.to",
        "indiehackers.com",
        "www.indiehackers.com",
        "sec.gov",
        "www.sec.gov",
        "arxiv.org",
        "medium.com",
        "substack.com",
        "youtube.com",
        "youtu.be",
        "twitter.com",
        "x.com",
        "linkedin.com",
        "facebook.com",
        "instagram.com",
        "wikipedia.org",
        "en.wikipedia.org",
        "google.com",
        "googleapis.com",
        "apple.com",
        "microsoft.com",
        "amazon.com",
        "cloudflare.com",
        "stackoverflow.com",
        "stackexchange.com",
        "data.stackexchange.com",
        "npmjs.com",
        "pypi.org",
        "crates.io",
        "docker.com",
        "hub.docker.com",
    }
)

PLATFORM_LABELS: frozenset[str] = frozenset(
    {
        "reddit",
        "github",
        "hacker news",
        "product hunt",
        "producthunt",
        "techcrunch",
        "theverge",
        "the verge",
        "indie hackers",
        "sec",
        "edgar",
        "devto",
        "dev to",
        "arxiv",
        "youtube",
        "twitter",
        "linkedin",
        "wikipedia",
        "medium",
        "substack",
        "this",
        "that",
        "discussion",
        "optimize",
        "model",
        "yagni",
        "show hn",
        "ask hn",
    }
)


def is_platform_domain(domain: str | None) -> bool:
    if not domain:
        return False
    host = domain.lower().removeprefix("www.")
    if host in PLATFORM_DOMAINS:
        return True
    return any(host.endswith(f".{item}") for item in PLATFORM_DOMAINS)


def is_platform_label(name: str | None) -> bool:
    if not name:
        return False
    return name.strip().lower() in PLATFORM_LABELS
