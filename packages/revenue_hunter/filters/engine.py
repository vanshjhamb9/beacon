from __future__ import annotations

from revenue_hunter.filters.taxonomy import (
    normalize_country,
    normalize_funding,
    normalize_industry,
    normalize_revenue,
    size_band_from_employees,
)
from revenue_hunter.models.types import FilterCriteria, FilterMatch, RevenueHunterInput


class TargetAccountFilter:
    """Deterministic ICP gate — only high-probability buying markets pass."""

    def apply(self, item: RevenueHunterInput, criteria: FilterCriteria) -> FilterMatch:
        country = normalize_country(item.country)
        industry = normalize_industry(item.industry)
        funding = normalize_funding(item.funding_stage)
        revenue = normalize_revenue(item.revenue_band)
        size = item.company_size_band or size_band_from_employees(item.employee_count)

        allowed_countries = {normalize_country(c) for c in criteria.countries} if criteria.countries else None
        allowed_sizes = set(criteria.company_sizes) if criteria.company_sizes else None
        allowed_industries = {normalize_industry(i) for i in criteria.industries} if criteria.industries else None
        allowed_funding = {normalize_funding(f) for f in criteria.funding_stages} if criteria.funding_stages else None
        allowed_revenue = {normalize_revenue(r) for r in criteria.revenue_bands} if criteria.revenue_bands else None

        country_match = allowed_countries is None or (country is not None and country in allowed_countries)
        size_match = allowed_sizes is None or (size is not None and size in allowed_sizes)
        industry_match = allowed_industries is None or (industry is not None and industry in allowed_industries)
        funding_match = (
            allowed_funding is None
            or funding is None  # unknown funding does not hard-fail when stage list is set
            or funding in allowed_funding
        )
        revenue_match = (
            allowed_revenue is None
            or revenue is None
            or revenue in allowed_revenue
        )

        # Hard gates: country + size + industry must match when criteria provided
        hard_pass = country_match and size_match and industry_match
        soft_pass = funding_match and revenue_match
        passed = hard_pass and soft_pass

        reasons: list[str] = []
        evidence: list[str] = []
        if country_match and country:
            evidence.append(f"country:{country}")
        else:
            reasons.append(f"country_mismatch:{item.country or 'unknown'}")
        if size_match and size:
            evidence.append(f"size:{size}")
        else:
            reasons.append(f"size_mismatch:{size or item.employee_count or 'unknown'}")
        if industry_match and industry:
            evidence.append(f"industry:{industry}")
        else:
            reasons.append(f"industry_mismatch:{item.industry or 'unknown'}")
        if funding:
            evidence.append(f"funding:{funding}")
            if not funding_match:
                reasons.append(f"funding_mismatch:{funding}")
        if revenue:
            evidence.append(f"revenue:{revenue}")
            if not revenue_match:
                reasons.append(f"revenue_mismatch:{revenue}")

        if passed:
            reasons = ["passed_target_account_filter"]

        return FilterMatch(
            passed=passed,
            country_match=country_match,
            size_match=size_match,
            industry_match=industry_match,
            funding_match=funding_match,
            revenue_match=revenue_match,
            matched_country=country if country_match else None,
            matched_size=size if size_match else None,
            matched_industry=industry if industry_match else None,
            matched_funding=funding if funding_match else None,
            matched_revenue=revenue if revenue_match else None,
            reasons=reasons,
            evidence=evidence,
        )
