"""Revenue Intelligence Pipeline - Orchestrates all engines into a single analysis."""

from __future__ import annotations

import logging

from packages.revenue_intelligence.models import CompanyIntelligence
from packages.revenue_intelligence.engines.icp_engine import match_icp
from packages.revenue_intelligence.engines.pain_engine import detect_pain
from packages.revenue_intelligence.engines.growth_engine import detect_growth
from packages.revenue_intelligence.engines.technology_gap import detect_technology_gap
from packages.revenue_intelligence.engines.support_gap import detect_support_gap
from packages.revenue_intelligence.engines.buying_intent import detect_buying_intent
from packages.revenue_intelligence.engines.traffic_signals import detect_traffic_signals
from packages.revenue_intelligence.engines.revenue_probability import calculate_probability
from packages.revenue_intelligence.engines.priority_engine import classify_priority
from packages.revenue_intelligence.engines.company_summary import generate_summary
from packages.revenue_intelligence.analysis.whatsapp_analysis import detect_whatsapp_signals
from packages.revenue_intelligence.analysis.social_growth import detect_social_growth
from packages.revenue_intelligence.analysis.review_analysis import detect_review_signals
from packages.revenue_intelligence.analysis.founder_activity import detect_founder_signals

logger = logging.getLogger(__name__)


class RevenueIntelligencePipeline:
    """Orchestrate all revenue intelligence engines into a single analysis.

    Pipeline order:
        1. ICP Match (reject enterprise early)
        2. Pain Detection
        3. Growth Detection
        4. Technology Gap
        5. Support Gap
        6. Traffic Signals
        7. Buying Intent
        8. Social Growth
        9. Review Analysis
        10. WhatsApp Analysis
        11. Founder Activity
        12. Revenue Probability
        13. Priority Classification
        14. Company Summary (why_comai, pitch, revenue_potential)
    """

    def analyze(self, lead_data: dict) -> CompanyIntelligence:
        """Run full revenue intelligence analysis on a single lead."""
        intel = CompanyIntelligence(
            company_name=lead_data.get("company_name", ""),
            website=lead_data.get("website", ""),
            domain=lead_data.get("domain", ""),
            platform=lead_data.get("platform", ""),
            category=lead_data.get("category", ""),
            product_count=lead_data.get("product_count", 0),
            country=lead_data.get("country", "India"),
        )

        # Step 1: ICP Match (reject enterprise early)
        intel = match_icp(intel, lead_data)

        # If rejected, skip expensive analysis
        if not intel.icp_match:
            intel.priority = "REJECT"
            intel.probability_to_buy = 0.0
            intel.evidence.append({
                "category": "pipeline",
                "signal": "icp_rejected",
                "summary": f"Rejected: {'; '.join(intel.rejection_reasons[:2])}",
                "score_impact": 0.0,
            })
            return intel

        # Step 2: Pain Detection
        intel = detect_pain(intel, lead_data)

        # Step 3: Growth Detection
        intel = detect_growth(intel, lead_data)

        # Step 4: Technology Gap
        intel = detect_technology_gap(intel, lead_data)

        # Step 5: Support Gap
        intel = detect_support_gap(intel, lead_data)

        # Step 6: Traffic Signals
        intel = detect_traffic_signals(intel, lead_data)

        # Step 7: Buying Intent (depends on pain + growth)
        intel = detect_buying_intent(intel, lead_data, intel.pain_score, intel.growth_score)

        # Step 8: Social Growth
        intel = detect_social_growth(intel, lead_data)

        # Step 9: Review Analysis
        intel = detect_review_signals(intel, lead_data)

        # Step 10: WhatsApp Analysis
        intel = detect_whatsapp_signals(intel, lead_data)

        # Step 11: Founder Activity
        intel = detect_founder_signals(intel, lead_data)

        # Step 12: Revenue Probability (depends on all prior scores)
        intel = calculate_probability(intel, lead_data)

        # Step 13: Priority Classification
        intel = classify_priority(intel)

        # Step 14: Company Summary
        intel = generate_summary(intel, lead_data)

        return intel

    def analyze_many(self, leads: list[dict]) -> list[CompanyIntelligence]:
        """Analyze multiple leads."""
        results: list[CompanyIntelligence] = []
        for lead in leads:
            try:
                intel = self.analyze(lead)
                results.append(intel)
            except Exception as e:
                logger.warning("Analysis failed for %s: %s", lead.get("domain"), e)
        return results
