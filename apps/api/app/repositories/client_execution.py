from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client_execution import (
    ClientHandoffRow,
    ClientHealthSnapshot,
    ClientMemoryRow,
    ClientProfile,
    ClientProject,
    DeliverySnapshot,
    RenewalPredictionRow,
    UpsellRecommendationRow,
)
from app.models.decision import DecisionMaker
from app.models.intelligence import Company
from app.models.outcomes import Deal
from app.models.revenue_hunter import RevenueHunterDossier
from client_execution.models.types import (
    ClientExecutionDecision,
    ClientExecutionInput,
    ClientProjectSignal,
)


class ClientExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def build_input(self, company_id: UUID) -> ClientExecutionInput | None:
        company = await self.session.get(Company, company_id)
        if company is None:
            return None
        attrs = company.attributes or {}
        dossier = await self.session.scalar(
            select(RevenueHunterDossier)
            .where(RevenueHunterDossier.company_id == company_id)
            .order_by(RevenueHunterDossier.created_at.desc())
            .limit(1)
        )
        dms = list(
            (await self.session.execute(select(DecisionMaker).where(DecisionMaker.company_id == company_id).limit(8)))
            .scalars()
            .all()
        )
        deal = await self.session.scalar(
            select(Deal).where(Deal.company_id == company_id).order_by(Deal.created_at.desc()).limit(1)
        )
        contract_value = float(attrs.get("contract_value") or (deal.value if deal else 0) or 0)
        won = bool(attrs.get("won") or deal is not None or attrs.get("is_client"))
        projects_raw = list(attrs.get("projects") or [])
        projects = [
            ClientProjectSignal(
                name=str(p.get("name") or "Delivery"),
                stage=str(p.get("stage") or "") or None,
                blocked=bool(p.get("blocked")),
                at_risk=bool(p.get("at_risk")),
                milestone=str(p.get("milestone") or "") or None,
                due_today=bool(p.get("due_today")),
                deliverable=str(p.get("deliverable") or "") or None,
            )
            for p in projects_raw
            if isinstance(p, dict)
        ]
        return ClientExecutionInput(
            company_id=company.id,
            company_name=company.name,
            industry=company.industry or (dossier.industry if dossier else None),
            won=won if won else True,
            contract_signed=bool(attrs.get("contract_signed")),
            kickoff_scheduled=bool(attrs.get("kickoff_scheduled")),
            requirements_complete=bool(attrs.get("requirements_complete")),
            planning_complete=bool(attrs.get("planning_complete")),
            design_complete=bool(attrs.get("design_complete")),
            development_active=bool(attrs.get("development_active")),
            testing_active=bool(attrs.get("testing_active")),
            in_review=bool(attrs.get("in_review")),
            launched=bool(attrs.get("launched")),
            in_support=bool(attrs.get("in_support")),
            upsell_signal=bool(attrs.get("upsell_signal")),
            renewal_due=bool(attrs.get("renewal_due")),
            referral_made=bool(attrs.get("referral_made")),
            lost_client=bool(attrs.get("lost_client")),
            archived=bool(attrs.get("archived")),
            services_purchased=list(attrs.get("services_purchased") or ([dossier.recommended_service] if dossier and dossier.recommended_service else [])),
            contract_value=contract_value,
            revenue_delivered=float(attrs.get("revenue_delivered") or 0),
            expected_delivery=str(attrs.get("expected_delivery") or "") or None,
            renewal_date=str(attrs.get("renewal_date") or "") or None,
            primary_contacts=list(attrs.get("primary_contacts") or []),
            decision_makers=[{"name": dm.name, "title": dm.role, "email": dm.work_email} for dm in dms],
            meeting_history=list(attrs.get("meeting_history") or []),
            requirements=list(attrs.get("requirements") or []),
            deliverables=list(attrs.get("deliverables") or []),
            risks=list(attrs.get("risks") or []),
            timeline=list(attrs.get("timeline") or []),
            support_requests=list(attrs.get("support_requests") or []),
            business_goals=list(attrs.get("business_goals") or []),
            pain_points=list(attrs.get("pain_points") or (dossier.pain_points if dossier and isinstance(dossier.pain_points, list) else []) or []),
            agreed_solution=str(attrs.get("agreed_solution") or "") or None,
            scope_summary=str(attrs.get("scope_summary") or "") or None,
            known_objections=list(attrs.get("known_objections") or []),
            decision_history=list(attrs.get("decision_history") or []),
            sales_notes=list(attrs.get("sales_notes") or []),
            founder_notes=list(attrs.get("founder_notes") or []),
            architecture_notes=list(attrs.get("architecture_notes") or []),
            documents=list(attrs.get("documents") or []),
            revisions=list(attrs.get("revisions") or []),
            feedback=list(attrs.get("feedback") or []),
            approvals=list(attrs.get("approvals") or []),
            growth_signals=list(attrs.get("growth_signals") or []),
            hiring_signals=list(attrs.get("hiring_signals") or []),
            funding_signals=list(attrs.get("funding_signals") or []),
            usage_signals=list(attrs.get("usage_signals") or []),
            expansion_signals=list(attrs.get("expansion_signals") or []),
            projects=projects,
            communication_score=float(attrs.get("communication_score") or 70),
            delivery_progress=float(attrs.get("delivery_progress") or 50),
            delay_days=int(attrs.get("delay_days") or 0),
            satisfaction=float(attrs.get("satisfaction") or 70),
            meetings_last_30d=int(attrs.get("meetings_last_30d") or 2),
            open_issues=int(attrs.get("open_issues") or 0),
            days_to_renewal=int(attrs["days_to_renewal"]) if attrs.get("days_to_renewal") is not None else None,
            now=datetime.now(UTC),
        )

    async def store_decision(self, decision: ClientExecutionDecision) -> ClientProfile:
        profile = ClientProfile(
            company_id=decision.company_id,
            company_name=decision.company_name,
            stage=decision.stage.value,
            contract_value=float(decision.workspace.contract_value),
            health_status=decision.health.status,
            overall_health=float(decision.health.overall_health),
            payload=decision.model_dump(mode="json"),
            evidence_chain=list(decision.evidence_chain),
            scoring_version=decision.scoring_version,
            metadata_json={},
        )
        self.session.add(profile)
        await self.session.flush()

        for p in decision.delivery_dashboard.blocked_projects + decision.delivery_dashboard.at_risk_projects:
            self.session.add(
                ClientProject(
                    company_id=decision.company_id,
                    profile_id=profile.id,
                    name=str(p.get("project") or "Delivery"),
                    stage=str(p.get("stage") or "") or None,
                    blocked="blocked" in str(p).lower() or bool(p.get("blocked")),
                    at_risk=True,
                    payload=p,
                    evidence=["source:delivery_dashboard"],
                )
            )
        self.session.add(
            ClientHealthSnapshot(
                company_id=decision.company_id,
                profile_id=profile.id,
                status=decision.health.status,
                overall_health=decision.health.overall_health,
                renewal_probability=decision.health.renewal_probability,
                upsell_probability=decision.health.upsell_probability,
                payload=decision.health.model_dump(mode="json"),
                evidence=list(decision.health.evidence),
            )
        )
        self.session.add(
            ClientHandoffRow(
                company_id=decision.company_id,
                profile_id=profile.id,
                payload=decision.handoff.model_dump(mode="json"),
                evidence=list(decision.handoff.evidence),
            )
        )
        for mem in decision.knowledge[:200]:
            self.session.add(
                ClientMemoryRow(
                    company_id=decision.company_id,
                    profile_id=profile.id,
                    record_type=mem.record_type,
                    title=mem.title,
                    body=mem.body,
                    tags=list(mem.tags),
                    searchable_text=mem.searchable_text,
                    evidence=list(mem.evidence),
                    immutable=True,
                )
            )
        for up in decision.upsells:
            existing = await self.session.scalar(
                select(UpsellRecommendationRow).where(UpsellRecommendationRow.recommendation_id == up.recommendation_id)
            )
            if existing:
                continue
            self.session.add(
                UpsellRecommendationRow(
                    company_id=decision.company_id,
                    profile_id=profile.id,
                    recommendation_id=up.recommendation_id,
                    service=up.service.value,
                    title=up.title,
                    reason=up.reason,
                    confidence=up.confidence,
                    requires_founder_approval=True,
                    modifies_production=False,
                    status="pending_approval",
                    evidence=list(up.evidence),
                )
            )
        self.session.add(
            RenewalPredictionRow(
                company_id=decision.company_id,
                profile_id=profile.id,
                renewal_date=decision.workspace.renewal_date,
                probability=decision.health.renewal_probability,
                payload={"renewal_probability": decision.health.renewal_probability},
                evidence=list(decision.health.evidence),
            )
        )
        self.session.add(
            DeliverySnapshot(
                payload=decision.delivery_dashboard.model_dump(mode="json"),
                founder_view=decision.founder_view.model_dump(mode="json"),
                evidence_chain=list(decision.evidence_chain),
                scoring_version=decision.scoring_version,
            )
        )
        await self.session.flush()
        return profile

    async def latest_for_company(self, company_id: UUID) -> ClientProfile | None:
        return await self.session.scalar(
            select(ClientProfile).where(ClientProfile.company_id == company_id).order_by(ClientProfile.created_at.desc()).limit(1)
        )

    async def recent_profiles(self, *, limit: int = 50) -> list[ClientProfile]:
        return list(
            (await self.session.execute(select(ClientProfile).order_by(ClientProfile.created_at.desc()).limit(limit)))
            .scalars()
            .all()
        )

    async def recent_health(self, *, limit: int = 50) -> list[ClientHealthSnapshot]:
        return list(
            (
                await self.session.execute(
                    select(ClientHealthSnapshot).order_by(ClientHealthSnapshot.created_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def recent_handoffs(self, *, limit: int = 50) -> list[ClientHandoffRow]:
        return list(
            (await self.session.execute(select(ClientHandoffRow).order_by(ClientHandoffRow.created_at.desc()).limit(limit)))
            .scalars()
            .all()
        )

    async def recent_upsells(self, *, limit: int = 50) -> list[UpsellRecommendationRow]:
        return list(
            (
                await self.session.execute(
                    select(UpsellRecommendationRow).order_by(UpsellRecommendationRow.created_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def recent_projects(self, *, limit: int = 50) -> list[ClientProject]:
        return list(
            (await self.session.execute(select(ClientProject).order_by(ClientProject.created_at.desc()).limit(limit)))
            .scalars()
            .all()
        )

    async def latest_delivery(self) -> DeliverySnapshot | None:
        return await self.session.scalar(select(DeliverySnapshot).order_by(DeliverySnapshot.created_at.desc()).limit(1))

    async def company_ids(self, *, limit: int = 40) -> list[UUID]:
        return list((await self.session.execute(select(Company.id).order_by(Company.updated_at.desc()).limit(limit))).scalars().all())

    async def dashboard_counts(self) -> dict[str, Any]:
        total = await self.session.scalar(select(func.count()).select_from(ClientProfile)) or 0
        by_stage = (await self.session.execute(select(ClientProfile.stage, func.count()).group_by(ClientProfile.stage))).all()
        by_health = (
            await self.session.execute(select(ClientProfile.health_status, func.count()).group_by(ClientProfile.health_status))
        ).all()
        return {
            "total_clients": int(total),
            "by_stage": {str(k): int(v) for k, v in by_stage},
            "by_health": {str(k): int(v) for k, v in by_health},
            "scoring_version": "aep-v1",
        }

    async def get_upsell(self, recommendation_id: str) -> UpsellRecommendationRow | None:
        return await self.session.scalar(
            select(UpsellRecommendationRow)
            .where(UpsellRecommendationRow.recommendation_id == recommendation_id)
            .order_by(UpsellRecommendationRow.created_at.desc())
            .limit(1)
        )
