from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.core.config import Settings
from app.models.ecommerce_leads import EcommerceLeadRow
from app.models.revenue_intelligence import RevenueIntelligenceRow
from app.repositories.ecommerce_leads import EcommerceLeadRepository
from app.repositories.revenue_intelligence import RevenueIntelligenceRepository
from packages.revenue_intelligence.services.pipeline import RevenueIntelligencePipeline

logger = logging.getLogger(__name__)


class RevenueIntelligenceService:
    """Service layer for revenue intelligence operations."""

    def __init__(
        self,
        ri_repo: RevenueIntelligenceRepository,
        lead_repo: EcommerceLeadRepository,
        *,
        settings: Settings | None = None,
    ) -> None:
        self.ri_repo = ri_repo
        self.lead_repo = lead_repo
        self.settings = settings
        self.pipeline = RevenueIntelligencePipeline()

    async def list_leads(
        self,
        *,
        priority: str | None = None,
        icp_match: bool | None = None,
        min_probability: float | None = None,
        platform: str | None = None,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        leads, total = await self.ri_repo.list_with_filters(
            priority=priority, icp_match=icp_match, min_probability=min_probability,
            platform=platform, category=category, limit=limit, offset=offset,
        )
        return {"leads": leads, "total": total, "page": offset // limit + 1, "page_size": limit}

    async def get_lead(self, lead_id: UUID) -> RevenueIntelligenceRow | None:
        return await self.ri_repo.get(lead_id)

    async def get_dashboard(self) -> dict[str, Any]:
        return await self.ri_repo.get_dashboard_stats()

    async def get_top_buyers(self, limit: int = 10) -> list[dict]:
        leads, _ = await self.ri_repo.list_with_filters(
            icp_match=True, min_probability=30.0, limit=limit
        )
        return [
            {"company_name": l.company_name, "domain": l.domain, "probability": l.probability_to_buy, "priority": l.priority}
            for l in leads
        ]

    async def get_highest_pain(self, limit: int = 10) -> list[dict]:
        all_leads, _ = await self.ri_repo.list_with_filters(icp_match=True, limit=500)
        sorted_leads = sorted(all_leads, key=lambda l: l.pain_score, reverse=True)[:limit]
        return [
            {"company_name": l.company_name, "domain": l.domain, "pain_score": l.pain_score, "pain_signals": l.pain_signals[:3]}
            for l in sorted_leads
        ]

    async def get_highest_growth(self, limit: int = 10) -> list[dict]:
        all_leads, _ = await self.ri_repo.list_with_filters(icp_match=True, limit=500)
        sorted_leads = sorted(all_leads, key=lambda l: l.growth_score, reverse=True)[:limit]
        return [
            {"company_name": l.company_name, "domain": l.domain, "growth_score": l.growth_score, "growth_signals": l.growth_signals[:3]}
            for l in sorted_leads
        ]

    async def get_highest_probability(self, limit: int = 10) -> list[dict]:
        leads, _ = await self.ri_repo.list_with_filters(icp_match=True, limit=limit)
        return [
            {"company_name": l.company_name, "domain": l.domain, "probability_to_buy": l.probability_to_buy, "why_comai": l.why_comai}
            for l in leads
        ]

    async def analyze_leads(self, *, limit: int = 500, country: str = "India") -> dict[str, Any]:
        """Run the full revenue intelligence pipeline on ecommerce leads."""
        leads, total = await self.lead_repo.list_with_filters(limit=limit, offset=0) if hasattr(self.lead_repo, 'list_with_filters') else ([], 0)

        processed = 0
        for lead in leads:
            try:
                lead_data = {
                    "id": str(lead.id),
                    "company_name": lead.company_name,
                    "website": lead.website,
                    "domain": lead.domain,
                    "platform": lead.platform,
                    "category": lead.category,
                    "country": lead.country,
                    "product_count": lead.product_count,
                    "shopify_detected": lead.shopify_detected,
                    "woocommerce_detected": lead.woocommerce_detected,
                    "chatbot_detected": lead.chatbot_detected,
                    "whatsapp_detected": lead.whatsapp_detected,
                    "crm_detected": lead.crm_detected,
                    "founder_name": lead.founder_name,
                    "owner_name": lead.owner_name,
                    "email": lead.email,
                    "phone": lead.phone,
                    "linkedin_url": lead.linkedin_url,
                    "social_links": lead.social_links or {},
                }

                intel = self.pipeline.analyze(lead_data)
                intel_dict = intel.to_dict()

                store_data = {
                    "ecommerce_lead_id": str(lead.id),
                    "company_name": intel_dict["company_name"],
                    "website": intel_dict["website"],
                    "domain": intel_dict["domain"],
                    "platform": intel_dict["platform"],
                    "category": intel_dict["category"],
                    "country": intel_dict["country"],
                    "pain_score": intel_dict["pain_score"],
                    "pain_signals": intel_dict["pain_signals"],
                    "growth_score": intel_dict["growth_score"],
                    "growth_signals": intel_dict["growth_signals"],
                    "buying_intent": intel_dict["buying_intent"],
                    "intent_signals": intel_dict["intent_signals"],
                    "technology_gap": intel_dict["technology_gap"],
                    "tech_gaps": intel_dict["tech_gaps"],
                    "support_gap": intel_dict["support_gap"],
                    "support_gaps": intel_dict["support_gaps"],
                    "icp_match": intel_dict["icp_match"],
                    "icp_score": intel_dict["icp_score"],
                    "icp_reasons": intel_dict["icp_reasons"],
                    "rejection_reasons": intel_dict["rejection_reasons"],
                    "revenue_potential": intel_dict["revenue_potential"],
                    "probability_to_buy": intel_dict["probability_to_buy"],
                    "probability_reasons": intel_dict["probability_reasons"],
                    "why_comai": intel_dict["why_comai"],
                    "recommended_pitch": intel_dict["recommended_pitch"],
                    "priority": intel_dict["priority"],
                    "traffic_score": intel_dict["traffic_score"],
                    "review_score": intel_dict["review_score"],
                    "social_growth": intel_dict["social_growth"],
                    "whatsapp_score": intel_dict["whatsapp_score"],
                    "founder_score": intel_dict["founder_score"],
                    "evidence_json": intel_dict["evidence"],
                    "product_count": intel_dict["product_count"],
                }

                await self.ri_repo.upsert_by_domain(store_data)
                processed += 1
            except Exception as e:
                logger.debug("Analysis failed for %s: %s", lead.domain, e)

        await self.ri_repo.commit()
        return {"status": "completed", "processed": processed, "total_leads": total}
