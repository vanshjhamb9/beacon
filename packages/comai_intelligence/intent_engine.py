"""Buying Intent Engine — Detects signals that decay over time.

Every signal should decay over time.
Fresh signals weigh more than stale signals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class IntentSignal:
    """Single detected buying intent signal."""

    signal_type: str
    description: str
    confidence: float  # 0-1
    evidence: list[str]
    source: str
    detected_at: datetime
    decay_rate: float  # Per day, 0-1
    weight: float  # 0-1, importance of this signal
    raw_data: dict[str, Any] = field(default_factory=dict)

    @property
    def age_days(self) -> int:
        """Age of signal in days."""
        now = datetime.now(timezone.utc)
        return max(0, (now - self.detected_at).days)

    @property
    def current_strength(self) -> float:
        """Signal strength after decay. 0-1."""
        decayed = self.confidence * (1.0 - self.decay_rate * self.age_days)
        return max(0.0, min(decayed, self.confidence))

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_type": self.signal_type,
            "description": self.description,
            "confidence": round(self.confidence, 3),
            "current_strength": round(self.current_strength, 3),
            "age_days": self.age_days,
            "evidence": self.evidence,
            "source": self.source,
            "detected_at": self.detected_at.isoformat(),
            "weight": self.weight,
        }


class BuyingIntentEngine:
    """Detects buying signals that decay over time.

    Signal types and their decay rates:
    - hiring: Decay fast (job posts expire)
    - expansion: Decay moderate
    - funding: Decay slow (funding matters for months)
    - traffic_growth: Decay moderate
    - website_redesign: Decay fast
    - marketing_expansion: Decay moderate
    - crm_migration: Decay moderate
    - technology_migration: Decay moderate
    """

    INTENT_DEFINITIONS: dict[str, dict[str, Any]] = {
        "hiring": {
            "description": "Company is hiring for ecommerce-relevant roles",
            "keywords": [
                "ecommerce manager", "shopify developer", "digital marketing",
                "customer support", "operations manager", "growth manager",
                "performance marketing", "brand manager", "content manager",
                "social media manager", "ui ux designer", "frontend developer",
            ],
            "decay_rate": 0.05,
            "weight": 0.9,
        },
        "expansion": {
            "description": "Company is expanding products, markets, or operations",
            "indicators": [
                "new_product_collections",
                "new_country_launch",
                "new_store_location",
                "international_shipping",
                "new_category_launch",
                "warehouse_expansion",
            ],
            "decay_rate": 0.03,
            "weight": 0.8,
        },
        "funding": {
            "description": "Company has received recent funding",
            "sources": ["tracxn", "yourstory", "press_releases", "crunchbase"],
            "decay_rate": 0.02,
            "weight": 0.95,
        },
        "traffic_growth": {
            "description": "Website traffic is growing",
            "indicators": [
                "alexa_rank_improvement",
                "similarweb_growth",
                "social_media_growth",
                "search_visibility_growth",
            ],
            "decay_rate": 0.04,
            "weight": 0.7,
        },
        "website_redesign": {
            "description": "Company recently redesigned or updated website",
            "indicators": [
                "recent_theme_change",
                "new_design",
                "updated_meta_tags",
                "new_checkout_flow",
            ],
            "decay_rate": 0.06,
            "weight": 0.6,
        },
        "marketing_expansion": {
            "description": "Company is expanding marketing efforts",
            "indicators": [
                "new_ad_campaigns",
                "increased_social_activity",
                "new_influencer_partnerships",
                "new_content_strategy",
                "increased_ad_spend_signals",
            ],
            "decay_rate": 0.04,
            "weight": 0.65,
        },
        "crm_migration": {
            "description": "Company is migrating or upgrading CRM/support tools",
            "indicators": [
                "new_chatbot_detected",
                "crm_change",
                "new_support_tool",
                "new_email_platform",
            ],
            "decay_rate": 0.03,
            "weight": 0.85,
        },
        "technology_migration": {
            "description": "Company is upgrading technology stack",
            "indicators": [
                "platform_change",
                "new_analytics",
                "new_payment_gateway",
                "new_theme_installed",
                "cdn_change",
            ],
            "decay_rate": 0.04,
            "weight": 0.7,
        },
        "competitor_frustration": {
            "description": "Company may be frustrated with existing tools",
            "indicators": [
                "bad_reviews_of_current_tool",
                "looking_for_alternatives",
                "complaints_on_social",
            ],
            "decay_rate": 0.03,
            "weight": 0.9,
        },
        "seasonal_preparation": {
            "description": "Company preparing for peak season (Diwali, festive, etc.)",
            "indicators": [
                "festive_collection_launch",
                "sale_preparation",
                "inventory_buildup",
                "marketing_ramp_up",
            ],
            "decay_rate": 0.07,
            "weight": 0.75,
        },
    }

    def detect_signals(self, company: dict[str, Any]) -> list[IntentSignal]:
        """Detect all buying intent signals for a company.

        Args:
            company: Company data with observable attributes.

        Returns:
            List of IntentSignal objects, sorted by current strength.
        """
        signals: list[IntentSignal] = []

        for signal_type, definition in self.INTENT_DEFINITIONS.items():
            indicators = definition.get("indicators", [])
            keywords = definition.get("keywords", [])
            matched: list[str] = []

            # Check keywords in job postings, description, etc.
            if keywords:
                job_text = " ".join([
                    company.get("job_postings", ""),
                    company.get("description", ""),
                    company.get("hiring_text", ""),
                ]).lower()
                for kw in keywords:
                    if kw.lower() in job_text:
                        matched.append(f"Keyword found: {kw}")

            # Check indicators
            for indicator in indicators:
                if company.get(indicator):
                    matched.append(f"Indicator present: {indicator}")
                elif self._check_indicator(indicator, company):
                    matched.append(f"Indicator detected: {indicator}")

            # Check sources
            for source_name in definition.get("sources", []):
                if company.get(f"found_on_{source_name}"):
                    matched.append(f"Found on: {source_name}")

            if matched:
                confidence = min(len(matched) * 0.3, 1.0)
                detected_at_str = company.get(f"{signal_type}_detected_at")
                if detected_at_str:
                    try:
                        detected_at = datetime.fromisoformat(detected_at_str)
                    except (ValueError, TypeError):
                        detected_at = datetime.now(timezone.utc)
                else:
                    detected_at = datetime.now(timezone.utc)

                signals.append(IntentSignal(
                    signal_type=signal_type,
                    description=definition["description"],
                    confidence=confidence,
                    evidence=matched,
                    source="buying_intent_engine",
                    detected_at=detected_at,
                    decay_rate=definition["decay_rate"],
                    weight=definition["weight"],
                ))

        # Sort by current strength (highest first)
        signals.sort(key=lambda s: s.current_strength, reverse=True)
        return signals

    def _check_indicator(self, indicator: str, company: dict[str, Any]) -> bool:
        """Check if an intent indicator is present."""
        if indicator == "new_product_collections":
            recent = company.get("recent_collections") or 0
            return recent > 0

        if indicator == "new_country_launch":
            return bool(company.get("new_country_launch"))

        if indicator == "international_shipping":
            return bool(company.get("international_shipping"))

        if indicator == "new_category_launch":
            return bool(company.get("new_category"))

        if indicator == "warehouse_expansion":
            return bool(company.get("warehouse_expansion"))

        if indicator == "new_chatbot_detected":
            return bool(company.get("new_chatbot"))

        if indicator == "crm_change":
            return bool(company.get("crm_change"))

        if indicator == "new_support_tool":
            return bool(company.get("new_support_tool"))

        if indicator == "new_email_platform":
            return bool(company.get("new_email_platform"))

        if indicator == "platform_change":
            return bool(company.get("platform_changed"))

        if indicator == "new_analytics":
            return bool(company.get("new_analytics"))

        if indicator == "new_payment_gateway":
            return bool(company.get("new_payment_gateway"))

        if indicator == "new_theme_installed":
            return bool(company.get("theme_changed"))

        if indicator == "new_ad_campaigns":
            return bool(company.get("active_ad_campaigns"))

        if indicator == "increased_social_activity":
            return bool(company.get("social_growth"))

        if indicator == "new_influencer_partnerships":
            return bool(company.get("influencer_partnerships"))

        if indicator == "bad_reviews_of_current_tool":
            return bool(company.get("tool_complaints"))

        if indicator == "festive_collection_launch":
            return bool(company.get("festive_launch"))

        if indicator == "sale_preparation":
            return bool(company.get("sale_prep"))

        if indicator == "inventory_buildup":
            return bool(company.get("inventory_increase"))

        if indicator == "marketing_ramp_up":
            return bool(company.get("marketing_increase"))

        return False

    def calculate_intent_score(self, signals: list[IntentSignal]) -> float:
        """Score overall buying intent 0-100 with decay applied."""
        if not signals:
            return 0.0

        total = sum(
            s.current_strength * s.weight * 100.0 for s in signals
        )
        return min(total, 100.0)

    def top_signals(self, signals: list[IntentSignal], limit: int = 3) -> list[IntentSignal]:
        """Return top N intent signals by current strength."""
        return signals[:limit]

    def intent_summary(self, signals: list[IntentSignal]) -> str:
        """Generate human-readable intent summary."""
        if not signals:
            return "No buying intent signals detected."
        top = self.top_signals(signals, 3)
        summaries = [s.signal_type.replace("_", " ") for s in top]
        return f"Intent signals: {', '.join(summaries)}"
