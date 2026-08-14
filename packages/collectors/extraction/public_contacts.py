"""Public-page contact extraction — evidence only, never invent people or emails."""

from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\+?\d[\d\-\s().]{7,}\d")
LINKEDIN_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/(?:in|company)/[A-Za-z0-9\-_/]+", re.I)
# 2–3 token person names only (prevents nav-text greed).
# Do NOT treat hyphen as a name/role separator — it breaks "Name Co-Founder".
_NAME = r"([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,2})"
# Accept Co-Founder / Co-founder / Cofounder variants from public HTML.
_ROLE = (
    r"(Co-[Ff]ounder|Cofounder|Founder|CEO|CTO|COO|CMO|CRO|"
    r"Chief\s+Executive\s+Officer|Chief\s+Technology\s+Officer|"
    r"Chief\s+Scientific\s+Officer|CSO)"
)
ROLE_RE = re.compile(rf"\b{_NAME}\s*[,–—|:]\s*{_ROLE}\b")
ROLE_RE2 = re.compile(rf"\b{_ROLE}\s*[,–—|:]\s*{_NAME}\b")
# "Jane Doe Co-Founder" / "Jane Doe Founder" (no punctuation)
ROLE_RE3 = re.compile(rf"\b{_NAME}\s+{_ROLE}\b")
# Titles that often precede a real person name in dense team HTML.
_LEADING_TITLE = re.compile(
    r"^(?:"
    r"Strategic\s+Alliance\s+Director|"
    r"Advanced\s+Robotics\s+Hardware\s+Engineer|"
    r"Hardware\s+Engineer|"
    r"Alliance\s+Director|"
    r"Chief\s+Technology|"
    r"Chief\s+Executive|"
    r"Team|Profile|Directors|Board|"
    r"Director|Engineer|Manager|Officer|President|Chairman|"
    r"VP|Vice\s+President"
    r")\s+",
    re.I,
)
_TITLE_TOKENS = {
    "director",
    "directors",
    "engineer",
    "manager",
    "officer",
    "president",
    "chairman",
    "advanced",
    "robotics",
    "hardware",
    "strategic",
    "alliance",
    "vice",
    "vp",
    "team",
    "profile",
    "board",
    "chief",
    "technology",
    "executive",
    "scientific",
    "names",
    "serial",
    "read",
    "story",
    "lightspeed",
}
# Non-person fragments from customer stories / marketing pages
_BLOCKED_NAME_PHRASES = frozenset(
    {
        "lightspeed read",
        "amplitude names",
        "amplitude names serial",
        "technology officer",
        "executive officer",
        "chief technology",
        "chief executive",
        "dax dasilva",  # Lightspeed customer story on Stripe homepage — not Stripe
    }
)

CONTACT_PATHS = ("", "/about", "/about-us", "/company", "/team", "/contact", "/contact-us", "/leadership")
SKIP_EMAIL = ("example.com", "sentry.io", "wixpress", "schema.org", "github.com", "producthunt.com")


def _normalize_role(role: str) -> str:
    r = re.sub(r"\s+", " ", role).strip()
    low = r.lower().replace(" ", "")
    if low in {"co-founder", "cofounder"}:
        return "Co-Founder"
    if low == "founder":
        return "Founder"
    if "chiefexecutive" in low or r.upper() == "CEO":
        return "CEO"
    if "chieftechnology" in low or r.upper() == "CTO":
        return "CTO"
    if "chiefscientific" in low or r.upper() == "CSO":
        return "CSO"
    if r.upper() in {"COO", "CMO", "CRO"}:
        return r.upper()
    return r


def _clean_person_name(raw: str) -> str:
    name = html.unescape(re.sub(r"\s+", " ", raw).strip())
    name = re.sub(r"^(Read\s+)?Bio\s+", "", name, flags=re.I).strip()
    for _ in range(4):
        nxt = _LEADING_TITLE.sub("", name).strip()
        if nxt == name:
            break
        name = nxt
    parts = [p for p in name.split() if p.lower() not in _TITLE_TOKENS]
    if len(parts) >= 2:
        # Prefer the trailing proper-name tokens after stripping titles.
        name = " ".join(parts[-3:] if len(parts) > 3 else parts)
    return name

def _same_org_email(email: str, domain: str) -> bool:
    host = email.lower().split("@")[-1]
    d = domain.lower().removeprefix("www.")
    if not d:
        return False
    return host == d or host.endswith("." + d)


