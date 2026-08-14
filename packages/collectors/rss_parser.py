import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import urlparse
from xml.etree import ElementTree

from collectors.events import NormalizedEvent
from collectors.extraction.quality import enrichment_metadata, strip_html
from intelligence.entity_resolution.platform_domains import is_platform_domain


def _text(element: ElementTree.Element, name: str) -> str:
    found = element.find(name)
    return unescape(found.text or "").strip() if found is not None else ""


def _namespaced_text(element: ElementTree.Element, namespace: str, name: str) -> str:
    found = element.find(f"{{{namespace}}}{name}")
    return unescape(found.text or "").strip() if found is not None else ""


def _categories(item: ElementTree.Element, atom_namespace: str) -> list[str]:
    categories: list[str] = []
    for category in item.findall("category"):
        value = (category.text or category.attrib.get("term") or "").strip()
        if value and value not in categories:
            categories.append(value)
    for category in item.findall(f"{{{atom_namespace}}}category"):
        value = (category.attrib.get("term") or category.text or "").strip()
        if value and value not in categories:
            categories.append(value)
    return categories[:12]


def _published_at(item: ElementTree.Element, atom_namespace: str) -> datetime:
    value = (
        _text(item, "pubDate")
        or _text(item, "updated")
        or _text(item, "published")
        or _namespaced_text(item, atom_namespace, "updated")
        or _namespaced_text(item, atom_namespace, "published")
    )
    if not value:
        return datetime.now(UTC)
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(UTC)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _accept_org_website(url: str) -> str | None:
    """Official company website only — never article/news/platform URLs."""
    raw = (url or "").strip()
    if not raw:
        return None
    if not raw.startswith("http"):
        raw = f"https://{raw}"
    try:
        parsed = urlparse(raw)
        host = parsed.netloc.lower().removeprefix("www.")
    except ValueError:
        return None
    if not host or is_platform_domain(host):
        return None
    # Article-depth paths are not identity — require site root or shallow path
    path = parsed.path or "/"
    if path not in {"", "/"} and path.count("/") > 2:
        return None
    return f"{parsed.scheme or 'https'}://{host}"


def _organization_website(item: ElementTree.Element, atom_namespace: str) -> str | None:
    """Extract Organization → Official Website from feed metadata. Never invent."""
    # Atom author/uri
    author = item.find(f"{{{atom_namespace}}}author")
    if author is not None:
        uri = _namespaced_text(author, atom_namespace, "uri") or _text(author, "uri")
        hit = _accept_org_website(uri)
        if hit:
            return hit
    # RSS source/@url (publisher feed identity — only if not a news platform)
    source_el = item.find("source")
    if source_el is not None:
        hit = _accept_org_website(source_el.attrib.get("url") or "")
        if hit:
            return hit
    # Explicit company/organization link relations
    for link in item.findall(f"{{{atom_namespace}}}link"):
        rel = (link.attrib.get("rel") or "").lower()
        href = link.attrib.get("href") or ""
        if rel in {"related", "via", "alternate"} and href:
            # alternate is usually the article — skip deep article paths
            if rel == "alternate":
                continue
            hit = _accept_org_website(href)
            if hit:
                return hit
    return None


