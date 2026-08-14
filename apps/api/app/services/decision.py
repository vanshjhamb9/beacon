from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.config import Settings
from app.repositories.decision import DecisionDiscoveryRepository
from decision_discovery import DecisionDiscoveryPipeline, DecisionDiscoveryService
from decision_discovery.connectors.licensed import LicensedPeopleConnector


def build_discovery_pipeline(settings: Settings) -> DecisionDiscoveryPipeline:
    apollo = settings.apollo_api_key.get_secret_value() if settings.apollo_api_key else None
    pdl = settings.people_data_labs_api_key.get_secret_value() if settings.people_data_labs_api_key else None
    return DecisionDiscoveryPipeline(
        licensed=LicensedPeopleConnector(
            apollo_api_key=apollo,
            people_data_labs_api_key=pdl,
            enabled=settings.decision_discovery_licensed_providers_enabled,
        )
    )


class DecisionMakerDiscoveryService:
    def __init__(
        self,
        repository: DecisionDiscoveryRepository,
        *,
        settings: Settings | None = None,
        pipeline: DecisionDiscoveryPipeline | None = None,
    ) -> None:
        self.repository = repository
        self.settings = settings
        if pipeline is not None:
            self.domain = DecisionDiscoveryService(pipeline)
        elif settings is not None:
            self.domain = DecisionDiscoveryService(build_discovery_pipeline(settings))
        else:
            self.domain = DecisionDiscoveryService()

    async def process_pending(self, *, limit: int) -> dict[str, int]:
        processed = 0
        inputs = await self.repository.pending_discovery_inputs(limit=limit)
        for item in inputs:
            report = self.domain.discover(item)
            await self.repository.store_discovery(report)
            processed += 1
        return {"processed": processed}

    async def company_report(self, company_id: UUID) -> dict[str, Any] | None:
        report = await self.repository.latest_report_for_company(company_id)
        if report is None:
            return None
        return await self.repository.report_bundle(report)

    async def opportunity_report(self, opportunity_id: UUID) -> dict[str, Any] | None:
        report = await self.repository.latest_report_for_opportunity(opportunity_id)
        if report is None:
            return None
        return await self.repository.report_bundle(report)

    async def refresh(self, entity_id: UUID) -> dict[str, Any]:
        item = await self.repository.discovery_input_for_company(entity_id, force_refresh=True)
        if item is None:
            item = await self.repository.discovery_input_for_opportunity(entity_id, force_refresh=True)
        if item is None:
            verification_item = await self.repository.discovery_input_for_verification(
                entity_id,
                force_refresh=True,
            )
            item = verification_item
        if item is None:
            return {"refreshed": False, "report": None}
        result = self.domain.discover(item)
        await self.repository.store_discovery(result)
        report = await self.repository.latest_report_for_company(result.company_id)
        bundle = await self.repository.report_bundle(report) if report else None
        return {"refreshed": True, "report": bundle}

    async def search(
        self,
        *,
        query: str | None,
        role: str | None,
        limit: int,
        offset: int,
    ) -> list[Any]:
        return await self.repository.search(query=query, role=role, limit=limit, offset=offset)
