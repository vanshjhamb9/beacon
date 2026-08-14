from __future__ import annotations

from revenue_hunter.models.types import CompanySizeBand, FilterCriteria, FundingStage, RevenueBand


TARGET_COUNTRIES: tuple[str, ...] = (
    "USA",
    "Canada",
    "UK",
    "Australia",
    "Germany",
    "Singapore",
    "UAE",
    "Saudi Arabia",
    "India",
)

# Canonical aliases → display country
COUNTRY_ALIASES: dict[str, str] = {
    "usa": "USA",
    "us": "USA",
    "united states": "USA",
    "united states of america": "USA",
    "america": "USA",
    "canada": "Canada",
    "uk": "UK",
    "united kingdom": "UK",
    "great britain": "UK",
    "england": "UK",
    "australia": "Australia",
    "au": "Australia",
    "germany": "Germany",
    "de": "Germany",
    "singapore": "Singapore",
    "sg": "Singapore",
    "uae": "UAE",
    "united arab emirates": "UAE",
    "dubai": "UAE",
    "saudi arabia": "Saudi Arabia",
    "ksa": "Saudi Arabia",
    "saudi": "Saudi Arabia",
    "india": "India",
    "in": "India",
}

TARGET_INDUSTRIES: tuple[str, ...] = (
    "SaaS",
    "Ecommerce",
    "Healthcare",
    "Fintech",
    "Manufacturing",
    "Logistics",
    "Education",
    "Real Estate",
    "Construction",
    "Legal",
    "Marketing",
    "Technology",
)

INDUSTRY_ALIASES: dict[str, str] = {
    "saas": "SaaS",
    "software": "SaaS",
    "software as a service": "SaaS",
    "ecommerce": "Ecommerce",
    "e-commerce": "Ecommerce",
    "e commerce": "Ecommerce",
    "retail": "Ecommerce",
    "dtc": "Ecommerce",
    "d2c": "Ecommerce",
    "healthcare": "Healthcare",
    "health": "Healthcare",
    "health tech": "Healthcare",
    "fintech": "Fintech",
    "finance": "Fintech",
    "financial services": "Fintech",
    "banking": "Fintech",
    "manufacturing": "Manufacturing",
    "industrial": "Manufacturing",
    "logistics": "Logistics",
    "supply chain": "Logistics",
    "education": "Education",
    "edtech": "Education",
    "real estate": "Real Estate",
    "proptech": "Real Estate",
    "construction": "Construction",
    "legal": "Legal",
    "law": "Legal",
    "marketing": "Marketing",
    "agency": "Marketing",
    "advertising": "Marketing",
    "technology": "Technology",
    "tech": "Technology",
    "it": "Technology",
}

COMPANY_SIZE_BANDS: tuple[str, ...] = tuple(b.value for b in CompanySizeBand)
FUNDING_STAGES: tuple[str, ...] = tuple(s.value for s in FundingStage)
REVENUE_BANDS: tuple[str, ...] = tuple(r.value for r in RevenueBand)

FUNDING_ALIASES: dict[str, str] = {
    "bootstrapped": "Bootstrapped",
    "bootstrap": "Bootstrapped",
    "self-funded": "Bootstrapped",
    "seed": "Seed",
    "pre-seed": "Seed",
    "preseed": "Seed",
    "series a": "Series A",
    "series_a": "Series A",
    "series-a": "Series A",
    "series b": "Series B",
    "series_b": "Series B",
    "series-b": "Series B",
    "series c": "Series C",
    "series_c": "Series C",
    "series-c": "Series C",
    "series d": "Series C",
    "public": "Public",
    "ipo": "Public",
    "listed": "Public",
}

REVENUE_ALIASES: dict[str, str] = {
    "startup": "Startup",
    "early stage": "Startup",
    "smb": "SMB",
    "small business": "SMB",
    "sme": "SMB",
    "mid market": "Mid Market",
    "mid-market": "Mid Market",
    "midmarket": "Mid Market",
    "enterprise": "Enterprise",
}


def normalize_country(value: str | None) -> str | None:
    if not value:
        return None
    return COUNTRY_ALIASES.get(value.strip().lower(), value.strip())


def normalize_industry(value: str | None) -> str | None:
    if not value:
        return None
    return INDUSTRY_ALIASES.get(value.strip().lower(), value.strip())


def normalize_funding(value: str | None) -> str | None:
    if not value:
        return None
    return FUNDING_ALIASES.get(value.strip().lower(), value.strip())


def normalize_revenue(value: str | None) -> str | None:
    if not value:
        return None
    return REVENUE_ALIASES.get(value.strip().lower(), value.strip())


def size_band_from_employees(count: int | None) -> str | None:
    if count is None:
        return None
    if count < 10:
        return None
    if count <= 25:
        return CompanySizeBand.S_10_25.value
    if count <= 50:
        return CompanySizeBand.S_25_50.value
    if count <= 100:
        return CompanySizeBand.S_50_100.value
    if count <= 250:
        return CompanySizeBand.S_100_250.value
    if count <= 500:
        return CompanySizeBand.S_250_500.value
    return CompanySizeBand.S_500_PLUS.value


def default_filter_criteria() -> FilterCriteria:
    """Agency default ICP — all supported countries/sizes/industries/funding/revenue."""
    return FilterCriteria(
        countries=list(TARGET_COUNTRIES),
        company_sizes=list(COMPANY_SIZE_BANDS),
        industries=list(TARGET_INDUSTRIES),
        funding_stages=list(FUNDING_STAGES),
        revenue_bands=list(REVENUE_BANDS),
    )
