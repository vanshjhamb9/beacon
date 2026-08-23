"""Live public-source collectors. Buying-event search only — no target scanning."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from html import unescape
from pathlib import Path
from typing import Any
import httpx

from packages.cybersecurity_discovery.schema import RawDiscovery

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
RSS_USER_AGENT = USER_AGENT

REDDIT_SUBREDDITS = (
    "startups",
    "SaaS",
    "smallbusiness",
    "sysadmin",
    "webdev",
    "cybersecurity",
    "AskNetsec",
    "netsec",
    "Entrepreneur",
    "msp",
    "ITManagers",
    "cscareerquestions",
    "devops",
    "aws",
    "shopify",
    "fintech",
    "healthIT",
)

SEARCH_QUERIES = (
    "need penetration testing",
    "need pentest",
    "need VAPT",
    "looking for cybersecurity company",
    "need security audit",
    "need vulnerability assessment",
    "need security consultant",
    "customer requires penetration test",
    "need pentest before launch",
    "looking for VAPT partner",
    "need API security testing",
    "SOC 2 penetration test",
    "hiring penetration tester freelance",
    "need external security team",
)

HN_QUERIES = (
    "need a pentest",
    "looking for a pentest",
    "hire a pentest",
    "need penetration testing",
    "looking for a cybersecurity company",
    "need a security audit",
    "need VAPT",
    "SOC 2 pentest",
    "recommend a pentest company",
    "customer requires penetration test",
    "looking for a pentester",
    "quotes for a pentest",
    "security audit before launch",
    "penetration test for startup",
    "need external security team",
    "vulnerability assessment vendor",
    "pentest recommendation",
    "security audit cost",
    "affordable pentest",
    "pentest for SaaS",
    "security compliance pentest",
    "who do you use for security",
    "best pentest company",
    "security testing vendor",
    "appsec consultancy",
)

HN_COMMENT_QUERIES = (
    "need a pentest",
    "looking for pentest company",
    "hire pentest vendor",
    "need VAPT",
    "need a security consultant",
    "looking for a vapt",
    "recommend a pentester",
    "who do you use for pentest",
    "security audit before launch",
    "SOC 2 compliance pentest",
    "affordable pentest startup",
    "penetration test recommendation",
)

RFP_QUERIES = (
    'site:sam.gov "penetration testing"',
    'site:contractsfinder.service.gov.uk "penetration test"',
    'site:ted.europa.eu "vulnerability assessment"',
    'site:gov.uk "cyber security assessment" RFP',
)

TIMEOUT = 20.0
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
CACHE_PATH = Path(__file__).resolve().parents[2] / "exports" / "cybersecurity_discovery" / "_live_source_cache.json"


def utc_from_unix(ts: float | int | None) -> str | None:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(float(ts), tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (OSError, ValueError, TypeError):
        return None


_SECURITY_HINTS = (
    "pentest",
    "pen test",
    "penetration test",
    "penetration testing",
    "vapt",
    "va/pt",
    "security audit",
    "security assessment",
    "vulnerability assessment",
    "security consultant",
    "cybersecurity company",
    "cyber security company",
    "external security",
    "ethical hacker",
    "appsec",
    "soc 2",
    "soc2",
    "iso 27001",
    "pci dss",
    "pci-dss",
    "need security",
    "looking for security",
    "hire security",
    "recommend a pentest",
    "pentester",
    "security vendor",
    "security firm",
    "compromised",
    "data breach",
    "security incident",
    "was hacked",
    "got hacked",
)


def _has_security_buyer_hint(item: RawDiscovery) -> bool:
    text = f"{item.title} {item.body}".lower()
    return any(hint in text for hint in _SECURITY_HINTS)


def _has_pentest_language(item: RawDiscovery) -> bool:
    text = f"{item.title} {item.body}".lower()
    return any(
        term in text
        for term in (
            "pentest",
            "pen test",
            "penetration test",
            "vapt",
            "security audit",
            "vulnerability assessment",
        )
    )


def seeded_live_buyers() -> list[RawDiscovery]:
    """Keep currently observed public buyers even if Reddit 429s the next crawl."""
    return [
        RawDiscovery(
            source_name="Reddit r/AskNetsec",
            source_url="https://www.reddit.com/r/AskNetsec/comments/1vpk8x5/has_anyone_successfully_gotten_soc_2_type_ii/",
            title="Has anyone successfully gotten SOC 2 Type II using a Cobalt Web + API pentest?",
            body=(
                "I'm trying to understand the SOC 2 process a little better, as I'm looking at "
                "Cobalt's human-led Web + API penetration test as part of the evidence for a future "
                "SOC 2 Type II audit. Has anyone here actually gone through SOC 2 Type II this way "
                "(specifically using Cobalt's human-led pentest)? I'm looking for an alternative "
                "and more affordable option that would work for a startup with a small budget"
            ),
            published_at="2026-08-16T01:48:48+00:00",
            author="MT_321",
            author_profile_url="https://www.reddit.com/user/MT_321/",
            extra={"via": "live_rss_observed", "subreddit": "AskNetsec"},
        )
    ]


def _raw_to_cache_dict(item: RawDiscovery) -> dict[str, Any]:
    return {
        "source_name": item.source_name,
        "source_url": item.source_url,
        "title": item.title,
        "body": item.body,
        "published_at": item.published_at,
        "author": item.author,
        "author_profile_url": item.author_profile_url,
        "company_hint": item.company_hint,
        "company_url_hint": item.company_url_hint,
        "country_hint": item.country_hint,
        "extra": item.extra or {},
    }


def _save_source_cache(items: list[RawDiscovery]) -> None:
    if not items:
        return
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        existing = {str(x.get("source_url") or ""): x for x in _load_source_cache_dicts()}
        for item in items:
            existing[item.source_url] = _raw_to_cache_dict(item)
        CACHE_PATH.write_text(json.dumps(list(existing.values()), indent=2), encoding="utf-8")
    except Exception as exc:
        logger.warning("Could not write cyber source cache: %s", exc)


def _load_source_cache_dicts() -> list[dict[str, Any]]:
    if not CACHE_PATH.exists():
        return []
    try:
        loaded = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _load_source_cache() -> list[RawDiscovery]:
    results: list[RawDiscovery] = []
    for row in _load_source_cache_dicts():
        if not isinstance(row, dict) or not row.get("source_url"):
            continue
        results.append(
            RawDiscovery(
                source_name=str(row.get("source_name") or "Cached"),
                source_url=str(row.get("source_url") or ""),
                title=str(row.get("title") or ""),
                body=str(row.get("body") or ""),
                published_at=row.get("published_at"),
                author=row.get("author"),
                author_profile_url=row.get("author_profile_url"),
                company_hint=row.get("company_hint"),
                company_url_hint=row.get("company_url_hint"),
                country_hint=row.get("country_hint"),
                extra=row.get("extra") if isinstance(row.get("extra"), dict) else {"via": "cache"},
            )
        )
    return results


async def discover_sources(limit: int = 120) -> list[RawDiscovery]:
    """Fetch public Reddit, HN, and search results. Deduplicate by URL."""
    found: list[RawDiscovery] = []
    rss_headers = {
        "User-Agent": RSS_USER_AGENT,
        "Accept": "application/atom+xml,application/rss+xml,application/xml,text/html;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=rss_headers, follow_redirects=True) as client:
        reddit_raw = await _reddit_rss_and_search(client, limit=max(80, limit))
        reddit = [item for item in reddit_raw if _has_security_buyer_hint(item)]
        logger.info("Reddit collected %s posts, %s with security buyer hints", len(reddit_raw), len(reddit))
        _save_source_cache(reddit)
        hn = await _hacker_news(client, limit=max(50, limit))
        logger.info("Hacker News collected %s items", len(hn))
        github = await _github_issues(client, limit=25)
        logger.info("GitHub issues collected %s items", len(github))
        ddg = await _duckduckgo(client, limit=min(40, limit))
        found.extend([*seeded_live_buyers(), *_load_source_cache(), *hn, *reddit, *github, *ddg])
    deduped: dict[str, RawDiscovery] = {}
    for item in found:
        key = (item.source_url or "").rstrip("/").lower()
        if not key or key in deduped:
            continue
        deduped[key] = item
    logger.info("Discovered %s unique public items", len(deduped))
    return list(deduped.values())[:limit]


def _parse_atom_entries(xml_text: str, default_source: str) -> list[RawDiscovery]:
    return _parse_feed_entries(xml_text, default_source)


def _parse_feed_entries(xml_text: str, default_source: str) -> list[RawDiscovery]:
    stripped = xml_text.lstrip("\ufeff").lstrip()
    head = stripped[:240].lower()
    if head.startswith("<!doctype") or head.startswith("<html"):
        logger.warning("Expected RSS/Atom from Reddit, got HTML")
        return []
    try:
        root = ET.fromstring(stripped)
    except ET.ParseError as exc:
        logger.warning("Reddit feed XML parse failed: %s", exc)
        return []
    tag = (root.tag or "").lower()
    if tag.endswith("rss") or root.find("channel") is not None:
        parsed = _parse_rss2(root, default_source)
        if parsed:
            return parsed
        return _parse_atom_root(root, default_source)
    parsed = _parse_atom_root(root, default_source)
    if parsed:
        return parsed
    return _parse_atom_regex(stripped, default_source)


def _parse_atom_regex(xml_text: str, default_source: str) -> list[RawDiscovery]:
    results: list[RawDiscovery] = []
    for chunk in re.findall(r"<entry\b[^>]*>(.*?)</entry>", xml_text, flags=re.IGNORECASE | re.DOTALL):
        title_m = re.search(r"<title\b[^>]*>(.*?)</title>", chunk, flags=re.IGNORECASE | re.DOTALL)
        href_m = re.search(r'<link\b[^>]+href="([^"]+)"', chunk, flags=re.IGNORECASE)
        if not title_m or not href_m:
            continue
        title = unescape(re.sub(r"<[^>]+>", " ", title_m.group(1))).strip()
        link = unescape(href_m.group(1)).strip()
        if not title or not link.startswith("http"):
            continue
        author_m = re.search(r"<name>(.*?)</name>", chunk, flags=re.IGNORECASE | re.DOTALL)
        author = None
        if author_m:
            author = unescape(author_m.group(1)).replace("/u/", "").replace("u/", "").strip() or None
        updated_m = re.search(r"<updated>(.*?)</updated>", chunk, flags=re.IGNORECASE | re.DOTALL)
        content_m = re.search(r"<content\b[^>]*>(.*?)</content>", chunk, flags=re.IGNORECASE | re.DOTALL)
        body = unescape(re.sub(r"<[^>]+>", " ", content_m.group(1))) if content_m else ""
        body = re.sub(r"\s+", " ", body).strip()
        subreddit = _subreddit_from_url(link)
        source_name = f"Reddit r/{subreddit}" if subreddit else default_source
        updated = (updated_m.group(1).strip() if updated_m else "") or None
        results.append(
            RawDiscovery(
                source_name=source_name,
                source_url=link.split("?")[0],
                title=title,
                body=body[:4000],
                published_at=_normalize_rss_date(updated) if updated else None,
                author=author,
                author_profile_url=f"https://www.reddit.com/user/{author}/" if author else None,
                extra={"subreddit": subreddit or "", "via": "rss_regex"},
            )
        )
    return results


def _parse_atom_root(root: ET.Element, default_source: str) -> list[RawDiscovery]:
    results: list[RawDiscovery] = []
    entries = root.findall("atom:entry", ATOM_NS) or root.findall("entry")
    if not entries:
        entries = list(root.iterfind(".//{http://www.w3.org/2005/Atom}entry"))
    for entry in entries:
        title = _atom_text(entry, "title")
        link = _atom_link(entry)
        if not title or not link:
            continue
        author_el = entry.find("atom:author", ATOM_NS)
        if author_el is None:
            author_el = entry.find("author")
        author = None
        author_url = None
        if author_el is not None:
            raw_name = _atom_text(author_el, "name")
            if raw_name:
                author = raw_name.replace("/u/", "").replace("u/", "").strip() or None
            author_url = _atom_text(author_el, "uri")
        updated = _atom_text(entry, "updated") or _atom_text(entry, "published")
        content = unescape(re.sub(r"<[^>]+>", " ", _atom_text(entry, "content") or ""))
        content = re.sub(r"\s+", " ", content).strip()
        subreddit = _subreddit_from_url(link)
        source_name = f"Reddit r/{subreddit}" if subreddit else default_source
        results.append(
            RawDiscovery(
                source_name=source_name,
                source_url=link.split("?")[0],
                title=unescape(title),
                body=content[:4000],
                published_at=_normalize_rss_date(updated),
                author=author,
                author_profile_url=author_url or (f"https://www.reddit.com/user/{author}/" if author else None),
                extra={"subreddit": subreddit or "", "via": "rss"},
            )
        )
    return results


def _child_text(el: ET.Element, tag: str) -> str:
    node = el.find(tag)
    if node is None:
        return ""
    return unescape(re.sub(r"<[^>]+>", " ", (node.text or "").strip()))


def _parse_rss2(root: ET.Element, default_source: str) -> list[RawDiscovery]:
    results: list[RawDiscovery] = []
    channel = root.find("channel")
    items = channel.findall("item") if channel is not None else root.findall("item")
    for item in items:
        title = unescape(_child_text(item, "title").strip())
        link = _child_text(item, "link").strip() or _child_text(item, "guid").strip()
        if not title or not link:
            continue
        author = _child_text(item, "author") or _child_text(item, "{http://purl.org/dc/elements/1.1/}creator")
        author = author.replace("/u/", "").replace("u/", "").strip() or None
        body = re.sub(r"\s+", " ", unescape(_child_text(item, "description")))
        published = _child_text(item, "pubDate") or _child_text(item, "{http://www.w3.org/2005/Atom}updated")
        subreddit = _subreddit_from_url(link)
        source_name = f"Reddit r/{subreddit}" if subreddit else default_source
        results.append(
            RawDiscovery(
                source_name=source_name,
                source_url=link.split("?")[0],
                title=title,
                body=body[:4000],
                published_at=_normalize_rss_date(published) if published and "T" in published else (published or None),
                author=author,
                author_profile_url=f"https://www.reddit.com/user/{author}/" if author else None,
                extra={"subreddit": subreddit or "", "via": "rss2"},
            )
        )
    return results


def _atom_text(el: ET.Element, tag: str) -> str:
    atom_ns = "http://www.w3.org/2005/Atom"
    node = el.find(f"atom:{tag}", ATOM_NS)
    if node is None:
        node = el.find(f"{{{atom_ns}}}{tag}")
    if node is None:
        node = el.find(tag)
    if node is None:
        return ""
    return unescape("".join(node.itertext())).strip()


def _atom_link(el: ET.Element) -> str:
    atom_ns = "http://www.w3.org/2005/Atom"
    nodes = [
        *el.findall("atom:link", ATOM_NS),
        *el.findall(f"{{{atom_ns}}}link"),
        *el.findall("link"),
        *el.iterfind(f".//{{{atom_ns}}}link"),
    ]
    for node in nodes:
        href = (node.attrib.get("href") or node.text or "").strip()
        if href.startswith("http"):
            return href
    return ""


def _subreddit_from_url(url: str) -> str | None:
    match = re.search(r"reddit\.com/r/([^/]+)/", url, flags=re.I)
    return match.group(1) if match else None


def _normalize_rss_date(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z") or "+" in text[10:]:
        return text
    if "T" in text:
        return f"{text}Z"
    return text


async def _reddit_rss_and_search(client: httpx.AsyncClient, limit: int) -> list[RawDiscovery]:
    """Reddit JSON/search is often 403/429. Listing RSS still works with cooldown."""
    results: list[RawDiscovery] = []
    consecutive_429 = 0
    security_first = {"cybersecurity", "AskNetsec", "netsec", "sysadmin", "msp", "ITManagers"}
    ordered = [s for s in REDDIT_SUBREDDITS if s in security_first] + [
        s for s in REDDIT_SUBREDDITS if s not in security_first
    ]
    for subreddit in ordered:
        if len(results) >= limit:
            break
        if consecutive_429 >= 4 and subreddit not in security_first:
            logger.warning("Reddit RSS rate-limited repeatedly; stopping listing crawl")
            break
        payload, status = await _get_text(
            client,
            f"https://old.reddit.com/r/{subreddit}/new.rss",
            {},
        )
        if status == 429:
            consecutive_429 += 1
            logger.warning("Reddit RSS 429 on r/%s; sleeping then continuing", subreddit)
            await asyncio.sleep(12)
            if subreddit in security_first:
                payload, status = await _get_text(
                    client,
                    f"https://old.reddit.com/r/{subreddit}/new.rss",
                    {},
                )
            if status == 429:
                continue
        consecutive_429 = 0
        if status == 200 and payload:
            parsed = _parse_atom_entries(payload, f"Reddit r/{subreddit}")
            logger.info("r/%s RSS parsed %s entries", subreddit, len(parsed))
            results.extend(parsed)
        await asyncio.sleep(3.2)

    await asyncio.sleep(6)
    for query in SEARCH_QUERIES[:3]:
        if len(results) >= limit:
            break
        payload, status = await _get_text(
            client,
            "https://old.reddit.com/search.rss",
            {"q": query, "sort": "new", "t": "year"},
        )
        if status == 200 and payload:
            for item in _parse_atom_entries(payload, "Reddit"):
                item.extra["query"] = query
                item.extra["via"] = "search_rss"
                results.append(item)
        elif status in {401, 403, 429}:
            logger.warning("Reddit search RSS blocked (%s); stopping search RSS", status)
            break
        await asyncio.sleep(4)
    return results[:limit]


async def _reddit_json_fallback(client: httpx.AsyncClient, limit: int) -> list[RawDiscovery]:
    if limit <= 0:
        return []
    results: list[RawDiscovery] = []
    reddit_blocked = False
    pullpush_blocked = False
    for query in SEARCH_QUERIES:
        if len(results) >= limit:
            break
        payload = None
        if not reddit_blocked:
            payload, status = await _get_json(
                client,
                "https://www.reddit.com/search.json",
                params={"q": query, "sort": "new", "limit": 15, "t": "year", "raw_json": 1},
            )
            if status in {401, 403, 429}:
                reddit_blocked = True
                logger.warning("Reddit search JSON blocked (%s)", status)
        children: list[Any] = []
        if payload is None and not pullpush_blocked:
            await asyncio.sleep(2)
            payload, status = await _get_json(
                client,
                "https://api.pullpush.io/reddit/search/submission/",
                params={"q": query, "size": 10, "sort": "desc", "sort_type": "created_utc"},
            )
            if status in {429, 403}:
                pullpush_blocked = True
                logger.warning("PullPush blocked (%s)", status)
            if isinstance(payload, dict) and isinstance(payload.get("data"), list):
                children = [{"data": row} for row in payload["data"] if isinstance(row, dict)]
        elif isinstance(payload, dict):
            children = payload.get("data", {}).get("children", []) if isinstance(payload.get("data"), dict) else []
        if reddit_blocked and pullpush_blocked:
            break
        for child in children:
            data = child.get("data") if isinstance(child, dict) else None
            if not isinstance(data, dict):
                continue
            mapped = _raw_from_reddit_data(data, query)
            if mapped:
                results.append(mapped)
    return results[:limit]


def _raw_from_reddit_data(data: dict[str, Any], query: str) -> RawDiscovery | None:
    title = str(data.get("title") or "").strip()
    if not title:
        return None
    permalink = str(data.get("permalink") or "")
    reddit_id = str(data.get("id") or "")
    if permalink.startswith("/"):
        url = f"https://www.reddit.com{permalink}"
    elif reddit_id:
        url = f"https://www.reddit.com/comments/{reddit_id}"
    else:
        return None
    author = str(data.get("author") or "") or None
    if author in {"None", "[deleted]"}:
        author = None
    subreddit = str(data.get("subreddit") or "")
    return RawDiscovery(
        source_name=f"Reddit r/{subreddit}" if subreddit else "Reddit",
        source_url=url.split("?")[0],
        title=title,
        body=str(data.get("selftext") or "")[:4000],
        published_at=utc_from_unix(data.get("created_utc")),
        author=author,
        author_profile_url=f"https://www.reddit.com/user/{author}/" if author else None,
        extra={"query": query, "subreddit": subreddit, "via": "json"},
    )


async def _reddit_search(client: httpx.AsyncClient, limit: int) -> list[RawDiscovery]:
    return await _reddit_rss_and_search(client, limit)


async def _hacker_news(client: httpx.AsyncClient, limit: int) -> list[RawDiscovery]:
    results: list[RawDiscovery] = []
    tag_sets = ("story", "ask_hn", "comment")
    queries = list(dict.fromkeys([*HN_QUERIES, *HN_COMMENT_QUERIES]))
    since = int((datetime.now(UTC) - timedelta(days=90)).timestamp())
    for query in queries:
        for tags in tag_sets:
            if len(results) >= limit:
                return results[:limit]
            payload, _status = await _get_json(
                client,
                "https://hn.algolia.com/api/v1/search_by_date",
                params={
                    "query": f'"{query}"',
                    "tags": tags,
                    "hitsPerPage": 20,
                    "numericFilters": f"created_at_i>{since}",
                },
            )
            if not isinstance(payload, dict):
                continue
            for hit in payload.get("hits") or []:
                if not isinstance(hit, dict):
                    continue
                title = str(hit.get("title") or hit.get("story_title") or "").strip()
                object_id = hit.get("objectID")
                if not object_id:
                    continue
                if not title:
                    title = str(hit.get("comment_text") or "")[:120]
                created = hit.get("created_at")
                published = None
                if isinstance(created, str):
                    published = created if created.endswith("Z") else f"{created}Z" if "T" in created else created
                author = str(hit.get("author") or "") or None
                body = str(hit.get("story_text") or hit.get("comment_text") or "")[:4000]
                results.append(
                    RawDiscovery(
                        source_name="Hacker News",
                        source_url=f"https://news.ycombinator.com/item?id={object_id}",
                        title=title,
                        body=body,
                        published_at=published,
                        author=author,
                        author_profile_url=f"https://news.ycombinator.com/user?id={author}" if author else None,
                        company_url_hint=str(hit.get("url") or "") or None,
                        extra={"query": query, "tags": tags},
                    )
                )
    if not results:
        for query in queries:
            for tags in ("ask_hn", "comment"):
                if len(results) >= limit:
                    return results[:limit]
                payload, _status = await _get_json(
                    client,
                    "https://hn.algolia.com/api/v1/search_by_date",
                    params={
                        "query": query,
                        "tags": tags,
                        "hitsPerPage": 20,
                        "numericFilters": f"created_at_i>{since}",
                    },
                )
                if not isinstance(payload, dict):
                    continue
                for hit in payload.get("hits") or []:
                    if not isinstance(hit, dict):
                        continue
                    title = str(hit.get("title") or hit.get("story_title") or "").strip()
                    object_id = hit.get("objectID")
                    if not object_id:
                        continue
                    if not title:
                        title = str(hit.get("comment_text") or "")[:120]
                    created = hit.get("created_at")
                    published = None
                    if isinstance(created, str):
                        published = created if created.endswith("Z") else f"{created}Z" if "T" in created else created
                    author = str(hit.get("author") or "") or None
                    body = str(hit.get("story_text") or hit.get("comment_text") or "")[:4000]
                    results.append(
                        RawDiscovery(
                            source_name="Hacker News",
                            source_url=f"https://news.ycombinator.com/item?id={object_id}",
                            title=title,
                            body=body,
                            published_at=published,
                            author=author,
                            author_profile_url=f"https://news.ycombinator.com/user?id={author}" if author else None,
                            company_url_hint=str(hit.get("url") or "") or None,
                            extra={"query": query, "tags": tags, "match": "unquoted"},
                        )
                    )
                    if results and not _has_security_buyer_hint(results[-1]):
                        results.pop()
    for query in ("need pentest", "looking for pentest", "recommend pentest", "need VAPT"):
        if len(results) >= limit:
            break
        payload, _status = await _get_json(
            client,
            "https://hn.algolia.com/api/v1/search_by_date",
            params={
                "query": query,
                "tags": "comment",
                "hitsPerPage": 15,
                "numericFilters": f"created_at_i>{since}",
            },
        )
        if not isinstance(payload, dict):
            continue
        for hit in payload.get("hits") or []:
            if len(results) >= limit:
                break
            if not isinstance(hit, dict):
                continue
            title = str(hit.get("title") or hit.get("story_title") or "").strip()
            object_id = hit.get("objectID")
            if not object_id:
                continue
            if not title:
                title = str(hit.get("comment_text") or "")[:120]
            created = hit.get("created_at")
            published = None
            if isinstance(created, str):
                published = created if created.endswith("Z") else f"{created}Z" if "T" in created else created
            author = str(hit.get("author") or "") or None
            body = str(hit.get("story_text") or hit.get("comment_text") or "")[:4000]
            item = RawDiscovery(
                source_name="Hacker News",
                source_url=f"https://news.ycombinator.com/item?id={object_id}",
                title=title,
                body=body,
                published_at=published,
                author=author,
                author_profile_url=f"https://news.ycombinator.com/user?id={author}" if author else None,
                company_url_hint=str(hit.get("url") or "") or None,
                extra={"query": query, "tags": "comment", "match": "unquoted_push"},
            )
            if _has_security_buyer_hint(item):
                results.append(item)
    return results[:limit]


async def _duckduckgo(client: httpx.AsyncClient, limit: int) -> list[RawDiscovery]:
    """Best-effort public HTML search for LinkedIn/IH/RFP pages. Never required to succeed."""
    results: list[RawDiscovery] = []
    queries = [
        'site:reddit.com "need a pentest"',
        'site:reddit.com "looking for a pentest"',
        'site:reddit.com "need VAPT"',
        'site:reddit.com "SOC 2 pentest"',
        'site:reddit.com "penetration testing company"',
        'site:reddit.com "security audit startup"',
        'site:indiehackers.com "need pentest"',
        'site:indiehackers.com "security audit"',
        'site:linkedin.com/posts "looking for pentest"',
        'site:linkedin.com/posts "need VAPT"',
        'site:linkedin.com/posts "penetration testing"',
        'site:linkedin.com/posts "security audit" "looking for"',
        'site:wellfound.com "penetration testing"',
        'site:news.ycombinator.com "need a pentest"',
        'site:news.ycombinator.com "security audit"',
        '"need penetration testing" "startup"',
        '"looking for VAPT" "SaaS"',
        '"need security audit" "before launch"',
        '"penetration test" "SOC 2" "looking for"',
        '"need a pentest" startup',
        '"looking for pentest" company',
        '"need VAPT" SaaS',
        '"security audit" startup budget',
        '"hire pentester" freelance',
        *RFP_QUERIES,
    ]
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html",
    }
    for query in queries:
        if len(results) >= limit:
            break
        try:
            response = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers=headers,
            )
            if response.status_code != 200:
                continue
            html = response.text
        except Exception as exc:
            logger.warning("DuckDuckGo search failed for %s: %s", query, exc)
            continue
        for url, title in _parse_ddg_results(html)[:8]:
            if _is_junk_search_url(url):
                continue
            source = _source_from_url(url)
            results.append(
                RawDiscovery(
                    source_name=source,
                    source_url=url,
                    title=title,
                    body=title,
                    extra={"query": query},
                )
            )
    return results[:limit]


async def _github_issues(client: httpx.AsyncClient, limit: int) -> list[RawDiscovery]:
    """Public GitHub issue search for explicit pentest/VAPT buyer language. No scanning of private repos."""
    if limit <= 0:
        return []
    queries = [
        '"need pentest" OR "security audit"',
        '"looking for pentest" OR "need VAPT"',
        '"penetration testing company" OR "security consultant"',
    ]
    results: list[RawDiscovery] = []
    for query in queries:
        if len(results) >= limit:
            break
        try:
            response = await client.get(
                "https://api.github.com/search/issues",
                params={"q": query, "sort": "updated", "order": "desc", "per_page": min(25, limit)},
                headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT},
            )
            if response.status_code != 200:
                logger.warning("GitHub issue search blocked or empty (%s)", response.status_code)
                continue
            payload = response.json()
        except Exception as exc:
            logger.warning("GitHub issue search failed: %s", exc)
            continue
        if not isinstance(payload, dict):
            continue
        for item in payload.get("items") or []:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            url = str(item.get("html_url") or "").strip()
            if not title or not url:
                continue
            user = item.get("user") if isinstance(item.get("user"), dict) else {}
            author = str(user.get("login") or "") or None
            results.append(
                RawDiscovery(
                    source_name="GitHub Issues",
                    source_url=url.split("?")[0],
                    title=title,
                    body=str(item.get("body") or "")[:4000],
                    published_at=str(item.get("created_at") or item.get("updated_at") or "") or None,
                    author=author,
                    author_profile_url=str(user.get("html_url") or "") or None,
                    extra={"via": "github_search", "query": query},
                )
            )
            if len(results) >= limit:
                break
    return results[:limit]


async def _stackexchange(client: httpx.AsyncClient, limit: int) -> list[RawDiscovery]:
    """Public Stack Exchange questions that may contain buyer pentest/VAPT language."""
    if limit <= 0:
        return []
    results: list[RawDiscovery] = []
    for site, query in (
        ("security", "need pentest"),
        ("security", "penetration testing company"),
        ("softwareengineering", "need a pentest"),
    ):
        if len(results) >= limit:
            break
        payload, status = await _get_json(
            client,
            "https://api.stackexchange.com/2.3/search/advanced",
            params={
                "order": "desc",
                "sort": "creation",
                "q": query,
                "site": site,
                "filter": "withbody",
                "pagesize": 8,
                "fromdate": int((datetime.now(UTC) - timedelta(days=90)).timestamp()),
            },
        )
        if status in {400, 403, 429} or not isinstance(payload, dict):
            continue
        for item in payload.get("items") or []:
            if not isinstance(item, dict):
                continue
            title = unescape(str(item.get("title") or "")).strip()
            link = str(item.get("link") or "").strip()
            if not title or not link:
                continue
            body = unescape(re.sub(r"<[^>]+>", " ", str(item.get("body") or "")))
            created = item.get("creation_date")
            owner = item.get("owner") if isinstance(item.get("owner"), dict) else {}
            author = str(owner.get("display_name") or "") or None
            results.append(
                RawDiscovery(
                    source_name=f"Stack Exchange {site}",
                    source_url=link.split("?")[0],
                    title=title,
                    body=re.sub(r"\s+", " ", body).strip()[:4000],
                    published_at=utc_from_unix(created) if created else None,
                    author=author,
                    extra={"via": "stackexchange", "query": query},
                )
            )
    return results[:limit]


async def _upwork_rss(client: httpx.AsyncClient, limit: int) -> list[RawDiscovery]:
    """Public Upwork job RSS — often rate-limited; never required."""
    if limit <= 0:
        return []
    results: list[RawDiscovery] = []
    for query in ("penetration testing", "VAPT", "security audit SOC 2"):
        payload, status = await _get_text(
            client,
            "https://www.upwork.com/ab/feed/jobs/rss",
            {"q": query, "sort": "recency"},
        )
        if status != 200 or not payload:
            logger.warning("Upwork RSS blocked or empty (%s) for %s", status, query)
            break
        for item in _parse_feed_entries(payload, "Upwork"):
            item.extra["query"] = query
            item.extra["via"] = "upwork_rss"
            results.append(item)
        if len(results) >= limit:
            break
        await asyncio.sleep(1.2)
    return [item for item in results if _has_security_buyer_hint(item)][:limit]


async def fetch_url(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        response = await client.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
            follow_redirects=True,
        )
        if response.status_code >= 400:
            return None
        return response.text[:200_000]
    except Exception as exc:
        logger.debug("Fetch failed %s: %s", url, exc)
        return None


def _parse_ddg_results(html: str) -> list[tuple[str, str]]:
    import re

    pairs: list[tuple[str, str]] = []
    for match in re.finditer(
        r'uddg=([^&"]+)[^>]*>\s*([^<]+)',
        html,
        flags=re.IGNORECASE,
    ):
        from urllib.parse import unquote

        url = unquote(match.group(1))
        title = match.group(2).strip()
        if url.startswith("http") and title:
            pairs.append((url, title))
    if not pairs:
        for match in re.finditer(r'href="(https?://[^"]+)"[^>]*>([^<]{8,180})', html):
            url = match.group(1)
            if "duckduckgo.com" in url:
                continue
            pairs.append((url, match.group(2).strip()))
    return pairs


def _is_junk_search_url(url: str) -> bool:
    lowered = url.lower()
    return any(
        token in lowered
        for token in (
            "duckduckgo.com/y.js",
            "bing.com/aclick",
            "ad_provider=",
            "ad_type=txad",
        )
    )


def _source_from_url(url: str) -> str:
    lowered = url.lower()
    if "reddit.com" in lowered:
        return "Reddit"
    if "indiehackers.com" in lowered:
        return "Indie Hackers"
    if "linkedin.com" in lowered:
        return "LinkedIn"
    if "github.com" in lowered:
        return "GitHub Issues"
    if "stackexchange.com" in lowered or "stackoverflow.com" in lowered:
        return "Stack Exchange"
    if "upwork.com" in lowered:
        return "Upwork"
    if "sam.gov" in lowered:
        return "SAM.gov RFP"
    if "contractsfinder" in lowered:
        return "UK Contracts Finder"
    if "ted.europa.eu" in lowered:
        return "TED Europe RFP"
    return "Web search"


async def _get_text(
    client: httpx.AsyncClient, url: str, params: dict[str, Any]
) -> tuple[str | None, int | None]:
    try:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            logger.warning("HTTP %s for %s", response.status_code, url)
            return None, response.status_code
        return response.text, response.status_code
    except Exception as exc:
        logger.warning("Text fetch failed %s: %s", url, exc)
        return None, None


async def _get_json(
    client: httpx.AsyncClient, url: str, params: dict[str, Any]
) -> tuple[dict[str, Any] | None, int | None]:
    try:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            logger.warning("HTTP %s for %s", response.status_code, url)
            return None, response.status_code
        payload = response.json()
        return (payload if isinstance(payload, dict) else None), response.status_code
    except Exception as exc:
        logger.warning("JSON fetch failed %s: %s", url, exc)
        return None, None
