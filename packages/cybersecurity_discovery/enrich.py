"""Contact enrichment from publicly visible evidence only.

Never guess emails. Never synthesize first.last@domain patterns.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from packages.cybersecurity_discovery.gates import email_is_generic
from packages.cybersecurity_discovery.schema import (
    CyberOpportunity,
    DECISION_MAKER_ROLES,
    EmailStatus,
    evidence_item,
)

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
LINKEDIN_RE = re.compile(
    r"https?://(?:www\.)?linkedin\.com/(?:in|company)/[A-Za-z0-9\-_%]+/?",
    re.IGNORECASE,
)
URL_RE = re.compile(r"https?://[^\s)>\"]+", re.IGNORECASE)
PHONE_RE = re.compile(r"\+?\d[\d\-\s().]{8,}\d")

PLATFORM_HOSTS = {
    "reddit.com",
    "www.reddit.com",
    "old.reddit.com",
    "np.reddit.com",
    "redditstatic.com",
    "www.redditstatic.com",
    "preview.redd.it",
    "i.redd.it",
    "b.thumbs.redditmedia.com",
    "styles.redditmedia.com",
    "external-preview.redd.it",
    "news.ycombinator.com",
    "hn.algolia.com",
    "linkedin.com",
    "www.linkedin.com",
    "twitter.com",
    "x.com",
    "indiehackers.com",
    "www.indiehackers.com",
    "upwork.com",
    "www.upwork.com",
    "github.com",
    "duckduckgo.com",
    "google.com",
    "youtube.com",
    "medium.com",
}

ROLE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (role, re.compile(rf"\b{re.escape(role)}\b", re.IGNORECASE))
    for role in DECISION_MAKER_ROLES
]
ROLE_PATTERNS.extend(
    [
        ("Founder", re.compile(r"\b(?:i'?m|i am|we are)\s+(?:the\s+)?(?:founder|co-?founder|ceo)\b", re.IGNORECASE)),
        ("CTO", re.compile(r"\b(?:i'?m|i am)\s+(?:the\s+)?cto\b", re.IGNORECASE)),
        ("CISO", re.compile(r"\b(?:i'?m|i am)\s+(?:the\s+)?ciso\b", re.IGNORECASE)),
    ]
)

DISPOSABLE_LOCAL = {"noreply", "no-reply", "donotreply", "mailer-daemon"}


def extract_emails(text: str) -> list[str]:
    """Return emails that literally appear in the text. Never construct addresses."""
    found: list[str] = []
    for match in EMAIL_RE.findall(text or ""):
        email = match.strip().rstrip(".,;")
        local = email.split("@", 1)[0].lower()
        if local in DISPOSABLE_LOCAL:
            continue
        if email.lower() not in {e.lower() for e in found}:
            found.append(email)
    return found


def extract_linkedin(text: str) -> list[str]:
    return list(dict.fromkeys(LINKEDIN_RE.findall(text or "")))


def extract_company_urls(text: str) -> list[str]:
    urls: list[str] = []
    for match in URL_RE.findall(text or ""):
        url = match.rstrip(".,);")
        host = urlparse(url).netloc.lower().removeprefix("www.")
        if not host or any(host.endswith(p.removeprefix("www.")) or host == p for p in PLATFORM_HOSTS):
            if host in {"linkedin.com"} or host.endswith("linkedin.com"):
                continue
            continue
        urls.append(url)
    return list(dict.fromkeys(urls))


def extract_role(text: str) -> str | None:
    for role, pattern in ROLE_PATTERNS:
        if pattern.search(text or ""):
            return role
    return None


def guess_email(_name: str | None, _domain: str | None) -> None:
    """Intentionally does nothing. Email guessing is forbidden."""
    return None


def apply_text_contacts(opp: CyberOpportunity, text: str) -> None:
    """Attach emails/LinkedIn/URLs that appear on the original post."""
    emails = extract_emails(text)
    if emails:
        chosen = next((e for e in emails if not email_is_generic(e)), emails[0])
        opp.email = chosen
        opp.email_status = EmailStatus.PUBLIC_UNVERIFIED.value
        opp.email_evidence.append(
            evidence_item(
                "email",
                chosen,
                opp.source_name,
                opp.source_url,
                "MEDIUM",
                opp.observed_at,
            )
        )
    linkedin = extract_linkedin(text)
    person = [u for u in linkedin if "/in/" in u.lower()]
    company_li = [u for u in linkedin if "/company/" in u.lower()]
    if person:
        opp.linkedin_url = person[0]
        opp.linkedin_status = "PUBLIC"
        if not opp.buyer_profile_url:
            opp.buyer_profile_url = person[0]
    elif company_li and not opp.linkedin_url:
        opp.linkedin_url = company_li[0]
        opp.linkedin_status = "PUBLIC"
    if not opp.company_url:
        urls = extract_company_urls(text)
        if urls:
            opp.company_url = urls[0]
    if not opp.buyer_role:
        opp.buyer_role = extract_role(text)
    _set_identity(opp)


def apply_website_contacts(
    opp: CyberOpportunity,
    html: str,
    page_url: str,
    *,
    verified: bool = False,
) -> None:
    """Use emails/forms found on an official company page. Still never guess."""
    emails = extract_emails(_strip_html(html)) + extract_emails(html)
    mailto = _mailto_addresses(html)
    for email in mailto + emails:
        if not opp.email:
            opp.email = email
        if email_is_generic(email):
            opp.email_status = EmailStatus.PUBLIC_UNVERIFIED.value
        else:
            opp.email_status = EmailStatus.VERIFIED.value if verified else EmailStatus.PUBLIC_UNVERIFIED.value
        opp.email_evidence.append(
            evidence_item(
                "email",
                email,
                "company_website",
                page_url,
                "HIGH" if verified and not email_is_generic(email) else "MEDIUM",
                opp.observed_at,
            )
        )
        break
    linkedin = extract_linkedin(html)
    if linkedin and not opp.linkedin_url:
        opp.linkedin_url = linkedin[0]
        opp.linkedin_status = "PUBLIC"
    if _has_contact_form(html):
        opp.contactability_evidence.append(
            evidence_item(
                "contact_form",
                True,
                "company_website",
                page_url,
                "MEDIUM",
                opp.observed_at,
            )
        )
    if page_url and not opp.company_url:
        opp.company_url = page_url
    if page_url:
        opp.company_verified = True
    _set_identity(opp)


def maybe_company_from_url(url: str | None) -> str | None:
    if not url:
        return None
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if not host or host in PLATFORM_HOSTS:
        return None
    label = host.split(".")[0]
    if label in {"www", "app", "mail"}:
        return None
    return label.replace("-", " ").title()


def _set_identity(opp: CyberOpportunity) -> None:
    if opp.buyer_name and opp.buyer_role and (opp.buyer_profile_url or opp.linkedin_url):
        opp.identity_confidence = "HIGH"
    elif opp.buyer_name and (opp.buyer_role or opp.buyer_profile_url or opp.linkedin_url):
        opp.identity_confidence = "MEDIUM"
    elif opp.buyer_name:
        opp.identity_confidence = "LOW"
    elif opp.company and (opp.company_url or opp.company_verified):
        opp.identity_confidence = "LOW"
    else:
        opp.identity_confidence = "UNKNOWN"


def _mailto_addresses(html: str) -> list[str]:
    found = re.findall(r"mailto:([^\"'\s>]+)", html or "", flags=re.IGNORECASE)
    cleaned: list[str] = []
    for item in found:
        addr = item.split("?", 1)[0].strip()
        if EMAIL_RE.fullmatch(addr):
            cleaned.append(addr)
    return cleaned


def _has_contact_form(html: str) -> bool:
    lowered = (html or "").lower()
    return "<form" in lowered and any(t in lowered for t in ("contact", "message", "email"))


def _strip_html(html: str) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(html or "")
    except Exception:
        return re.sub(r"<[^>]+>", " ", html or "")
    return parser.text


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        if data and data.strip():
            self._chunks.append(data.strip())

    @property
    def text(self) -> str:
        return " ".join(self._chunks)


def resolve_url(base: str, href: str) -> str:
    return urljoin(base, href)
