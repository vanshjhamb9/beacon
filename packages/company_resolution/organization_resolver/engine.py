"""Phase 2 — resolve organization identity from a raw signal. Never invent."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from company_resolution.models.types import OrganizationCandidate, RawSignalEnvelope, UNKNOWN
from intelligence.entity_resolution.normalization import normalize_company_name, normalize_domain
from intelligence.entity_resolution.platform_domains import is_platform_domain, is_platform_label
from production_hardening.admission.engine import FAKE_NAME_PATTERNS

DOMAIN_RE = re.compile(r"\b(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+)(?:/[^\s]*)?", re.I)
LINKEDIN_CO_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/company/[a-zA-Z0-9\-_/%]+", re.I)
GITHUB_ORG_RE = re.compile(r"https?://(?:www\.)?github\.com/([a-zA-Z0-9\-]+)/?", re.I)
FUNDING_RE = re.compile(r"(crunchbase\.com|pitchbook\.com|dealroom\.co)/[^\s]+", re.I)
SHOW_HN_RE = re.compile(r"\bShow HN:\s*([A-Za-z0-9][A-Za-z0-9.&+\- ]{1,60})", re.I)
PRODUCT_TITLE_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9 .&\-]{1,60}?)(?:\s*[—\-–:|]\s+|\s+–\s+)", re.I)

# Reject version-like and non-business "domains" extracted from titles
INVALID_DOMAIN_RE = re.compile(
    r"^("
    r"\d+(\.\d+)+|"  # 2.0, 3.1.4
    r"[a-z]+-\d+(\.\d+)+|"  # gpt-5.6
    r"\d+(\.\d+)*x|"  # 6.4x
    r".*\.(tsx|ts|js|jsx|py|md|json|yml|yaml|xml|exe|sh|map)$"
    r")$",
    re.I,
)
VALID_TLDS = frozenset(
    {
        "com",
        "io",
        "ai",
        "co",
        "dev",
        "app",
        "net",
        "org",
        "so",
        "gg",
        "sh",
        "to",
        "me",
        "us",
        "uk",
        "de",
        "fr",
        "ca",
        "au",
        "in",
        "tech",
        "health",
        "cloud",
        "software",
        "systems",
        "studio",
        "tools",
        "hq",
        "inc",
        "xyz",
        "page",
        "site",
        "online",
        "store",
        "shop",
        "pro",
        "info",
        "biz",
        "tv",
        "fm",
        "ly",
        "vc",
        "fund",
        "capital",
    }
)


class OrganizationResolverEngine:
    """Search signal for org names, domains, LinkedIn, GitHub org, funding, homepage."""

    def resolve(self, signal: RawSignalEnvelope, *, hints: dict[str, Any] | None = None) -> OrganizationCandidate:
        hints = hints or {}
        text = f"{signal.title}\n{signal.body}"
        evidence: list[str] = []

        domains = self._collect_domains(signal, hints)
        official_domain = domains[0] if domains else None
        if official_domain:
            evidence.append(f"domain:{official_domain}")

        linkedin = self._first(LINKEDIN_CO_RE.findall(text) + list(filter(None, [hints.get("linkedin_company")])))
        if linkedin:
            evidence.append(f"linkedin:{linkedin}")

        github_org = None
        for m in GITHUB_ORG_RE.findall(text):
            if m.lower() not in {"topics", "settings", "marketplace", "orgs", "features", "pricing"}:
                github_org = m
                evidence.append(f"github_org:{m}")
                break
        if hints.get("github_organization"):
            github_org = str(hints["github_organization"])
            evidence.append("github_org:hint")

        funding = None
        fm = FUNDING_RE.search(text)
        if fm:
            funding = fm.group(0)
            evidence.append(f"funding:{funding}")

        homepage = None
        if official_domain and not is_platform_domain(official_domain):
            homepage = f"https://{official_domain}"
            evidence.append(f"homepage:{homepage}")
        elif hints.get("homepage"):
            homepage = str(hints["homepage"])
            evidence.append("homepage:hint")

        legal_name = self._resolve_name(signal, hints, official_domain)
        if legal_name and legal_name != UNKNOWN:
            evidence.append(f"name:{legal_name}")

        found = bool(
            (legal_name and legal_name != UNKNOWN and not is_platform_label(legal_name))
            and (
                (official_domain and not is_platform_domain(official_domain))
                or linkedin
                or (github_org and signal.source == "github_trending")
                or funding
                or homepage
            )
        )
        # Strict: need name + non-platform domain for found=True (sprint: if none exist, discard)
        if not (legal_name and legal_name != UNKNOWN and official_domain and not is_platform_domain(official_domain)):
            # Product Hunt exception: name + producthunt URL still not enough without product domain
            # Allow LinkedIn company + name
            if legal_name and legal_name != UNKNOWN and linkedin:
                found = True
            else:
                found = False

        return OrganizationCandidate(
            legal_name=legal_name or UNKNOWN,
            official_domain=official_domain if official_domain and not is_platform_domain(official_domain) else None,
            official_url=homepage,
            linkedin_company=linkedin,
            github_organization=github_org,
            funding_page=funding,
            homepage=homepage,
            business_registration=str(hints["business_registration"]) if hints.get("business_registration") else None,
            evidence=evidence,
            found=found,
        )

    def _collect_domains(self, signal: RawSignalEnvelope, hints: dict[str, Any]) -> list[str]:
        candidates: list[str] = []
        for d in signal.domains:
            nd = normalize_domain(d)
            if nd and self._is_plausible_domain(nd):
                candidates.append(nd)
        meta_domain = signal.metadata.get("domain") or hints.get("domain")
        if isinstance(meta_domain, str):
            nd = normalize_domain(meta_domain)
            if nd and self._is_plausible_domain(nd):
                candidates.insert(0, nd)
        for link in [*signal.outbound_links, signal.url or ""]:
            if not link:
                continue
            host = urlparse(link if "://" in link else f"https://{link}").netloc.lower().removeprefix("www.")
            nd = normalize_domain(host)
            if nd and self._is_plausible_domain(nd):
                candidates.append(nd)
        # Only mine body/title domains when metadata didn't supply one (avoid version false positives)
        if not candidates:
            for m in DOMAIN_RE.findall(f"{signal.title}\n{signal.body}"):
                nd = normalize_domain(m)
                if nd and self._is_plausible_domain(nd):
                    candidates.append(nd)

        unique: list[str] = []
        seen: set[str] = set()
        for d in candidates:
            if d in seen:
                continue
            seen.add(d)
            unique.append(d)
        non_platform = [d for d in unique if not is_platform_domain(d)]
        return non_platform or []

    def _is_plausible_domain(self, domain: str) -> bool:
        d = domain.lower().removeprefix("www.")
        if not d or INVALID_DOMAIN_RE.match(d):
            return False
        parts = d.split(".")
        if len(parts) < 2:
            return False
        tld = parts[-1]
        if tld.isdigit() or not tld.isalpha():
            return False
        if len(tld) > 12:
            return False
        # Require known-ish TLD OR length>=2 alpha tld without digits in labels that look like versions
        if any(p.replace("-", "").isdigit() for p in parts[:-1]):
            return False
        if tld not in VALID_TLDS and len(tld) not in {2, 3, 4}:
            return False
        if tld not in VALID_TLDS and len(tld) == 4 and tld not in {"info", "name", "aero"}:
            # allow common 4-letter only if in set; else reject exotic false positives
            return tld in {"tech", "site", "blog", "shop", "fund"}
        return True

    def _resolve_name(
        self,
        signal: RawSignalEnvelope,
        hints: dict[str, Any],
        domain: str | None,
    ) -> str:
        for key in ("company_name", "legal_name", "organization", "product_name"):
            if hints.get(key):
                name = str(hints[key]).strip()
                if self._valid_name(name):
                    return name
        meta_hints = signal.metadata.get("company_hints") or []
        if isinstance(meta_hints, list):
            for h in meta_hints:
                if self._valid_name(str(h)):
                    return str(h).strip()
        if signal.source == "product_hunt":
            m = PRODUCT_TITLE_RE.match(signal.title.strip())
            if m and self._valid_name(m.group(1)):
                return m.group(1).strip()
            # Fallback: first segment before dash
            part = re.split(r"\s+[—\-–|:]\s+", signal.title.strip(), maxsplit=1)[0].strip()
            if self._valid_name(part) and len(part.split()) <= 4:
                return part
        m = SHOW_HN_RE.search(signal.title)
        if m and self._valid_name(m.group(1)):
            return m.group(1).strip()
        for ent in signal.extracted_entities + signal.mentions:
            if self._valid_name(ent):
                return ent.strip()
        if domain:
            label = domain.split(".")[0].replace("-", " ").title()
            if self._valid_name(label) and len(label) >= 3:
                return label
        return UNKNOWN

    def _valid_name(self, name: str) -> bool:
        n = (name or "").strip()
        if len(n) < 2 or len(n) > 80:
            return False
        low = n.lower()
        if low in FAKE_NAME_PATTERNS or is_platform_label(n):
            return False
        if normalize_company_name(n) in {"", "unknown", "none"}:
            return False
        # Reject code-like tokens
        if re.search(r"\.(tsx|ts|js|py|md|json|yml|yaml|xml)$", low):
            return False
        return True

    @staticmethod
    def _first(items: list[Any]) -> str | None:
        for item in items:
            if item:
                return str(item)
        return None
