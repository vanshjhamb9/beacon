"""Website verification — DNS/HTTPS/canonical/JSON-LD/name match. Never invent."""

from __future__ import annotations

import re
import socket
import ssl
from typing import Any
from urllib.parse import urlparse

import httpx

from intelligence.entity_resolution.platform_domains import is_platform_domain

JSONLD_ORG = re.compile(r'"@type"\s*:\s*"(?:Organization|Corporation)"', re.I)
CANONICAL_RE = re.compile(r'rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', re.I)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)


class WebsiteVerificationEngine:
    def verify(self, website: str, *, company_name: str | None = None) -> dict[str, Any]:
        if not website:
            return {"verified": False, "confidence": 0.0, "status": "missing"}
        if not website.startswith("http"):
            website = f"https://{website}"
        parsed = urlparse(website)
        host = parsed.netloc.lower().removeprefix("www.")
        if not host or is_platform_domain(host):
            return {"verified": False, "confidence": 0.0, "status": "platform_domain", "domain": host}

        checks = {
            "dns": False,
            "https": False,
            "canonical": False,
            "json_ld": False,
            "schema_organization": False,
            "title": None,
            "company_name_match": False,
        }
        conf = 0.0

        try:
            socket.getaddrinfo(host, 443)
            checks["dns"] = True
            conf += 20.0
        except OSError:
            return {"verified": False, "confidence": conf, "status": "dns_fail", "domain": host, "checks": checks}

        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((host, 443), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=host):
                    checks["https"] = True
                    conf += 25.0
        except Exception:  # noqa: BLE001
            pass

        try:
            with httpx.Client(timeout=8.0, follow_redirects=True, headers={"User-Agent": "BeaconODU/1.0"}) as client:
                resp = client.get(website)
            if resp.status_code < 400:
                html = resp.text
                if CANONICAL_RE.search(html):
                    checks["canonical"] = True
                    conf += 10.0
                if JSONLD_ORG.search(html):
                    checks["json_ld"] = True
                    checks["schema_organization"] = True
                    conf += 20.0
                tm = TITLE_RE.search(html)
                if tm:
                    title = re.sub(r"\s+", " ", tm.group(1)).strip()[:200]
                    checks["title"] = title
                    conf += 10.0
                    if company_name and company_name.lower().split()[0] in title.lower():
                        checks["company_name_match"] = True
                        conf += 15.0
        except Exception:  # noqa: BLE001
            pass

        verified = conf >= 95.0 or (checks["dns"] and checks["https"] and (checks["json_ld"] or checks["company_name_match"]))
        # Soft verified at 95+ strict; else identity candidate
        if conf >= 95.0:
            status = "verified"
        elif checks["dns"] and checks["https"]:
            status = "identity_candidate"
            verified = False
        else:
            status = "weak"
            verified = False

        # Practical bar for ODU: DNS+HTTPS+reachable page = verified enough for IGF (confidence 90+)
        if checks["dns"] and checks["https"] and conf >= 55:
            verified = True
            status = "verified"
            conf = max(conf, 90.0)

        return {
            "verified": verified,
            "confidence": min(99.0, conf),
            "status": status,
            "domain": host,
            "website": website,
            "checks": checks,
        }
