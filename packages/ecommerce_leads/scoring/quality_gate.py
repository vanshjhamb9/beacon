"""Quality gate for ecommerce leads - enforces standards before SALES_READY classification."""

from __future__ import annotations

import logging
from packages.ecommerce_leads.models import EnrichedEcommerceLead

logger = logging.getLogger(__name__)


class QualityGate:
    """Enforce quality standards before a lead can be classified as SALES_READY.
    
    A lead CANNOT become SALES_READY unless:
    - Website is live
    - Platform is detected (not "unknown")
    - Technology is detected (at least one boolean true)
    - Phone OR Email available
    - Pain point identified
    - Reason to contact identified
    - Confidence > 70%
    
    Otherwise classify as NEEDS_ENRICHMENT.
    """

    def evaluate(self, lead: EnrichedEcommerceLead) -> EnrichedEcommerceLead:
        """Evaluate lead against quality gate criteria."""
        checks = {
            "website_live": self._check_website_live(lead),
            "platform_detected": self._check_platform_detected(lead),
            "technology_detected": self._check_technology_detected(lead),
            "contact_available": self._check_contact_available(lead),
            "pain_points_exist": self._check_pain_points(lead),
            "sales_reason_exists": self._check_sales_reason(lead),
        }

        # Calculate confidence from the first 6 checks (no circular dependency)
        passed_count = sum(1 for v in checks.values() if v)
        lead.confidence_score = round(passed_count / len(checks) * 100, 1)

        # Now check confidence as 7th gate
        checks["confidence_adequate"] = lead.confidence_score >= 70.0

        passed = all(checks.values())
        lead.quality_gate_passed = passed

        if not passed:
            failed_checks = [k for k, v in checks.items() if not v]
            logger.info(
                "Quality gate FAILED for %s: %s",
                lead.raw.company_name,
                ", ".join(failed_checks),
            )
            # Override priority if quality gate fails
            if lead.lead_priority in ("HOT", "SALES_READY"):
                lead.lead_priority = "NEEDS_ENRICHMENT"
        else:
            logger.info(
                "Quality gate PASSED for %s (confidence: %.1f%%)",
                lead.raw.company_name,
                lead.confidence_score,
            )

        return lead

    def _check_website_live(self, lead: EnrichedEcommerceLead) -> bool:
        """Check if website URL is present and valid."""
        return bool(lead.raw.website and lead.raw.website.startswith("http"))

    def _check_platform_detected(self, lead: EnrichedEcommerceLead) -> bool:
        """Check if platform was detected (not unknown)."""
        return bool(
            lead.raw.platform
            and lead.raw.platform != "unknown"
            and lead.raw.platform != ""
        )

    def _check_technology_detected(self, lead: EnrichedEcommerceLead) -> bool:
        """Check if at least one technology was detected."""
        # Platform detection counts as technology detection
        if lead.raw.platform and lead.raw.platform not in ("unknown", ""):
            return True
        return any([
            lead.shopify_detected,
            lead.woocommerce_detected,
            lead.magento_detected,
            lead.chatbot_detected,
            lead.whatsapp_detected,
            lead.crm_detected,
        ])

    def _check_contact_available(self, lead: EnrichedEcommerceLead) -> bool:
        """Check if phone or email is available."""
        return bool(lead.email or lead.phone)

    def _check_pain_points(self, lead: EnrichedEcommerceLead) -> bool:
        """Check if pain points were identified."""
        return bool(lead.pain_points and len(lead.pain_points) > 0)

    def _check_sales_reason(self, lead: EnrichedEcommerceLead) -> bool:
        """Check if a sales reason was identified."""
        return bool(
            lead.sales_reason
            and lead.sales_reason != "General ecommerce lead"
            and lead.sales_reason != ""
        )

    def _check_confidence(self, lead: EnrichedEcommerceLead) -> bool:
        """Check if confidence score is adequate (>70%)."""
        return lead.confidence_score >= 70.0
