"""Technology enrichment for ecommerce leads."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from packages.ecommerce_leads.collectors.ecommerce_detector import EcommerceDetector
from packages.ecommerce_leads.models import EnrichedEcommerceLead

logger = logging.getLogger(__name__)


class TechnologyEnricher:
    """Detect ecommerce platform and technology stack."""

    def __init__(self, *, timeout: float = 15.0) -> None:
        self.timeout = timeout
        self._detector = EcommerceDetector(timeout=timeout)

    async def enrich(self, lead: EnrichedEcommerceLead) -> EnrichedEcommerceLead:
        """Enrich technology detection from the website."""
        try:
            result = await self._detector.detect(lead.raw.website)

            lead.shopify_detected = result.get("shopify_detected", False)
            lead.woocommerce_detected = result.get("woocommerce_detected", False)
            lead.magento_detected = result.get("magento_detected", False)
            lead.chatbot_detected = result.get("chatbot_detected", False)
            lead.whatsapp_detected = result.get("whatsapp_detected", False)
            lead.crm_detected = result.get("crm_detected", False)

            if lead.raw.platform == "unknown" or not lead.raw.platform:
                lead.raw.platform = result.get("platform", "unknown")

            lead.raw.metadata["platform_confidence"] = result.get("platform_confidence", 0.0)
            lead.raw.metadata["technology_indicators"] = result.get("indicators", [])

            logger.info(
                "Technology enriched for %s: platform=%s, chatbot=%s, whatsapp=%s",
                lead.raw.website, lead.raw.platform, lead.chatbot_detected, lead.whatsapp_detected,
            )

        except Exception as e:
            logger.warning("Technology enrichment failed for %s: %s", lead.raw.website, e)

        return lead
