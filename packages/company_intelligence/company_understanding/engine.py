"""Company Understanding — extract business facts from website corpus. Never fabricate."""

from __future__ import annotations

import re
from typing import Any

from company_intelligence.models.types import UNKNOWN, AttributedValue, CompanyBusinessProfile, WebsiteCorpus

INDUSTRY_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Software", ("saas", "software", "platform", "api", "developer")),
    ("Healthcare", ("healthcare", "health", "clinic", "hospital", "patient")),
    ("Finance", ("fintech", "finance", "banking", "payments", "insurance")),
    ("E-commerce", ("ecommerce", "e-commerce", "shopify", "retail", "storefront")),
    ("Education", ("education", "edtech", "learning", "school", "university")),
    ("Manufacturing", ("manufacturing", "factory", "industrial", "supply chain")),
    ("Real Estate", ("real estate", "property", "proptech")),
    ("Marketing", ("marketing", "agency", "advertising", "seo")),
    ("Logistics", ("logistics", "shipping", "freight", "warehouse")),
    ("Automotive", ("automotive", "vehicle", "mobility")),
)


def _attr(value: str, *, source: str, page: str | None, excerpt: str | None, confidence: float) -> AttributedValue:
    if not value or value.strip() in {"", UNKNOWN}:
        return AttributedValue()
    return AttributedValue(
        value=value.strip()[:500],
        confidence=confidence,
        source=source,
        page=page,
        excerpt=(excerpt or value)[:240],
        evidence=[f"source:{source}", f"value:{value.strip()[:80]}"],
    )


