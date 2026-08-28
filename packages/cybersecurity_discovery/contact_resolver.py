"""Contact enrichment waterfall for cybersecurity leads.

Tries multiple methods to find emails and contact info for anonymous forum posters.
Methods are tried in order of reliability:
1. HN User Profile API (free, no key)
2. Reddit User Profile API (free, no key)
3. Company website contact recovery (reuse existing module)
4. Email pattern generation + SMTP verification
5. WHOIS domain lookup
"""

from __future__ import annotations

import asyncio
import logging
import re
import smtplib
import socket
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

HN_USER_API = "https://hacker-news.firebaseio.com/v0/user/{username}.json"
REDDIT_USER_API = "https://www.reddit.com/user/{username}/about.json"
USER_AGENT = "BeaconCyberEnrichment/1.0 (security research)"


async def enrich_contacts(
    opp: Any,
    client: httpx.AsyncClient,
    *,
   HN_author: str | None = None,
    Reddit_author: str | None = None,
    company_url: str | None = None,
) -> dict[str, Any]:
    """Try multiple methods to find contact info for an opportunity.

    Returns dict with keys: email, buyer_name, company_url, contact_source, contact_evidence.
    """
    result: dict[str, Any] = {
        "email": getattr(opp, "email", None),
        "buyer_name": getattr(opp, "buyer_name", None),
        "company_url": getattr(opp, "company_url", None) or company_url,
        "contact_source": None,
        "contact_evidence": [],
    }

    # If we already have an email, skip enrichment
    if result["email"]:
        return result

    # Method 1: HN User Profile
    if HN_author and not result["email"]:
        hn_result = await _resolve_hn_profile(client, HN_author)
        if hn_result:
            result["contact_evidence"].append(hn_result)
            if hn_result.get("email") and not result["email"]:
                result["email"] = hn_result["email"]
                result["contact_source"] = "hn_profile"
            if hn_result.get("company_url") and not result["company_url"]:
                result["company_url"] = hn_result["company_url"]
            if hn_result.get("buyer_name") and not result["buyer_name"]:
                result["buyer_name"] = hn_result["buyer_name"]

    # Method 2: Reddit User Profile
    if Reddit_author and not result["email"]:
        reddit_result = await _resolve_reddit_profile(client, Reddit_author)
        if reddit_result:
            result["contact_evidence"].append(reddit_result)
            if reddit_result.get("email") and not result["email"]:
                result["email"] = reddit_result["email"]
                result["contact_source"] = "reddit_profile"
            if reddit_result.get("company_url") and not result["company_url"]:
                result["company_url"] = reddit_result["company_url"]

    # Method 3: Company Website Contact Recovery
    if result["company_url"] and not result["email"]:
        site_result = await _recover_from_website(client, result["company_url"])
        if site_result:
            result["contact_evidence"].append(site_result)
            if site_result.get("email") and not result["email"]:
                result["email"] = site_result["email"]
                result["contact_source"] = "company_website"
            if site_result.get("buyer_name") and not result["buyer_name"]:
                result["buyer_name"] = site_result["buyer_name"]

    # Method 4: Email Pattern Generation + SMTP Verify
    if result["company_url"] and result["buyer_name"] and not result["email"]:
        pattern_result = await _generate_and_verify_email(
            client, result["company_url"], result["buyer_name"]
        )
        if pattern_result:
            result["contact_evidence"].append(pattern_result)
            if pattern_result.get("email") and not result["email"]:
                result["email"] = pattern_result["email"]
                result["contact_source"] = "pattern_generation"

    # Method 5: WHOIS Domain Lookup
    if result["company_url"] and not result["email"]:
        whois_result = await _whois_lookup(result["company_url"])
        if whois_result:
            result["contact_evidence"].append(whois_result)
            if whois_result.get("email") and not result["email"]:
                result["email"] = whois_result["email"]
                result["contact_source"] = "whois"

    return result


