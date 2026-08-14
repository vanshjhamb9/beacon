from typing import Any
from uuid import UUID

from app.core.config import Settings, get_settings
from app.repositories.enrichment import EnrichmentRepository
from lead_enrichment import EnrichmentPipeline
from lead_enrichment.connectors.dns_mx import DnsMxConnector
from lead_enrichment.connectors.licensed import LicensedProviderConnector
from lead_enrichment.connectors.website import WebsiteConnector


def build_enrichment_pipeline(settings: Settings | None = None) -> EnrichmentPipeline:
    resolved = settings or get_settings()
    api_keys: dict[str, str] = {}
    if resolved.builtwith_api_key is not None:
        api_keys["builtwith"] = resolved.builtwith_api_key.get_secret_value()
    if resolved.wappalyzer_api_key is not None:
        api_keys["wappalyzer"] = resolved.wappalyzer_api_key.get_secret_value()
    if resolved.crunchbase_api_key is not None:
        api_keys["crunchbase"] = resolved.crunchbase_api_key.get_secret_value()
    return EnrichmentPipeline(
        website=WebsiteConnector(enabled=resolved.enrichment_website_fetch_enabled),
        dns=DnsMxConnector(enabled=resolved.enrichment_dns_lookup_enabled),
        licensed=LicensedProviderConnector(api_keys=api_keys),
    )


class LeadEnrichmentService:
    def __init__(
        self,
        repository: EnrichmentRepository,
        pipeline: EnrichmentPipeline | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.repository = repository
        self.pipeline = pipeline or build_enrichment_pipeline(settings)

    async def process_pending(self, *, limit: int) -> dict[str, int]:
        processed = 0
        inputs = await self.repository.pending_opportunity_inputs(limit=limit)
        for item in inputs:
            result = self.pipeline.process(item)
            await self.repository.store_enrichment(result)
            processed += 1
        return {"processed": processed}

    async def company_lead_profile(self, company_id: UUID) -> dict[str, Any] | None:
        return await self.repository.lead_profile_for_company(company_id)

    async def opportunity_lead_profile(self, opportunity_id: UUID) -> dict[str, Any] | None:
        return await self.repository.lead_profile_for_opportunity(opportunity_id)

    async def refresh(self, opportunity_or_company_id: UUID) -> dict[str, Any] | None:
        opportunity_input = await self.repository.opportunity_input(
            opportunity_or_company_id,
            force_refresh=True,
        )
        if opportunity_input is None:
            latest = await self.repository.latest_report_for_company(opportunity_or_company_id)
            if latest is None:
                return None
            opportunity_input = await self.repository.opportunity_input(
                latest.opportunity_id,
                force_refresh=True,
            )
        if opportunity_input is None:
            return None
        result = self.pipeline.process(opportunity_input)
        await self.repository.store_enrichment(result)
        return await self.repository.lead_profile_for_opportunity(result.opportunity_id)
