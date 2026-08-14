"""Lead Intelligence Explorer (LIX v1) — explainable lead lifecycle observability.

No GPT. No AI. No new scoring engine. Append-only history only.
"""

from __future__ import annotations

from lead_intelligence.lead_quality_scorer import LeadQualityScorer

SCORING_VERSION = "lix-v2"

PROVIDER_CATALOG: tuple[str, ...] = (
    "hunter",
    "apollo",
    "linkedin",
    "people_data_labs",
    "clearbit",
    "crunchbase",
    "builtwith",
    "wappalyzer",
    "google_maps",
    "meta",
    "opencorporates",
    "github",
    "product_hunt",
    "yc",
    "website",
    "rss",
    "hacker_news",
    "reddit",
    "devto",
    "sec_edgar",
    "identity_graph",
    "internal",
)

PIPELINE_STAGES: tuple[str, ...] = (
    "signal",
    "identity",
    "website",
    "company",
    "enrichment",
    "email",
    "decision_maker",
    "sales_ready",
    "revenue_ready",
)

__all__ = ["SCORING_VERSION", "PROVIDER_CATALOG", "PIPELINE_STAGES", "LeadQualityScorer"]