async def _resolve_hn_profile(client: httpx.AsyncClient, username: str) -> dict[str, Any] | None:
    """Fetch HN user profile and extract company/email from about field."""
    try:
        resp = await client.get(
            HN_USER_API.format(username=username),
            timeout=10.0,
            headers={"User-Agent": USER_AGENT},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data:
            return None

        about = str(data.get("about") or "").strip()
        if not about:
            return None

        result: dict[str, Any] = {
            "source": "hn_profile",
            "username": username,
            "karma": data.get("karma", 0),
        }

        # Extract email from about field
        email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', about)
        if email_match:
            result["email"] = email_match.group(0).lower()

        # Extract website/company from about field
        url_match = re.search(r'https?://[^\s<>"]+', about)
        if url_match:
            url = url_match.group(0)
            host = urlparse(url).netloc.lower().removeprefix("www.")
            if host and "ycombinator.com" not in host:
                result["company_url"] = f"https://{host}"

        # Extract company name patterns
        company_patterns = [
            r'(?:CTO|CEO|Founder|Co-founder|Head of)\s+(?:at|@)\s+([A-Z][A-Za-z0-9\s&]+)',
            r'(?:working\s+at|building)\s+([A-Z][A-Za-z0-9\s&]+)',
            r'([A-Z][A-Za-z0-9]+)\s+(?:CTO|CEO|Founder|Co-founder)',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, about)
            if match:
                result["buyer_name"] = match.group(1).strip()
                break

        return result
    except Exception as exc:  # noqa: BLE001
        logger.debug("HN profile resolution failed for %s: %s", username, exc)
        return None


async def _resolve_reddit_profile(client: httpx.AsyncClient, username: str) -> dict[str, Any] | None:
    """Fetch Reddit user profile and extract website/social links."""
    try:
        resp = await client.get(
            REDDIT_USER_API.format(username=username),
            timeout=10.0,
            headers={"User-Agent": USER_AGENT},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data or "data" not in data:
            return None
        profile = data["data"]

        result: dict[str, Any] = {
            "source": "reddit_profile",
            "username": username,
        }

        # Extract website from profile
        website = profile.get("subreddit", {}).get("public_description", "")
        if not website:
            website = profile.get("icon_img", "")

        # Check for social links in about
        about = profile.get("subreddit", {}).get("description", "")
        if about:
            url_match = re.search(r'https?://[^\s<>"]+', about)
            if url_match:
                url = url_match.group(0)
                host = urlparse(url).netloc.lower().removeprefix("www.")
                if host and "reddit.com" not in host:
                    result["company_url"] = f"https://{host}"

            # Extract email
            email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', about)
            if email_match:
                result["email"] = email_match.group(0).lower()

        return result
    except Exception as exc:  # noqa: BLE001
        logger.debug("Reddit profile resolution failed for %s: %s", username, exc)
        return None


async def _recover_from_website(client: httpx.AsyncClient, company_url: str) -> dict[str, Any] | None:
    """Scrape company website for contact info (emails, founder names)."""
    try:
        base = company_url.rstrip("/")
        result: dict[str, Any] = {"source": "company_website", "company_url": company_url}

        # Try common contact pages
        contact_paths = ["/", "/contact", "/contact-us", "/about", "/about-us", "/team"]
        for path in contact_paths:
            try:
                resp = await client.get(f"{base}{path}", timeout=10.0, follow_redirects=True)
                if resp.status_code != 200:
                    continue
                html = resp.text

                # Extract emails
                emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', html)
                emails = [e.lower() for e in emails if _is_valid_email(e)]
                if emails:
                    # Prefer info@ or founder emails
                    brand_domain = urlparse(company_url).netloc.lower().removeprefix("www.")
                    brand_emails = [e for e in emails if brand_domain in e]
                    if brand_emails:
                        result["email"] = brand_emails[0]
                    elif emails:
                        result["email"] = emails[0]

                # Extract founder name from JSON-LD or meta
                founder_match = re.search(
                    r'"founder"\s*:\s*"([^"]+)"', html
                ) or re.search(
                    r'(?:founded|created)\s+by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', html
                )
                if founder_match:
                    result["buyer_name"] = founder_match.group(1).strip()

                if result.get("email"):
                    break
            except Exception:  # noqa: BLE001
                continue

        return result if result.get("email") or result.get("buyer_name") else None
    except Exception as exc:  # noqa: BLE001
        logger.debug("Website contact recovery failed for %s: %s", company_url, exc)
        return None


async def _generate_and_verify_email(
    client: httpx.AsyncClient, company_url: str, buyer_name: str
) -> dict[str, Any] | None:
    """Generate email patterns and verify via SMTP."""
    try:
        domain = urlparse(company_url).netloc.lower().removeprefix("www.")
        if not domain:
            return None

        # Extract first and last name from buyer_name
        parts = buyer_name.strip().split()
        if len(parts) < 2:
            return None
        first = parts[0].lower()
        last = parts[-1].lower()

        # Generate candidates
        candidates = [
            f"{first}@{domain}",
            f"{first}.{last}@{domain}",
            f"{first}{last}@{domain}",
            f"{f[0]}{last}@{domain}",
            f"{first}.{f[0]}@{domain}",
        ]

        # Check MX record first
        mx_valid = await _check_mx(domain)
        if not mx_valid:
            return None

        # Try SMTP verification
        for email in candidates:
            if await _smtp_verify(email, domain):
                return {"source": "pattern_generation", "email": email}

        return None
    except Exception as exc:  # noqa: BLE001
        logger.debug("Email pattern generation failed for %s: %s", company_url, exc)
        return None


async def _whois_lookup(company_url: str) -> dict[str, Any] | None:
    """WHOIS domain lookup for registrant email."""
    try:
        domain = urlparse(company_url).netloc.lower().removeprefix("www.")
        if not domain:
            return None

        # Use python-whois if available
        try:
            import whois
            w = whois.whois(domain)
            if w and w.emails:
                for email in w.emails:
                    if email and _is_valid_email(email):
                        return {"source": "whois", "email": email.lower()}
        except ImportError:
            pass

        # Fallback: RDAP lookup
        try:
            import httpx as _httpx
            resp = await _httpx.AsyncClient(timeout=10.0).get(
                f"https://rdap.org/domain/{domain}",
                headers={"User-Agent": USER_AGENT},
            )
            if resp.status_code == 200:
                data = resp.json()
                for entity in data.get("entities", []):
                    for vc in entity.get("vcardArray", [])[1:]:
                        if isinstance(vc, list):
                            for item in vc:
                                if isinstance(item, list) and len(item) >= 2:
                                    if item[0] == "email":
                                        email = item[1]
                                        if _is_valid_email(email):
                                            return {"source": "rdap", "email": email.lower()}
        except Exception:  # noqa: BLE001
            pass

        return None
    except Exception as exc:  # noqa: BLE001
        logger.debug("WHOIS lookup failed for %s: %s", company_url, exc)
        return None


async def _check_mx(domain: str) -> bool:
    """Check if domain has MX records."""
    try:
        import asyncio.dns
        resolver = asyncio.dns.Resolver()
        mx = await resolver.query(domain, "MX")
        return bool(mx)
    except Exception:  # noqa: BLE001
        return False


async def _smtp_verify(email: str, domain: str) -> bool:
    """Verify email via SMTP RCPT TO (no email sent)."""
    try:
        import asyncio.dns
        resolver = asyncio.dns.Resolver()
        mx_records = await resolver.query(domain, "MX")
        if not mx_records:
            return False
        mx_host = str(mx_records[0].exchange).rstrip(".")

        loop = asyncio.get_event_loop()

        def _verify():
            try:
                with smtplib.SMTP(mx_host, 25, timeout=5) as smtp:
                    smtp.ehlo("beacon.local")
                    smtp.mail("test@beacon.local")
                    code, _ = smtp.rcpt(email)
                    return code == 250
            except Exception:  # noqa: BLE001
                return False

        return await loop.run_in_executor(None, _verify)
    except Exception:  # noqa: BLE001
        return False


def _is_valid_email(email: str) -> bool:
    """Basic email validation."""
    if not email or len(email) > 254:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