def _plausible_phone(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 10 or len(digits) > 15:
        return False
    # ORCID / UUID fragments / repeated filler
    if re.search(r"0000-000\d", phone):
        return False
    if re.search(r"(\d)\1{5,}", digits):
        return False
    if digits.startswith("000"):
        return False
    return True


def extract_public_contacts(html_src: str, *, page_url: str, domain: str) -> dict[str, Any]:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html_src)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)

    emails: list[str] = []
    for email in EMAIL_RE.findall(html_src):
        low = email.lower()
        if any(x in low for x in SKIP_EMAIL):
            continue
        # OFC: only same-organization domain emails count as business email evidence
        if domain and not _same_org_email(low, domain):
            continue
        if low not in emails:
            emails.append(low)

    phones: list[str] = []
    for phone in PHONE_RE.findall(text):
        if not _plausible_phone(phone):
            continue
        cleaned = re.sub(r"\s+", " ", phone).strip()
        if cleaned not in phones:
            phones.append(cleaned)

    linkedin: list[str] = []
    for li in LINKEDIN_RE.findall(html_src):
        if li not in linkedin:
            linkedin.append(li)

    people: list[dict[str, str]] = []
    for m in ROLE_RE.finditer(text):
        people.append({"name": m.group(1), "role": m.group(2), "source": page_url})
    for m in ROLE_RE2.finditer(text):
        people.append({"name": m.group(2), "role": m.group(1), "source": page_url})
    for m in ROLE_RE3.finditer(text):
        people.append({"name": m.group(1), "role": m.group(2), "source": page_url})

    # Dedupe people; reject Co-Founder split artifacts and nav/bio noise
    NOISE = (
        "coming soon",
        "read bio",
        "leadership",
        "officer read",
        "people",
        "our team",
        "view open",
    )
    seen: set[str] = set()
    unique_people: list[dict[str, str]] = []
    for p in people:
        name = _clean_person_name(p["name"])
        parts = name.split()
        if len(parts) < 2 or len(parts) > 4:
            continue
        if parts[-1].lower() in {"co", "the", "and"}:
            continue
        # Reject single-initial / first-name-only residue after cleaning
        if any(len(tok) < 2 for tok in parts):
            continue
        low = name.lower()
        if low in {"executive officer", "chief executive", "unknown"} or low in _BLOCKED_NAME_PHRASES:
            continue
        if any(n in low for n in NOISE):
            continue
        # Residual title / marketing pollution after cleaning → skip
        if any(tok in _TITLE_TOKENS for tok in low.split()):
            continue
        # Require look of a real person name (letters only tokens)
        if not all(re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", tok) for tok in parts):
            continue
        role = _normalize_role(p["role"])
        key = f"{low}|{role.lower()}"
        if key in seen:
            continue
        seen.add(key)
        unique_people.append({"name": name, "role": role, "source": p["source"]})

    return {
        "emails": emails[:5],
        "phones": phones[:3],
        "linkedin": linkedin[:5],
        "decision_makers": unique_people[:8],
        "page": page_url,
    }


def recover_from_official_website(website: str, *, timeout: float = 6.0, max_pages: int = 6) -> dict[str, Any]:
    """Crawl a few public pages on the official site. Never invent."""
    if not website.startswith("http"):
        website = f"https://{website}"
    parsed = urlparse(website)
    domain = parsed.netloc.lower().removeprefix("www.")
    base = f"{parsed.scheme}://{parsed.netloc}"

    merged: dict[str, Any] = {
        "emails": [],
        "phones": [],
        "linkedin": [],
        "decision_makers": [],
        "pages_fetched": [],
        "about_excerpt": None,
    }
    seen_people: set[str] = set()

    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "BeaconOFC/1.0 (+https://beacon.ai)"},
        ) as client:
            for path in CONTACT_PATHS:
                if len(merged["pages_fetched"]) >= max_pages:
                    break
                url = base if not path else urljoin(base + "/", path.lstrip("/"))
                try:
                    resp = client.get(url)
                except Exception:  # noqa: BLE001
                    continue
                if resp.status_code >= 400 or len(resp.text) < 40:
                    continue
                merged["pages_fetched"].append(url)
                hit = extract_public_contacts(resp.text, page_url=url, domain=domain)
                for e in hit["emails"]:
                    if e not in merged["emails"]:
                        merged["emails"].append(e)
                for p in hit["phones"]:
                    if p not in merged["phones"]:
                        merged["phones"].append(p)
                for li in hit["linkedin"]:
                    if li not in merged["linkedin"]:
                        merged["linkedin"].append(li)
                for person in hit["decision_makers"]:
                    key = f"{person['name'].lower()}|{person['role'].lower()}"
                    if key in seen_people:
                        continue
                    seen_people.add(key)
                    merged["decision_makers"].append(person)
                if path in {"/about", "/about-us", "/company"} and not merged["about_excerpt"]:
                    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", resp.text)
                    text = re.sub(r"<[^>]+>", " ", text)
                    text = re.sub(r"\s+", " ", text).strip()
                    if len(text) > 80:
                        merged["about_excerpt"] = text[:400]
    except Exception:  # noqa: BLE001
        return merged

    return merged
