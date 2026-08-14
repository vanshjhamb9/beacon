"""Configurable constants for Opportunity Intelligence."""

from __future__ import annotations

from types import MappingProxyType

from opportunity_intelligence.enums import BuyingWindow, FreshnessBucket, SignalCategory, SourceTier

SCORING_VERSION = "oip-v1"
MINIMUM_EVIDENCE = 2
MAX_SCORE = 100.0
DEFAULT_TRUST = 50.0
DEFAULT_CONFIDENCE = 50.0
DEFAULT_ICP_SCORE = 50.0
DEDUPLICATION_KEY_LIMIT = 191

SCORE_WEIGHTS = MappingProxyType(
    {
        "intent": 0.18,
        "pain": 0.14,
        "budget": 0.14,
        "growth": 0.12,
        "timing": 0.14,
        "freshness": 0.10,
        "evidence": 0.10,
        "icp": 0.08,
    }
)

SIGNAL_FACTOR_BASELINES = MappingProxyType(
    {
        SignalCategory.HIRING: {"intent": 82, "pain": 58, "budget": 62, "growth": 84, "timing": 78},
        SignalCategory.FUNDING: {"intent": 88, "pain": 55, "budget": 94, "growth": 90, "timing": 82},
        SignalCategory.EXPANSION: {"intent": 84, "pain": 60, "budget": 76, "growth": 92, "timing": 84},
        SignalCategory.LEADERSHIP: {"intent": 74, "pain": 70, "budget": 68, "growth": 70, "timing": 76},
        SignalCategory.TECH_STACK: {"intent": 72, "pain": 64, "budget": 58, "growth": 66, "timing": 70},
        SignalCategory.CUSTOMER_PAIN: {"intent": 86, "pain": 94, "budget": 66, "growth": 58, "timing": 86},
        SignalCategory.PRODUCT: {"intent": 76, "pain": 62, "budget": 64, "growth": 78, "timing": 74},
        SignalCategory.PARTNERSHIP: {"intent": 70, "pain": 52, "budget": 66, "growth": 72, "timing": 66},
        SignalCategory.COMPLIANCE: {"intent": 80, "pain": 86, "budget": 72, "growth": 54, "timing": 84},
        SignalCategory.SECURITY: {"intent": 82, "pain": 90, "budget": 76, "growth": 56, "timing": 86},
        SignalCategory.MARKET: {"intent": 68, "pain": 58, "budget": 58, "growth": 72, "timing": 62},
    }
)

FRESHNESS_BUCKETS = (
    (0, 7, 100.0, FreshnessBucket.ZERO_TO_SEVEN),
    (8, 30, 90.0, FreshnessBucket.EIGHT_TO_THIRTY),
    (31, 60, 75.0, FreshnessBucket.THIRTY_ONE_TO_SIXTY),
    (61, 90, 60.0, FreshnessBucket.SIXTY_ONE_TO_NINETY),
    (91, 180, 30.0, FreshnessBucket.NINETY_ONE_TO_ONE_EIGHTY),
    (181, None, 5.0, FreshnessBucket.ONE_EIGHTY_PLUS),
)

BUYING_WINDOW_LIMITS = MappingProxyType(
    {
        BuyingWindow.IMMEDIATE: (0, 30),
        BuyingWindow.WARM: (31, 60),
        BuyingWindow.FUTURE: (61, 90),
        BuyingWindow.DORMANT: (91, None),
    }
)

SIGNAL_REGISTRY_DEFAULTS = MappingProxyType(
    {
        SignalCategory.HIRING: (1, 1.00, 2, 30, BuyingWindow.IMMEDIATE),
        SignalCategory.FUNDING: (1, 1.00, 2, 30, BuyingWindow.IMMEDIATE),
        SignalCategory.EXPANSION: (1, 0.95, 2, 45, BuyingWindow.IMMEDIATE),
        SignalCategory.LEADERSHIP: (2, 0.82, 2, 45, BuyingWindow.WARM),
        SignalCategory.TECH_STACK: (3, 0.70, 2, 60, BuyingWindow.WARM),
        SignalCategory.CUSTOMER_PAIN: (1, 1.00, 2, 30, BuyingWindow.IMMEDIATE),
        SignalCategory.PRODUCT: (2, 0.78, 2, 60, BuyingWindow.WARM),
        SignalCategory.PARTNERSHIP: (3, 0.65, 2, 60, BuyingWindow.FUTURE),
        SignalCategory.COMPLIANCE: (2, 0.86, 2, 45, BuyingWindow.IMMEDIATE),
        SignalCategory.SECURITY: (1, 0.92, 2, 30, BuyingWindow.IMMEDIATE),
        SignalCategory.MARKET: (4, 0.55, 2, 90, BuyingWindow.FUTURE),
    }
)

SOURCE_TIERS = MappingProxyType(
    {
        SourceTier.TIER_1: (
            "LinkedIn",
            "Career Pages",
            "Crunchbase",
            "Google News",
            "Greenhouse",
            "Lever",
            "Ashby",
            "Workday",
        ),
        SourceTier.TIER_2: ("Twitter", "Github", "Reddit", "Product Hunt", "HackerNews"),
        SourceTier.TIER_3: ("RSS", "Blogs", "Press Release", "SEC", "App Store", "Play Store"),
    }
)

SOURCE_TRUST_BY_TIER = MappingProxyType(
    {
        SourceTier.TIER_1: 92.0,
        SourceTier.TIER_2: 74.0,
        SourceTier.TIER_3: 64.0,
    }
)
