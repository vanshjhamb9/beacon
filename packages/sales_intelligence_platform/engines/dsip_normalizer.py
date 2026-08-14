"""DSIP: Normalization Engine.

Normalizes all extracted data to consistent formats.
Prevents inconsistent values across sources.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Country code mappings
COUNTRY_NAMES = {
    "india": "IN", "in": "IN", "bharat": "IN",
    "united states": "US", "usa": "US", "us": "US", "united states of america": "US",
    "united kingdom": "GB", "uk": "GB", "gb": "GB", "great britain": "GB",
    "uae": "AE", "united arab emirates": "AE", "ae": "AE", "dubai": "AE",
    "singapore": "SG", "sg": "SG",
    "australia": "AU", "au": "AU",
    "canada": "CA", "ca": "CA",
    "germany": "DE", "de": "DE",
    "france": "FR", "fr": "FR",
    "japan": "JP", "jp": "JP",
    "china": "CN", "cn": "CN",
}

# Industry mappings
INDUSTRY_SYNONYMS = {
    "beauty": ["beauty", "cosmetics", "skincare", "personal care", "beauty products"],
    "fashion": ["fashion", "apparel", "clothing", "wear", "fashion accessories"],
    "electronics": ["electronics", "gadgets", "tech products", "electronic devices"],
    "food": ["food", "beverages", "organic food", "health food", "snacks"],
    "home": ["home decor", "furniture", "home goods", "kitchen", "household"],
    "health": ["health", "wellness", "supplements", "fitness", "health products"],
    "pet": ["pet", "pet care", "pet food", "pet products", "animal care"],
    "jewelry": ["jewelry", "jewellery", "accessories", "fashion jewelry", "luxury jewelry"],
    "kids": ["kids", "baby", "maternity", "children", "infant"],
}

# Platform detection patterns
PLATFORM_PATTERNS = {
    "shopify": [r"\.myshopify\.com", r"cdn\.shopify\.com", r"Shopify\.theme"],
    "woocommerce": [r"woocommerce", r"wp-content/plugins/woocommerce"],
    "magento": [r"magento", r"Mage\.Cookies"],
    "bigcommerce": [r"bigcommerce", r"BigCommerce"],
    "squarespace": [r"squarespace\.com", r"Squarespace"],
    "wix": [r"wix\.com", r"Wix"],
}


class DataNormalizer:
    """Normalizes all extracted data to consistent formats."""

    def normalize_company(self, company: dict) -> dict:
        """Normalize a company record."""
        normalized = {}

        # Normalize name
        normalized["company_name"] = self.normalize_company_name(
            company.get("company_name", "")
        )

        # Normalize domain
        normalized["primary_domain"] = self.normalize_domain(
            company.get("primary_domain", "") or company.get("website", "")
        )

        # Normalize website
        normalized["website"] = self.normalize_url(
            company.get("website", "")
        )

        # Normalize country
        normalized["country"] = self.normalize_country(
            company.get("country", "")
        )

        # Normalize industry
        normalized["industry"] = self.normalize_industry(
            company.get("industry", "")
        )

        # Normalize platform
        normalized["platform"] = self.normalize_platform(
            company.get("platform", "")
        )

        # Normalize emails
        normalized["emails"] = [
            self.normalize_email(e) for e in company.get("emails", [])
        ]

        # Normalize phones
        normalized["phones"] = [
            self.normalize_phone(p, company.get("country", "")) for p in company.get("phones", [])
        ]

        # Normalize URLs
        normalized["social_profiles"] = {
            k: self.normalize_url(v)
            for k, v in company.get("social_profiles", {}).items()
            if v
        }

        return normalized

    def normalize_company_name(self, name: str) -> str:
        """Normalize company name."""
        if not name:
            return ""

        # Remove extra whitespace
        name = re.sub(r"\s+", " ", name.strip())

        # Remove common suffixes
        suffixes = [
            " pvt ltd", " private limited", " ltd", " limited",
            " llp", " inc", " corp", " corporation",
            " llc", " co", " company",
        ]
        name_lower = name.lower()
        for suffix in suffixes:
            if name_lower.endswith(suffix):
                name = name[: -len(suffix)].strip()
                name_lower = name.lower()

        # Title case
        name = name.title()

        return name

    def normalize_domain(self, domain: str) -> str:
        """Normalize a domain."""
        if not domain:
            return ""

        # Add scheme if missing
        if not domain.startswith(("http://", "https://")):
            domain = "https://" + domain

        try:
            parsed = urlparse(domain)
            domain = parsed.netloc or parsed.path
        except Exception:
            pass

        # Remove www.
        domain = domain.lower().replace("www.", "")

        # Remove trailing slash
        domain = domain.rstrip("/")

        # Remove port
        domain = domain.split(":")[0]

        return domain

    def normalize_url(self, url: str) -> str:
        """Normalize a URL."""
        if not url:
            return ""

        # Add scheme if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            parsed = urlparse(url)
            # Reconstruct without fragment
            url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                url += f"?{parsed.query}"
        except Exception:
            pass

        return url.lower()

    def normalize_country(self, country: str) -> str:
        """Normalize country to ISO code."""
        if not country:
            return ""

        country_lower = country.strip().lower()

        # Direct lookup
        if country_lower in COUNTRY_NAMES:
            return COUNTRY_NAMES[country_lower]

        # Check if already a valid code
        if country.upper() in COUNTRY_NAMES.values():
            return country.upper()

        return country.upper()[:2] if len(country) >= 2 else country.upper()

    def normalize_industry(self, industry: str) -> str:
        """Normalize industry to canonical form."""
        if not industry:
            return ""

        industry_lower = industry.strip().lower()

        # Check synonyms
        for canonical, synonyms in INDUSTRY_SYNONYMS.items():
            if industry_lower in synonyms or any(s in industry_lower for s in synonyms):
                return canonical

        return industry_lower

    def normalize_platform(self, platform: str) -> str:
        """Normalize platform name."""
        if not platform:
            return ""

        platform_lower = platform.strip().lower()

        # Direct match
        known_platforms = ["shopify", "woocommerce", "magento", "bigcommerce", "squarespace", "wix"]
        for p in known_platforms:
            if p in platform_lower:
                return p

        return platform_lower

    def normalize_email(self, email_data: dict | str) -> dict:
        """Normalize email."""
        if isinstance(email_data, str):
            email_data = {"email": email_data}

        email = email_data.get("email", "").strip().lower()

        # Basic email validation
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        is_valid = bool(re.match(email_regex, email))

        # Check for third-party domains
        third_party_domains = [
            "sentry.io", "shopify.com", "google.com", "facebook.com",
            "instagram.com", "twitter.com", "linkedin.com",
        ]
        domain = email.split("@")[1] if "@" in email else ""
        is_third_party = domain in third_party_domains

        return {
            "email": email if is_valid else "",
            "type": email_data.get("type", "unknown"),
            "confidence": email_data.get("confidence", 0.5 if is_valid else 0.0),
            "is_valid": is_valid,
            "is_third_party": is_third_party,
        }

    def normalize_phone(self, phone_data: dict | str, country: str = "") -> dict:
        """Normalize phone number."""
        if isinstance(phone_data, str):
            phone_data = {"phone": phone_data}

        phone = phone_data.get("phone", "").strip()

        # Remove non-numeric characters except +
        phone_clean = re.sub(r"[^\d+]", "", phone)

        # Add country code if missing
        if country and not phone_clean.startswith("+"):
            country_code = COUNTRY_NAMES.get(country.lower(), "")
            if country_code and not phone_clean.startswith(country_code):
                phone_clean = f"+{country_code}{phone_clean}"

        return {
            "phone": phone_clean,
            "type": phone_data.get("type", "unknown"),
            "confidence": phone_data.get("confidence", 0.5),
            "original": phone,
        }

    def detect_platform_from_html(self, html_content: str) -> str:
        """Detect platform from HTML content."""
        if not html_content:
            return ""

        html_lower = html_content.lower()

        for platform, patterns in PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, html_lower, re.IGNORECASE):
                    return platform

        return ""

    def normalize_all(self, companies: list[dict]) -> list[dict]:
        """Normalize a list of companies."""
        return [self.normalize_company(c) for c in companies]
