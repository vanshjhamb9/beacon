"""Main discovery engine — orchestrates all sources and deduplicates."""

from __future__ import annotations

import logging
from datetime import date

from packages.discovery_engine.base import DiscoverySource
from packages.discovery_engine.models import DiscoveredCompany
from packages.discovery_engine.sources import (
    FundingDiscovery,
    HiringDiscovery,
    NewLaunchDiscovery,
    AcceleratorDiscovery,
    FounderDiscovery,
    MarketingDiscovery,
)
from packages.discovery_engine.sources.reddit_intent import RedditIntentDiscovery
from packages.discovery_engine.sources.producthunt_intent import ProductHuntIntentDiscovery
from packages.discovery_engine.sources.twitter_intent import TwitterIntentDiscovery
from packages.discovery_engine.sources.linkedin_intent import LinkedInIntentDiscovery
from packages.discovery_engine.sources.upwork_intent import UpworkIntentDiscovery
from packages.discovery_engine.sources.startup_community import StartupCommunityDiscovery
from packages.discovery_engine.sources.cyber_intent import CyberIntentDiscovery

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """Orchestrates multiple discovery sources, deduplicates, and outputs companies."""

    def __init__(self) -> None:
        self.sources: list[DiscoverySource] = [
            # Intent-first sources (CTO directive)
            RedditIntentDiscovery(),
            TwitterIntentDiscovery(),
            LinkedInIntentDiscovery(),
            ProductHuntIntentDiscovery(),
            UpworkIntentDiscovery(),
            StartupCommunityDiscovery(),
            CyberIntentDiscovery(),
            # Legacy sources
            FundingDiscovery(),
            HiringDiscovery(),
            NewLaunchDiscovery(),
            AcceleratorDiscovery(),
            FounderDiscovery(),
            MarketingDiscovery(),
        ]

    async def discover(
        self,
        limit: int = 30,
        min_per_source: int = 3,
    ) -> list[DiscoveredCompany]:
        """Run all discovery sources and return deduplicated companies.

        Args:
            limit: Total companies to return.
            min_per_source: Minimum companies to try to get from each source.

        Returns:
            Deduplicated list of DiscoveredCompany.
        """
        all_companies: list[DiscoveredCompany] = []
        seen_names: set[str] = set()
        seen_domains: set[str] = set()

        for source in self.sources:
            logger.info("Running source: %s", source.name)
            try:
                # Request more than min_per_source to allow for deduplication
                raw = await source.discover(limit=max(min_per_source * 3, 20))
                added = 0
                for company in raw:
                    if added >= limit:
                        break

                    name_key = company.company_name.lower().strip()
                    domain_key = company.domain.lower().strip()

                    # Skip if already seen (by name or domain)
                    if name_key in seen_names or domain_key in seen_domains:
                        continue

                    # Skip REJECT-worthy companies
                    if self._should_reject(company):
                        continue

                    seen_names.add(name_key)
                    seen_domains.add(domain_key)
                    all_companies.append(company)
                    added += 1

                logger.info(
                    "  Source %s: %d raw → %d added (total: %d)",
                    source.name, len(raw), added, len(all_companies),
                )
            except Exception as e:
                logger.error("  Source %s failed: %s", source.name, e)

        # Sort by discovery date (most recent first), then by source priority
        source_priority = {
            "reddit_intent": 0,
            "twitter_intent": 1,
            "linkedin_intent": 2,
            "producthunt_intent": 3,
            "upwork_intent": 4,
            "startup_community": 5,
            "funding_announcements": 6,
            "hiring_signals": 7,
            "new_launches": 8,
            "founder_activity": 9,
            "accelerator_incubator": 10,
            "marketing_activity": 11,
        }
        all_companies.sort(
            key=lambda c: (
                source_priority.get(c.source, 99),
                c.company_name,
            )
        )

        return all_companies[:limit]

    def _should_reject(self, company: DiscoveredCompany) -> bool:
        """Check if company should be immediately rejected."""
        name_lower = company.company_name.lower()

        # Reject known enterprise/large companies
        enterprise_names = [
            "tata", "reliance", "aditya birla", "godrej", "itc", "hul",
            "hindustan unilever", "procter", "gamble", "nestle", "unilever",
            "amazon", "flipkart", "meesho", "jio", "airtel", "bharti",
            "mahindra", "bajaj", "hero", "maruti", "hyundai", "kia",
            "ola", "uber", "swiggy", "zomato", "paytm", "phonepe",
            "razorpay", "cred", "nykaa", "firstcry",
        ]
        for ent in enterprise_names:
            if ent in name_lower:
                return True

        # Reject if domain suggests a marketplace
        marketplace_domains = [
            "amazon.", "flipkart.", "meesho.", "myntra.", "ajio.",
            "snapdeal.", "paytm.", "ebay.",
        ]
        for mkt in marketplace_domains:
            if mkt in company.domain:
                return True

        return False
