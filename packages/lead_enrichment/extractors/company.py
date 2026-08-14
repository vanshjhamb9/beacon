from __future__ import annotations

import re

from lead_enrichment.connectors.website import normalize_domain, website_url_for_domain
from lead_enrichment.models.types import (
    EnrichedCompanyProfile,
    EnrichmentOpportunityInput,
    EnrichmentSourceType,
    FieldAttribution,
    WebsiteFetchResult,
)

_SIZE_PATTERNS: tuple[tuple[re.Pattern[str], str, int], ...] = (
    (re.compile(r"\b(\d{1,3})\s*[-–to]+\s*(\d{2,5})\s+employees\b", re.I), "range", 0),
    (re.compile(r"\b(\d{1,5})\+?\s+employees\b", re.I), "count", 0),
    (re.compile(r"\bteam of\s+(\d{1,4})\b", re.I), "count", 0),
)

_FOUNDED_RE = re.compile(r"\b(?:founded|established|since)\s+(?:in\s+)?(19|20)\d{2}\b", re.I)
_COUNTRY_HINTS = (
    "united states",
    "usa",
    "uk",
    "united kingdom",
    "canada",
    "australia",
    "germany",
    "france",
    "india",
    "singapore",
    "netherlands",
    "ireland",
)


class CompanyProfileExtractor:
    def extract(
        self,
        item: EnrichmentOpportunityInput,
        website: WebsiteFetchResult | None,
    ) -> EnrichedCompanyProfile:
        domain = normalize_domain(item.domain or item.website)
        website_url = item.website or website_url_for_domain(domain)
        attributions: list[FieldAttribution] = []

        def attr(field: str, value: object, source: EnrichmentSourceType, confidence: float, url: str | None = None, evidence: str = "") -> None:
            if value is None or value == "":
                return
            attributions.append(
                FieldAttribution(
                    field_name=field,
                    value=value,
                    source=source,
                    source_url=url,
                    confidence=confidence,
                    evidence=evidence,
                )
            )

        industry = item.industry or self._from_context(item, "industry")
        description = item.description or self._description_from_website(website) or item.opportunity_narrative
        location = item.location or self._from_context(item, "location") or self._location_from_website(website)
        country = item.country or self._country_from_text(f"{location or ''} {description or ''}")
        founded_year = self._founded_year(website, item)
        employee_count, size_range = self._size_estimate(item, website)

        attr("company_name", item.company_name, EnrichmentSourceType.BEACON_INTELLIGENCE, 100.0)
        attr("domain", domain, EnrichmentSourceType.BEACON_INTELLIGENCE, 90.0 if domain else 0.0)
        attr("website", website_url, EnrichmentSourceType.COMPANY_WEBSITE if website and website.fetched else EnrichmentSourceType.BEACON_INTELLIGENCE, 88.0 if website_url else 0.0, website_url)
        attr("industry", industry, EnrichmentSourceType.BEACON_CONTEXT, 80.0 if industry else 0.0)
        attr("description", description, EnrichmentSourceType.COMPANY_WEBSITE if website and website.fetched else EnrichmentSourceType.BEACON_OPPORTUNITY, 70.0 if description else 0.0)
        attr("location", location, EnrichmentSourceType.COMPANY_WEBSITE if location and website else EnrichmentSourceType.USER_PROVIDED, 65.0 if location else 0.0)
        attr("country", country, EnrichmentSourceType.COMPANY_WEBSITE, 60.0 if country else 0.0)
        attr("founded_year", founded_year, EnrichmentSourceType.COMPANY_WEBSITE, 68.0 if founded_year else 0.0)
        attr("employee_count_estimate", employee_count, EnrichmentSourceType.COMPANY_WEBSITE, 62.0 if employee_count else 0.0)
        attr("company_size_range", size_range, EnrichmentSourceType.COMPANY_WEBSITE, 62.0 if size_range else 0.0)

        sub_industry = self._from_context(item, "sub_industry")
        revenue_estimate = None
        budget = item.revenue_recommendation.get("estimated_budget_range")
        if isinstance(budget, str) and budget:
            revenue_estimate = budget
            attr("revenue_estimate", revenue_estimate, EnrichmentSourceType.BEACON_REVENUE, 70.0)

        return EnrichedCompanyProfile(
            company_name=item.company_name,
            website=website_url,
            domain=domain,
            industry=industry if isinstance(industry, str) else None,
            sub_industry=sub_industry if isinstance(sub_industry, str) else None,
            description=description if isinstance(description, str) else None,
            location=location if isinstance(location, str) else None,
            country=country,
            founded_year=founded_year,
            employee_count_estimate=employee_count,
            company_size_range=size_range,
            revenue_estimate=revenue_estimate,
            attributions=attributions,
        )

    def _from_context(self, item: EnrichmentOpportunityInput, key: str) -> str | None:
        value = item.context_intelligence.get(key)
        return str(value) if value else None

    def _description_from_website(self, website: WebsiteFetchResult | None) -> str | None:
        if not website:
            return None
        for page in website.pages:
            if page.page_type in {"about", "homepage"} and len(page.text) > 80:
                return page.text[:500]
        return None

    def _location_from_website(self, website: WebsiteFetchResult | None) -> str | None:
        if not website:
            return None
        pattern = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?),\s*([A-Z]{2}|[A-Z][a-z]+)\b")
        for page in website.pages:
            if page.page_type in {"contact", "about", "homepage"}:
                match = pattern.search(page.text)
                if match:
                    return match.group(0)
        return None

    def _country_from_text(self, text: str) -> str | None:
        lowered = text.lower()
        for country in _COUNTRY_HINTS:
            if country in lowered:
                return country.title() if country not in {"usa", "uk"} else country.upper()
        return None

    def _founded_year(self, website: WebsiteFetchResult | None, item: EnrichmentOpportunityInput) -> int | None:
        attrs_year = item.company_attributes.get("founded_year")
        if isinstance(attrs_year, int) and 1800 <= attrs_year <= 2100:
            return attrs_year
        if website:
            for page in website.pages:
                match = _FOUNDED_RE.search(page.text)
                if match:
                    year = int(re.search(r"(19|20)\d{2}", match.group(0)).group(0))  # type: ignore[union-attr]
                    return year
        return None

    def _size_estimate(
        self,
        item: EnrichmentOpportunityInput,
        website: WebsiteFetchResult | None,
    ) -> tuple[int | None, str | None]:
        attrs_count = item.company_attributes.get("employee_count")
        if isinstance(attrs_count, int) and attrs_count > 0:
            return attrs_count, self._range_for_count(attrs_count)

        stage = str(item.context_intelligence.get("company_stage") or "").lower()
        stage_map = {
            "startup": (15, "1-50"),
            "early": (25, "1-50"),
            "scaling": (120, "51-200"),
            "growth": (250, "201-500"),
            "enterprise": (1200, "1001-5000"),
        }
        if website:
            for page in website.pages:
                for pattern, kind, _ in _SIZE_PATTERNS:
                    match = pattern.search(page.text)
                    if not match:
                        continue
                    if kind == "range":
                        low, high = int(match.group(1)), int(match.group(2))
                        return (low + high) // 2, f"{low}-{high}"
                    count = int(match.group(1))
                    return count, self._range_for_count(count)

        if stage in stage_map:
            return stage_map[stage]
        return None, None

    def _range_for_count(self, count: int) -> str:
        if count <= 10:
            return "1-10"
        if count <= 50:
            return "11-50"
        if count <= 200:
            return "51-200"
        if count <= 500:
            return "201-500"
        if count <= 1000:
            return "501-1000"
        if count <= 5000:
            return "1001-5000"
        return "5000+"