class CompanyUnderstandingEngine:
    def extract(self, corpus: WebsiteCorpus, payload: dict[str, Any] | None = None) -> CompanyBusinessProfile:
        payload = payload or {}
        blob = self._blob(corpus, payload)
        homepage = corpus.pages[0] if corpus.pages else None
        page_url = homepage.url if homepage else corpus.website

        description = self._first(
            [
                (homepage.description if homepage and homepage.description != UNKNOWN else None, "meta_description"),
                (homepage.open_graph.get("description") if homepage else None, "open_graph"),
                (payload.get("description"), "payload"),
                (self._sentence_about(blob), "page_text"),
            ],
            page=page_url,
            confidence=88,
        )
        tagline = self._first(
            [
                (homepage.open_graph.get("title") if homepage else None, "open_graph"),
                (homepage.title if homepage and homepage.title != UNKNOWN else None, "title"),
                (homepage.headings[0] if homepage and homepage.headings else None, "heading"),
            ],
            page=page_url,
            confidence=80,
        )
        mission = self._field_near(blob, ("mission", "our mission"), page=page_url)
        vision = self._field_near(blob, ("vision", "our vision"), page=page_url)
        industry = self._industry(blob, payload, page=page_url)
        business_model = self._business_model(blob, page=page_url)
        company_type = self._company_type(blob, page=page_url)
        target_market = self._field_near(blob, ("for teams", "for enterprises", "for startups", "built for"), page=page_url)
        primary_product = self._primary_product(corpus, payload, page=page_url)
        primary_services = self._field_near(blob, ("services", "we offer", "what we do"), page=page_url)
        country = self._country(blob, payload, page=page_url)
        locations = self._field_near(blob, ("offices", "headquartered", "based in", "locations"), page=page_url)
        languages = _attr("English", source="default_public", page=page_url, excerpt="English", confidence=40) if blob else AttributedValue()
        if any(x in blob for x in ("español", "french", "deutsch", "multilingual")):
            languages = _attr("Multi-language", source="page_text", page=page_url, excerpt="multilingual", confidence=70)
        customer_type = self._customer_type(blob, page=page_url)
        founded = self._founded(blob, page=page_url)
        employees = self._employees(blob, payload, page=page_url)
        revenue = self._field_near(blob, ("arr", "revenue", "million"), page=page_url, confidence=55)
        enterprise = _attr(
            "Enterprise" if "enterprise" in blob else UNKNOWN,
            source="page_text",
            page=page_url,
            excerpt="enterprise" if "enterprise" in blob else None,
            confidence=75 if "enterprise" in blob else 0,
        )

        evidence = [
            f"pages:{corpus.page_count}",
            f"industry:{industry.value}",
            f"product:{primary_product.value}",
        ]
        return CompanyBusinessProfile(
            description=description,
            tagline=tagline,
            mission=mission,
            vision=vision,
            industry=industry,
            business_model=business_model,
            company_type=company_type,
            target_market=target_market,
            primary_product=primary_product,
            primary_services=primary_services,
            country=country,
            locations=locations,
            languages=languages if languages.value != UNKNOWN else AttributedValue(),
            customer_type=customer_type,
            founded=founded,
            employee_hints=employees,
            revenue_hints=revenue,
            enterprise_status=enterprise,
            evidence=evidence,
        )

    def _blob(self, corpus: WebsiteCorpus, payload: dict[str, Any]) -> str:
        parts = [
            str(payload.get("description") or ""),
            str(payload.get("content") or ""),
            str(payload.get("body") or ""),
        ]
        for p in corpus.pages:
            parts.extend([p.title, p.description, " ".join(p.headings), p.text[:3000], p.footer])
        return " ".join(parts).lower()

    def _first(self, candidates: list[tuple[Any, str]], *, page: str | None, confidence: float) -> AttributedValue:
        for value, source in candidates:
            if value and str(value).strip() and str(value).strip() != UNKNOWN:
                return _attr(str(value), source=source, page=page, excerpt=str(value), confidence=confidence)
        return AttributedValue()

    def _field_near(self, blob: str, cues: tuple[str, ...], *, page: str | None, confidence: float = 70) -> AttributedValue:
        for cue in cues:
            idx = blob.find(cue)
            if idx >= 0:
                excerpt = blob[idx : idx + 160].strip()
                return _attr(excerpt[:160], source="page_text", page=page, excerpt=excerpt, confidence=confidence)
        return AttributedValue()

    def _sentence_about(self, blob: str) -> str | None:
        m = re.search(r"(.{40,220}(?:platform|software|helps|enables|automates|builds).{0,80})", blob)
        return m.group(1).strip() if m else None

    def _industry(self, blob: str, payload: dict[str, Any], *, page: str | None) -> AttributedValue:
        if payload.get("industry"):
            return _attr(str(payload["industry"]), source="payload", page=page, excerpt=str(payload["industry"]), confidence=90)
        for label, terms in INDUSTRY_PATTERNS:
            if any(t in blob for t in terms):
                return _attr(label, source="keyword_evidence", page=page, excerpt=next(t for t in terms if t in blob), confidence=78)
        return AttributedValue()

    def _business_model(self, blob: str, *, page: str | None) -> AttributedValue:
        if "subscription" in blob or "saas" in blob:
            return _attr("SaaS / Subscription", source="page_text", page=page, excerpt="saas", confidence=80)
        if "marketplace" in blob:
            return _attr("Marketplace", source="page_text", page=page, excerpt="marketplace", confidence=78)
        if "agency" in blob or "services" in blob:
            return _attr("Services", source="page_text", page=page, excerpt="services", confidence=65)
        return AttributedValue()

    def _company_type(self, blob: str, *, page: str | None) -> AttributedValue:
        if "startup" in blob:
            return _attr("Startup", source="page_text", page=page, excerpt="startup", confidence=70)
        if "enterprise software" in blob or "b2b" in blob:
            return _attr("B2B Software", source="page_text", page=page, excerpt="b2b", confidence=75)
        return AttributedValue()

    def _primary_product(self, corpus: WebsiteCorpus, payload: dict[str, Any], *, page: str | None) -> AttributedValue:
        if payload.get("primary_product"):
            return _attr(str(payload["primary_product"]), source="payload", page=page, excerpt=str(payload["primary_product"]), confidence=90)
        for p in corpus.pages:
            if p.path.rstrip("/") in {"/products", "/product", "/solutions"} and p.headings:
                return _attr(p.headings[0], source="products_page", page=p.url, excerpt=p.headings[0], confidence=82)
        if corpus.pages and corpus.pages[0].headings:
            return _attr(corpus.pages[0].headings[0], source="homepage_heading", page=page, excerpt=corpus.pages[0].headings[0], confidence=70)
        name = str(payload.get("company_name") or payload.get("name") or "")
        return _attr(name, source="company_name", page=page, excerpt=name, confidence=50) if name else AttributedValue()

    def _country(self, blob: str, payload: dict[str, Any], *, page: str | None) -> AttributedValue:
        if payload.get("country"):
            return _attr(str(payload["country"]), source="payload", page=page, excerpt=str(payload["country"]), confidence=90)
        for c, keys in (
            ("United States", ("united states", " usa", "u.s.", "san francisco", "new york")),
            ("United Kingdom", ("united kingdom", " london", " uk")),
            ("India", (" india", "bengaluru", "bangalore", "mumbai")),
            ("Canada", (" canada", "toronto", "vancouver")),
            ("Germany", (" germany", "berlin", "munich")),
        ):
            if any(k in blob for k in keys):
                return _attr(c, source="location_evidence", page=page, excerpt=next(k for k in keys if k in blob), confidence=72)
        return AttributedValue()

    def _customer_type(self, blob: str, *, page: str | None) -> AttributedValue:
        if "enterprise" in blob:
            return _attr("Enterprise", source="page_text", page=page, excerpt="enterprise", confidence=80)
        if "smb" in blob or "small business" in blob:
            return _attr("SMB", source="page_text", page=page, excerpt="smb", confidence=78)
        if "developer" in blob:
            return _attr("Developers", source="page_text", page=page, excerpt="developer", confidence=75)
        return AttributedValue()

    def _founded(self, blob: str, *, page: str | None) -> AttributedValue:
        m = re.search(r"founded in (20\d{2}|19\d{2})", blob)
        if m:
            return _attr(m.group(1), source="page_text", page=page, excerpt=m.group(0), confidence=85)
        return AttributedValue()

    def _employees(self, blob: str, payload: dict[str, Any], *, page: str | None) -> AttributedValue:
        if payload.get("employees"):
            return _attr(str(payload["employees"]), source="payload", page=page, excerpt=str(payload["employees"]), confidence=90)
        m = re.search(r"(\d{1,4})\+?\s*(?:employees|people|team members)", blob)
        if m:
            return _attr(m.group(1), source="page_text", page=page, excerpt=m.group(0), confidence=80)
        return AttributedValue()
