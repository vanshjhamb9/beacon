from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.config import Settings
from app.repositories.copilot import SalesCopilotRepository
from sales_copilot import SalesCopilotPipeline, SalesCopilotService
from sales_copilot.llm.factory import LLMProviderConfig, LLMProviderFactory
from sales_copilot.models.types import LLMProviderName, ReviewAction, ReviewRequest


def build_copilot_pipeline(settings: Settings) -> SalesCopilotPipeline:
    provider = LLMProviderName(settings.sales_copilot_provider)
    factory = LLMProviderFactory(
        LLMProviderConfig(
            provider=provider,
            openai_api_key=settings.openai_api_key.get_secret_value() if settings.openai_api_key else None,
            anthropic_api_key=settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None,
            gemini_api_key=settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else None,
            openrouter_api_key=settings.openrouter_api_key.get_secret_value() if settings.openrouter_api_key else None,
            openai_model=settings.openai_model,
            anthropic_model=settings.anthropic_model,
            gemini_model=settings.gemini_model,
            openrouter_model=settings.openrouter_model,
            temperature=settings.sales_copilot_temperature,
        )
    )
    return SalesCopilotPipeline(llm_factory=factory)


class AISalesCopilotService:
    def __init__(
        self,
        repository: SalesCopilotRepository,
        *,
        settings: Settings | None = None,
        pipeline: SalesCopilotPipeline | None = None,
    ) -> None:
        self.repository = repository
        self.settings = settings
        if pipeline is not None:
            self.domain = SalesCopilotService(pipeline)
        elif settings is not None:
            self.domain = SalesCopilotService(build_copilot_pipeline(settings))
        else:
            self.domain = SalesCopilotService()

    async def process_pending(self, *, limit: int) -> dict[str, int]:
        processed = 0
        skipped = 0
        inputs = await self.repository.pending_inputs(limit=limit * 3 if self._gate_enabled() else limit)
        allowed = await self._top_tier_company_ids() if self._gate_enabled() else None
        for item in inputs:
            if allowed is not None and item.company_id not in allowed:
                skipped += 1
                continue
            version = await self.repository.next_version(item.opportunity_id)
            package = self.domain.generate(item, version=version)
            await self.repository.store_package(package)
            processed += 1
            if processed >= limit:
                break
        return {"processed": processed, "skipped_non_top_tier": skipped}

    def _gate_enabled(self) -> bool:
        return bool(self.settings and getattr(self.settings, "target_account_gate_enabled", True))

    async def _top_tier_company_ids(self) -> set[UUID]:
        from app.repositories.target_account import TargetAccountRepository

        if self.repository.session is None:
            return set()
        return await TargetAccountRepository(self.repository.session).top_tier_company_ids()

    async def company_package(self, company_id: UUID) -> dict[str, Any] | None:
        package = await self.repository.latest_for_company(company_id)
        if package is None:
            return None
        return await self.repository.package_bundle(package)

    async def opportunity_package(self, opportunity_id: UUID) -> dict[str, Any] | None:
        package = await self.repository.latest_for_opportunity(opportunity_id)
        if package is None:
            return None
        return await self.repository.package_bundle(package)

    async def generate(self, entity_id: UUID) -> dict[str, Any]:
        item = await self.repository.build_input_for_company(entity_id, force_refresh=True)
        if item is None:
            item = await self.repository.build_input_for_opportunity(entity_id, force_refresh=True)
        if item is None:
            return {"generated": False, "package": None}
        version = await self.repository.next_version(item.opportunity_id)
        package = self.domain.generate(item, version=version)
        stored = await self.repository.store_package(package)
        bundle = await self.repository.package_bundle(stored)
        return {"generated": True, "package": bundle}

    async def regenerate(self, entity_id: UUID) -> dict[str, Any]:
        existing = await self.repository.get_package(entity_id)
        if existing is not None:
            await self.repository.apply_review(
                existing,
                action=ReviewAction.REGENERATE,
                reviewer="system",
                notes="Regeneration requested",
                rating=None,
            )
            entity_id = existing.opportunity_id
        return await self.generate(entity_id)

    async def review(self, package_id: UUID, request: ReviewRequest) -> dict[str, Any]:
        package = await self.repository.get_package(package_id)
        if package is None:
            return {"reviewed": False, "package": None}
        if request.action == ReviewAction.REGENERATE:
            return await self.regenerate(package_id)
        updated = await self.repository.apply_review(
            package,
            action=request.action,
            reviewer=request.reviewer,
            notes=request.notes,
            rating=request.rating,
        )
        bundle = await self.repository.package_bundle(updated)
        return {"reviewed": True, "package": bundle}

    async def history(self, entity_id: UUID) -> list[Any]:
        return await self.repository.history_for_entity(entity_id)
