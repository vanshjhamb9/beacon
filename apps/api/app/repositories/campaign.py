from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import (
    Campaign,
    CampaignApproval,
    CampaignAudit,
    CampaignChannel,
    CampaignExecutionLog,
    CampaignSchedule,
    CampaignStep,
)
from app.models.copilot import SalesDraft, SalesPackage
from app.models.decision import DecisionDiscoveryReport, DecisionMaker
from app.models.intelligence import Company
from app.models.opportunity import Opportunity
from app.models.outcomes import ContactAttempt, OpportunityOutcome
from app.models.revenue import SalesPlaybook
from app.models.verification import VerificationReport
from campaign_intelligence.channels.catalog import all_channels
from campaign_intelligence.models.types import CampaignInput, CampaignPlan, CampaignStatus
from campaign_intelligence.scheduler.rules import ScheduleEngine


class CampaignRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.scheduler = ScheduleEngine()

    async def ensure_channel_seed(self) -> None:
        existing = await self.session.scalar(select(CampaignChannel.id).limit(1))
        if existing is not None:
            return
        for channel in all_channels():
            self.session.add(
                CampaignChannel(
                    kind=channel.kind.value,
                    label=channel.label,
                    supports_async=channel.supports_async,
                    supports_attachments=channel.supports_attachments,
                    requires_opt_in=channel.requires_opt_in,
                    max_daily_sends=channel.max_daily_sends,
                    min_gap_hours=channel.min_gap_hours,
                    business_hours_only=channel.business_hours_only,
                    constraints=list(channel.constraints),
                    delivery_ready=False,
                    metadata_json={},
                )
            )
        await self.session.flush()

    async def list_campaigns(self, *, limit: int = 100, offset: int = 0) -> Sequence[Campaign]:
        result = await self.session.execute(
            select(Campaign).order_by(Campaign.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def get_campaign(self, campaign_id: UUID) -> Campaign | None:
        return await self.session.get(Campaign, campaign_id)

    async def campaign_bundle(self, campaign: Campaign) -> dict[str, Any]:
        steps = (
            await self.session.execute(
                select(CampaignStep)
                .where(CampaignStep.campaign_id == campaign.id)
                .order_by(CampaignStep.sequence)
            )
        ).scalars().all()
        schedules = (
            await self.session.execute(
                select(CampaignSchedule)
                .where(CampaignSchedule.campaign_id == campaign.id)
                .order_by(CampaignSchedule.planned_at)
            )
        ).scalars().all()
        approvals = (
            await self.session.execute(
                select(CampaignApproval)
                .where(CampaignApproval.campaign_id == campaign.id)
                .order_by(CampaignApproval.created_at.desc())
            )
        ).scalars().all()
        logs = (
            await self.session.execute(
                select(CampaignExecutionLog)
                .where(CampaignExecutionLog.campaign_id == campaign.id)
                .order_by(CampaignExecutionLog.created_at.desc())
                .limit(50)
            )
        ).scalars().all()
        audit = (
            await self.session.execute(
                select(CampaignAudit)
                .where(CampaignAudit.campaign_id == campaign.id)
                .order_by(CampaignAudit.created_at.desc())
                .limit(50)
            )
        ).scalars().all()
        return {
            "campaign": campaign,
            "steps": steps,
            "schedules": schedules,
            "approvals": approvals,
            "execution_logs": logs,
            "audit": audit,
        }

    async def build_input_for_company(self, company_id: UUID, *, force_refresh: bool = False) -> CampaignInput | None:
        opportunity = await self.session.scalar(
            select(Opportunity)
            .where(Opportunity.company_id == company_id)
            .order_by(Opportunity.opportunity_score.desc(), Opportunity.created_at.desc())
            .limit(1)
        )
        if opportunity is None:
            return None
        return await self.build_input_for_opportunity(opportunity.id, force_refresh=force_refresh)

    async def build_input_for_opportunity(
        self, opportunity_id: UUID, *, force_refresh: bool = False
    ) -> CampaignInput | None:
        opportunity = await self.session.get(Opportunity, opportunity_id)
        if opportunity is None:
            return None
        company = await self.session.get(Company, opportunity.company_id)
        if company is None:
            return None

        package = await self.session.scalar(
            select(SalesPackage)
            .where(
                SalesPackage.opportunity_id == opportunity_id,
                SalesPackage.review_status.in_(["approved", "favorite", "pending"]),
            )
            .order_by(SalesPackage.version.desc(), SalesPackage.created_at.desc())
            .limit(1)
        )
        if package is None:
            package = await self.session.scalar(
                select(SalesPackage)
                .where(SalesPackage.opportunity_id == opportunity_id)
                .order_by(SalesPackage.version.desc(), SalesPackage.created_at.desc())
                .limit(1)
            )
        # Prefer approved packages when available
        approved = await self.session.scalar(
            select(SalesPackage)
            .where(SalesPackage.opportunity_id == opportunity_id, SalesPackage.review_status == "approved")
            .order_by(SalesPackage.version.desc())
            .limit(1)
        )
        if approved is not None:
            package = approved

        decision = await self.session.scalar(
            select(DecisionDiscoveryReport)
            .where(DecisionDiscoveryReport.opportunity_id == opportunity_id)
            .order_by(DecisionDiscoveryReport.created_at.desc())
            .limit(1)
        )
        playbook = await self.session.scalar(
            select(SalesPlaybook)
            .where(SalesPlaybook.opportunity_id == opportunity_id)
            .order_by(SalesPlaybook.created_at.desc())
            .limit(1)
        )
        verification = await self.session.scalar(
            select(VerificationReport)
            .where(VerificationReport.opportunity_id == opportunity_id)
            .order_by(VerificationReport.created_at.desc())
            .limit(1)
        )
        outcome = await self.session.scalar(
            select(OpportunityOutcome)
            .where(OpportunityOutcome.opportunity_id == opportunity_id)
            .order_by(OpportunityOutcome.created_at.desc())
            .limit(1)
        )
        contacts = (
            await self.session.execute(
                select(ContactAttempt)
                .where(ContactAttempt.opportunity_id == opportunity_id)
                .order_by(ContactAttempt.attempted_at.desc())
                .limit(20)
            )
        ).scalars().all()

        sales_package: dict[str, Any] = {}
        if package is not None:
            drafts = (
                await self.session.execute(select(SalesDraft).where(SalesDraft.package_id == package.id))
            ).scalars().all()
            style_variants: dict[str, list[dict[str, Any]]] = {}
            for draft in drafts:
                style_variants.setdefault(draft.style, []).append(
                    {
                        "kind": draft.kind,
                        "style": draft.style,
                        "title": draft.title,
                        "body": draft.body,
                        "subject_lines": list(draft.subject_lines or []),
                        "attribution": dict(draft.attribution or {}),
                    }
                )
            sales_package = {
                "id": str(package.id),
                "review_status": package.review_status,
                "version": package.version,
                "recommended_service": package.recommended_service,
                "business_pain": package.business_pain,
                "quality_scores": dict(package.quality_scores or {}),
                "sections": list(package.sections or []),
                "style_variants": [
                    {"style": style, "drafts": drafts_for_style}
                    for style, drafts_for_style in style_variants.items()
                ],
                "drafts": [
                    draft
                    for drafts_for_style in style_variants.values()
                    for draft in drafts_for_style
                ],
                "evidence_chain": list(package.evidence_chain or []),
            }

        makers: list[dict[str, Any]] = []
        primary = None
        if decision is not None:
            maker_rows = (
                await self.session.execute(
                    select(DecisionMaker).where(DecisionMaker.discovery_report_id == decision.id)
                )
            ).scalars().all()
            makers = [
                {
                    "name": row.name,
                    "role": row.role,
                    "confidence": row.confidence,
                    "is_primary": row.is_primary,
                }
                for row in maker_rows
            ]
            primary = next((m for m in makers if m.get("is_primary")), makers[0] if makers else None)

        revenue = {
            "recommended_service": (playbook.recommended_service if playbook else None)
            or (package.recommended_service if package else None)
            or "",
            "business_pain": (playbook.business_pain if playbook else None)
            or (package.business_pain if package else None)
            or opportunity.narrative,
            "buyer_persona": (playbook.decision_maker if playbook else None),
            "conversation_angle": playbook.conversation_angle if playbook else None,
        }

        return CampaignInput(
            company_id=company.id,
            opportunity_id=opportunity.id,
            company_name=company.name,
            industry=company.industry,
            company_size=None,
            timezone="UTC",
            opportunity_score=opportunity.opportunity_score,
            opportunity_status=opportunity.status,
            opportunity_urgency=opportunity.urgency_score,
            recommended_service=str(revenue.get("recommended_service") or ""),
            business_pain=str(revenue.get("business_pain") or ""),
            buyer_persona=str(revenue.get("buyer_persona")) if revenue.get("buyer_persona") else None,
            sales_package=sales_package,
            decision_discovery={
                "best_outreach_sequence": list(decision.best_outreach_sequence or []) if decision else [],
                "buyer_match_confidence": decision.buyer_match_confidence if decision else 0.0,
                "overall_discovery_score": decision.overall_discovery_score if decision else 0.0,
                "primary_decision_maker": primary,
                "decision_makers": makers,
                "recommended_service": decision.recommended_service if decision else revenue.get("recommended_service"),
            },
            revenue=revenue,
            opportunity={
                "id": str(opportunity.id),
                "status": opportunity.status,
                "opportunity_score": opportunity.opportunity_score,
                "urgency_score": opportunity.urgency_score,
                "narrative": opportunity.narrative,
            },
            verification={
                "decision": verification.decision if verification else None,
                "overall_readiness": verification.overall_readiness if verification else None,
                "trust_score": verification.trust_score if verification else None,
                "overall_data_quality": verification.overall_data_quality if verification else None,
            },
            outcomes={
                "lifecycle_stage": outcome.lifecycle_stage if outcome else None,
                "contact_channels": [row.channel for row in contacts],
            },
            force_refresh=force_refresh,
        )

    async def store_plan(self, plan: CampaignPlan) -> Campaign:
        await self.ensure_channel_seed()
        campaign = Campaign(
            company_id=plan.company_id,
            opportunity_id=plan.opportunity_id,
            sales_package_id=plan.sales_package_id,
            company_name=plan.company_name,
            status=plan.status.value,
            priority=plan.priority.value,
            primary_channel=plan.primary_channel.value,
            secondary_channel=plan.secondary_channel.value if plan.secondary_channel else None,
            follow_up_count=plan.follow_up_count,
            delay_hours_between_messages=list(plan.delay_hours_between_messages),
            expected_confidence=plan.expected_confidence,
            channel_choice_reason=plan.channel_choice_reason,
            timing_reason=plan.timing_reason,
            message_selection_reason=plan.message_selection_reason,
            recommended_service=plan.recommended_service or "",
            business_pain=plan.business_pain or "",
            buyer_persona=plan.buyer_persona,
            industry=plan.industry,
            communication_style=plan.communication_style,
            timezone=plan.schedule_rules.timezone,
            schedule_rules=plan.schedule_rules.model_dump(mode="json"),
            evidence=[item.model_dump(mode="json") for item in plan.evidence],
            quality=dict(plan.quality),
            plan_payload=dict(plan.plan_payload),
        )
        self.session.add(campaign)
        await self.session.flush()

        planned_times = self.scheduler.plan_step_times(
            rules=plan.schedule_rules,
            delay_hours=list(plan.delay_hours_between_messages),
        )
        step_rows: list[CampaignStep] = []
        for step in plan.outreach_sequence:
            row = CampaignStep(
                campaign_id=campaign.id,
                company_id=plan.company_id,
                sequence=step.sequence,
                kind=step.kind.value,
                channel=step.channel.value,
                delay_hours=step.delay_hours,
                draft_kind=step.draft_kind,
                draft_style=step.draft_style,
                subject_preview=step.subject_preview,
                body_preview=step.body_preview,
                message_selection_reason=step.message_selection_reason,
                timing_reason=step.timing_reason,
                confidence=step.confidence,
                status="planned",
                evidence=[item.model_dump(mode="json") for item in step.evidence],
                sales_draft_ref=dict(step.sales_draft_ref),
            )
            self.session.add(row)
            step_rows.append(row)
        await self.session.flush()

        for idx, step_row in enumerate(step_rows):
            planned_at = planned_times[idx] if idx < len(planned_times) else datetime.now(UTC)
            self.session.add(
                CampaignSchedule(
                    campaign_id=campaign.id,
                    campaign_step_id=step_row.id,
                    company_id=plan.company_id,
                    planned_at=planned_at,
                    timezone=plan.schedule_rules.timezone,
                    status="planned",
                    rules_snapshot=plan.schedule_rules.model_dump(mode="json"),
                    timing_reason=step_row.timing_reason,
                )
            )

        self.session.add(
            CampaignExecutionLog(
                campaign_id=campaign.id,
                company_id=plan.company_id,
                event_type="campaign_created",
                channel=plan.primary_channel.value,
                status="ready",
                message="Campaign plan created. Delivery disabled until Sprint 15 providers.",
                provider="none",
                delivery_attempted=False,
                details={"follow_up_count": plan.follow_up_count},
            )
        )
        self.session.add(
            CampaignAudit(
                campaign_id=campaign.id,
                company_id=plan.company_id,
                entity_type="campaign",
                entity_id=campaign.id,
                action="created",
                actor="system",
                before_state={},
                after_state={"status": campaign.status, "priority": campaign.priority},
                details={"expected_confidence": plan.expected_confidence},
            )
        )
        await self.session.flush()
        return campaign

    async def apply_status(
        self,
        campaign: Campaign,
        *,
        to_status: CampaignStatus,
        action: str,
        actor: str,
        notes: str = "",
    ) -> Campaign:
        before = campaign.status
        campaign.status = to_status.value
        self.session.add(
            CampaignApproval(
                campaign_id=campaign.id,
                company_id=campaign.company_id,
                action=action,
                from_status=before,
                to_status=to_status.value,
                actor=actor,
                notes=notes,
                metadata_json={"delivery_attempted": False},
            )
        )
        self.session.add(
            CampaignAudit(
                campaign_id=campaign.id,
                company_id=campaign.company_id,
                entity_type="campaign",
                entity_id=campaign.id,
                action=action,
                actor=actor,
                before_state={"status": before},
                after_state={"status": to_status.value},
                details={"notes": notes},
            )
        )
        self.session.add(
            CampaignExecutionLog(
                campaign_id=campaign.id,
                company_id=campaign.company_id,
                event_type=action,
                channel=campaign.primary_channel,
                status=to_status.value,
                message=f"Campaign {action}. No provider delivery performed.",
                provider="none",
                delivery_attempted=False,
                details={},
            )
        )
        if to_status == CampaignStatus.APPROVED:
            # Mark schedules as approved/ready — still not sent.
            schedules = (
                await self.session.execute(
                    select(CampaignSchedule).where(CampaignSchedule.campaign_id == campaign.id)
                )
            ).scalars().all()
            for schedule in schedules:
                schedule.status = "approved_ready"
            campaign.status = CampaignStatus.SCHEDULED.value
            # Extra audit for scheduled readiness
            self.session.add(
                CampaignAudit(
                    campaign_id=campaign.id,
                    company_id=campaign.company_id,
                    entity_type="campaign",
                    entity_id=campaign.id,
                    action="scheduled_ready",
                    actor=actor,
                    before_state={"status": CampaignStatus.APPROVED.value},
                    after_state={"status": CampaignStatus.SCHEDULED.value},
                    details={"note": "Execution readiness only; providers not connected"},
                )
            )
        await self.session.flush()
        return campaign

    async def company_timeline(self, company_id: UUID) -> list[dict[str, Any]]:
        campaigns = (
            await self.session.execute(
                select(Campaign)
                .where(Campaign.company_id == company_id)
                .order_by(Campaign.created_at.desc())
                .limit(20)
            )
        ).scalars().all()
        timeline: list[dict[str, Any]] = []
        for campaign in campaigns:
            audit_rows = (
                await self.session.execute(
                    select(CampaignAudit)
                    .where(CampaignAudit.campaign_id == campaign.id)
                    .order_by(CampaignAudit.created_at.asc())
                )
            ).scalars().all()
            for row in audit_rows:
                timeline.append(
                    {
                        "campaign_id": str(campaign.id),
                        "company_id": str(company_id),
                        "action": row.action,
                        "actor": row.actor,
                        "before_state": row.before_state,
                        "after_state": row.after_state,
                        "created_at": row.created_at.isoformat(),
                        "company_name": campaign.company_name,
                        "status": campaign.status,
                    }
                )
        return timeline

    async def dashboard_rows(self) -> list[dict[str, Any]]:
        campaigns = await self.list_campaigns(limit=500, offset=0)
        return [
            {
                "id": str(item.id),
                "status": item.status,
                "priority": item.priority,
                "primary_channel": item.primary_channel,
                "expected_confidence": item.expected_confidence,
                "company_name": item.company_name,
                "company_id": str(item.company_id),
            }
            for item in campaigns
        ]

    async def list_schedules(self, *, limit: int = 200) -> Sequence[CampaignSchedule]:
        result = await self.session.execute(
            select(CampaignSchedule).order_by(CampaignSchedule.planned_at.asc()).limit(limit)
        )
        return list(result.scalars().all())

    async def list_approvals_pending(self, *, limit: int = 100) -> Sequence[Campaign]:
        result = await self.session.execute(
            select(Campaign)
            .where(Campaign.status.in_(["needs_review", "draft"]))
            .order_by(Campaign.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
