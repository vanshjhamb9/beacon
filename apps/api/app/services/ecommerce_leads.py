from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.core.config import Settings
from app.models.ecommerce_leads import EcommerceLeadRow
from app.repositories.ecommerce_leads import EcommerceLeadRepository
from packages.ecommerce_leads.exporters.excel_exporter import ExcelExporter
from packages.ecommerce_leads.services.lead_pipeline import LeadPipeline

logger = logging.getLogger(__name__)


class EcommerceLeadsService:
    """Service layer for ecommerce leads operations."""

    def __init__(
        self,
        repository: EcommerceLeadRepository,
        *,
        settings: Settings | None = None,
    ) -> None:
        self.repository = repository
        self.settings = settings
        self.pipeline = LeadPipeline()
        self.exporter = ExcelExporter()

    async def list_leads(
        self,
        *,
        country: str | None = None,
        state: str | None = None,
        category: str | None = None,
        platform: str | None = None,
        min_score: float | None = None,
        priority: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        leads, total = await self.repository.list_with_filters(
            country=country,
            state=state,
            category=category,
            platform=platform,
            min_score=min_score,
            priority=priority,
            limit=limit,
            offset=offset,
        )
        return {
            "leads": leads,
            "total": total,
            "page": offset // limit + 1,
            "page_size": limit,
        }

    async def get_lead(self, lead_id: UUID) -> EcommerceLeadRow | None:
        return await self.repository.get(lead_id)

    async def discover_leads(
        self,
        *,
        limit: int = 500,
        country: str = "India",
    ) -> dict[str, Any]:
        """Run the discovery pipeline and store results."""
        logger.info("Starting discovery: limit=%d, country=%s", limit, country)
        results = await self.pipeline.run_discovery(limit=limit, country=country)

        stored = 0
        for lead_data in results:
            try:
                await self.repository.upsert_by_domain(lead_data)
                stored += 1
            except Exception as e:
                logger.debug("Failed to store lead %s: %s", lead_data.get("domain"), e)

        await self.repository.commit()
        logger.info("Discovery complete: %d leads stored", stored)

        return {
            "status": "completed",
            "leads_collected": len(results),
            "leads_stored": stored,
        }

    async def export_leads(
        self,
        *,
        country: str | None = None,
        state: str | None = None,
        category: str | None = None,
        platform: str | None = None,
        min_score: float | None = None,
        priority: str | None = None,
    ) -> bytes:
        """Export leads to Excel."""
        all_leads: list[EcommerceLeadRow] = []
        offset = 0
        batch_size = 500

        while True:
            leads, total = await self.repository.list_with_filters(
                country=country,
                state=state,
                category=category,
                platform=platform,
                min_score=min_score,
                priority=priority,
                limit=batch_size,
                offset=offset,
            )
            all_leads.extend(leads)
            offset += batch_size
            if offset >= total or not leads:
                break

        lead_dicts = [
            {
                "company_name": l.company_name,
                "website": l.website,
                "platform": l.platform,
                "category": l.category,
                "city": l.city,
                "state": l.state,
                "owner_name": l.owner_name,
                "founder_name": l.founder_name,
                "email": l.email,
                "phone": l.phone,
                "instagram_url": l.instagram_url,
                "linkedin_url": l.linkedin_url,
                "whatsapp": l.phone if l.whatsapp_detected else "",
                "product_count": l.product_count,
                "chatbot_detected": l.chatbot_detected,
                "comai_score": l.comai_score,
                "lead_priority": l.lead_priority,
                "sales_reason": l.sales_reason,
                "source": l.source,
            }
            for l in all_leads
        ]

        return self.exporter.export_leads(lead_dicts)

    async def get_stats(self) -> dict[str, Any]:
        return await self.repository.get_stats()
