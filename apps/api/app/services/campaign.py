from __future__ import annotations

from typing import Any
from uuid import UUID

from app.repositories.campaign import CampaignRepository
from campaign_intelligence import CampaignIntelligenceService
from campaign_intelligence.analytics.metrics import CampaignAnalytics
from campaign_intelligence.approval.workflow import ApprovalWorkflow
from campaign_intelligence.models.types import CampaignStatus


class CampaignService:
    def __init__(
        self,
        repository: CampaignRepository,
        *,
        domain: CampaignIntelligenceService | None = None,
    ) -> None:
        self.repository = repository
        self.domain = domain or CampaignIntelligenceService()
        self.workflow = ApprovalWorkflow()
        self.analytics = CampaignAnalytics()

    async def list_campaigns(self, *, limit: int, offset: int) -> list[Any]:
        return list(await self.repository.list_campaigns(limit=limit, offset=offset))

    async def get_campaign(self, campaign_id: UUID) -> dict[str, Any] | None:
        campaign = await self.repository.get_campaign(campaign_id)
        if campaign is None:
            return None
        return await self.repository.campaign_bundle(campaign)

    async def create_for_company(self, company_id: UUID) -> dict[str, Any]:
        item = await self.repository.build_input_for_company(company_id, force_refresh=True)
        if item is None:
            return {"created": False, "campaign": None, "detail": "No opportunity found for company"}
        if not item.sales_package:
            return {
                "created": False,
                "campaign": None,
                "detail": "Approved or available Sales Copilot package required",
            }
        # Compose Production Validation lead gate — never redesign campaign planner.
        gate = await self._lead_readiness_gate(company_id)
        if gate is not None and not gate.get("outreach_allowed", True):
            return {
                "created": False,
                "campaign": None,
                "detail": (
                    f"Lead readiness {gate.get('score')} below gate; "
                    f"blocked: {', '.join(gate.get('blocking_reasons') or [])}"
                ),
                "lead_readiness": gate,
            }
        plan = self.domain.create_plan(item)
        stored = await self.repository.store_plan(plan)
        bundle = await self.repository.campaign_bundle(stored)
        return {"created": True, "campaign": bundle, "detail": None}

    async def _lead_readiness_gate(self, company_id: UUID) -> dict[str, Any] | None:
        try:
            from app.repositories.production_validation import ProductionValidationRepository
            from app.services.production_validation import ProductionValidationPlatformService

            service = ProductionValidationPlatformService(ProductionValidationRepository(self.repository.session))
            return await service.company_readiness(company_id, refresh=True)
        except Exception:  # noqa: BLE001
            return None

    async def approve(self, campaign_id: UUID, *, actor: str = "operator", notes: str = "") -> dict[str, Any]:
        return await self._transition(
            campaign_id,
            target=CampaignStatus.APPROVED,
            action="approve",
            actor=actor,
            notes=notes,
        )

    async def reject(self, campaign_id: UUID, *, actor: str = "operator", notes: str = "") -> dict[str, Any]:
        return await self._transition(
            campaign_id,
            target=CampaignStatus.REJECTED,
            action="reject",
            actor=actor,
            notes=notes,
        )

    async def bulk_approve(
        self,
        campaign_ids: list[UUID],
        *,
        actor: str = "founder",
        notes: str = "",
    ) -> dict[str, Any]:
        results = []
        for cid in campaign_ids:
            results.append(await self.approve(cid, actor=actor, notes=notes or "bulk_approve"))
        return {
            "updated": sum(1 for r in results if r.get("updated")),
            "failed": sum(1 for r in results if not r.get("updated")),
            "results": results,
        }

    async def bulk_reject(
        self,
        campaign_ids: list[UUID],
        *,
        actor: str = "founder",
        notes: str = "",
    ) -> dict[str, Any]:
        results = []
        for cid in campaign_ids:
            results.append(await self.reject(cid, actor=actor, notes=notes or "bulk_reject"))
        return {
            "updated": sum(1 for r in results if r.get("updated")),
            "failed": sum(1 for r in results if not r.get("updated")),
            "results": results,
        }

    async def pause(self, campaign_id: UUID, *, actor: str = "operator", notes: str = "") -> dict[str, Any]:
        return await self._transition(
            campaign_id,
            target=CampaignStatus.PAUSED,
            action="pause",
            actor=actor,
            notes=notes,
        )

    async def cancel(self, campaign_id: UUID, *, actor: str = "operator", notes: str = "") -> dict[str, Any]:
        return await self._transition(
            campaign_id,
            target=CampaignStatus.CANCELLED,
            action="cancel",
            actor=actor,
            notes=notes,
        )

    async def _transition(
        self,
        campaign_id: UUID,
        *,
        target: CampaignStatus,
        action: str,
        actor: str,
        notes: str,
    ) -> dict[str, Any]:
        campaign = await self.repository.get_campaign(campaign_id)
        if campaign is None:
            return {"updated": False, "campaign": None, "detail": "Campaign not found"}
        current = CampaignStatus(campaign.status)
        try:
            if action == "approve":
                self.workflow.approve(current)
            elif action == "reject":
                self.workflow.reject(current)
            elif action == "pause":
                self.workflow.pause(current)
            elif action == "cancel":
                self.workflow.cancel(current)
            else:
                self.workflow.transition(current, target)
        except ValueError as exc:
            return {"updated": False, "campaign": None, "detail": str(exc)}
        updated = await self.repository.apply_status(
            campaign,
            to_status=target,
            action=action,
            actor=actor,
            notes=notes,
        )
        bundle = await self.repository.campaign_bundle(updated)
        return {"updated": True, "campaign": bundle, "detail": None}

    async def dashboard(self) -> dict[str, Any]:
        rows = await self.repository.dashboard_rows()
        base = self.analytics.dashboard(rows)
        pending = await self.repository.list_approvals_pending(limit=50)
        schedules = await self.repository.list_schedules(limit=100)
        base["pending_approvals"] = [
            {
                "id": str(item.id),
                "company_id": str(item.company_id),
                "company_name": item.company_name,
                "priority": item.priority,
                "primary_channel": item.primary_channel,
                "expected_confidence": item.expected_confidence,
                "status": item.status,
            }
            for item in pending
        ]
        base["upcoming_schedules"] = [
            {
                "id": str(item.id),
                "campaign_id": str(item.campaign_id),
                "company_id": str(item.company_id),
                "planned_at": item.planned_at.isoformat(),
                "timezone": item.timezone,
                "status": item.status,
                "timing_reason": item.timing_reason,
            }
            for item in schedules
        ]
        return base