def parse_rss_events(
    xml: str,
    *,
    source: str,
    feed_url: str,
    max_items: int,
) -> list[NormalizedEvent]:
    root = ElementTree.fromstring(xml)
    content_namespace = "http://purl.org/rss/1.0/modules/content/"
    dc_namespace = "http://purl.org/dc/elements/1.1/"
    atom_namespace = "http://www.w3.org/2005/Atom"
    items = root.findall(".//item")

    if not items:
        items = root.findall(f".//{{{atom_namespace}}}entry")

    events: list[NormalizedEvent] = []
    for item in items[:max_items]:
        title = strip_html(_text(item, "title") or _namespaced_text(item, atom_namespace, "title"))
        link = _text(item, "link")
        if not link:
            atom_link = item.find(f"{{{atom_namespace}}}link")
            link = atom_link.attrib.get("href", "") if atom_link is not None else ""

        raw_content = (
            _namespaced_text(item, content_namespace, "encoded")
            or _text(item, "description")
            or _namespaced_text(item, atom_namespace, "summary")
            or _namespaced_text(item, atom_namespace, "content")
            or title
        )
        content = strip_html(raw_content)
        author = (
            _text(item, "author")
            or _text(item, "dc:creator")
            or _namespaced_text(item, dc_namespace, "creator")
        )
        # Atom <author><name>…</name></author>
        if not author:
            author_el = item.find(f"{{{atom_namespace}}}author")
            if author_el is not None:
                author = _namespaced_text(author_el, atom_namespace, "name") or _text(author_el, "name")
        categories = _categories(item, atom_namespace)

        if not title or not link:
            continue

        org_website = _organization_website(item, atom_namespace)
        published = _published_at(item, atom_namespace)
        trigger_signals = _trigger_signals(title, content, source)
        extra: dict = {
            "feed_url": feed_url,
            "author": author or None,
            "categories": categories,
            # Article URL host is never company identity for RSS — leave domain empty unless org site found
            "domain": None,
            "article_only": org_website is None,
            "source_kind": "event",
            "lead_eligible": True,
            "content_occurred_at": published.isoformat(),
            "buying_signals": trigger_signals,
        }
        # Product Hunt Atom embeds /r/p/{post_id} "Link" → official site redirect (when resolvable)
        if source == "product_hunt":
            redirect_match = re.search(
                r"https?://(?:www\.)?producthunt\.com/r/p/(\d+)[^\"'\s<]*",
                raw_content,
                re.I,
            )
            if redirect_match:
                extra["ph_post_id"] = redirect_match.group(1)
                extra["ph_redirect_url"] = redirect_match.group(0).replace("&amp;", "&")
            if author:
                extra["ph_maker"] = author
                extra["makers"] = [author]
        # HN / launch posts often link directly to the product site
        if source in {"hacker_news", "github_trending"} and not org_website:
            hit = _accept_org_website(link)
            if hit:
                org_website = hit
                extra["article_only"] = False
        if org_website:
            host = urlparse(org_website).netloc.lower().removeprefix("www.")
            extra["canonical_website"] = org_website
            extra["organization_website"] = org_website
            extra["official_website"] = org_website
            extra["homepage"] = org_website
            extra["official_domain"] = host
            extra["domain"] = host
            extra["website_attribution"] = {
                "website": org_website,
                "source": "rss_canonical_company_website",
                "confidence": 88,
                "collector": source,
            }

        metadata = enrichment_metadata(
            title=title,
            content=content,
            url=link,
            extra=extra,
        )
        # Re-assert: never keep article/news host as company domain without org evidence
        if not org_website:
            metadata["domain"] = None
            metadata["article_only"] = True

        events.append(
            NormalizedEvent(
                source=source,
                url=link,
                title=title,
                content=content,
                published_at=published,
                metadata=metadata,
            )
        )

    return events


def _trigger_signals(title: str, content: str, source: str) -> list[str]:
    blob = f"{title} {content}".lower()
    signals: list[str] = []
    if source == "product_hunt" or "product hunt" in blob:
        signals.append(f"Product Hunt launch signal: {title[:100]}")
    if any(k in blob for k in ("hiring", "we're hiring", "is hiring", "job opening")):
        signals.append(f"Hiring signal: {title[:100]}")
    if any(k in blob for k in ("funding", "raised", "series a", "series b", "seed round")):
        signals.append(f"Funding signal: {title[:100]}")
    if any(k in blob for k in ("launch", "launched", "shipping", "show hn")):
        signals.append(f"Launch signal: {title[:100]}")
    if not signals:
        signals.append(f"{source} signal: {title[:100]}")
    return signals[:4]
