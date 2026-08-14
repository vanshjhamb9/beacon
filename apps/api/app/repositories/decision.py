from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.context import CompanyProfile
from app.models.decision import (
    CompanyContactChannel,
    CompanyDepartment,
    CompanyLeadership,
    CompanyPublicProfile,
    DecisionConfidence,
    DecisionDiscoveryReport,
    DecisionHistory,
    DecisionMaker,
)
from app.models.enrichment import CompanyContact, CompanyPerson, CompanySocialProfile, EnrichmentReport
from app.models.intelligence import Company, Person
from app.models.opportunity import Opportunity
from app.models.revenue import SalesPlaybook, SolutionMatch
from app.models.verification import VerificationReport
from decision_discovery.models.types import DecisionDiscoveryInput, DecisionMakerReport


class DecisionDiscoveryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def pending_discovery_inputs(self, *, limit: int) -> Sequence[DecisionDiscoveryInput]:
        stale_or_missing = ~exists().where(
            DecisionDiscoveryReport.verification_report_id == VerificationReport.id,
            DecisionDiscoveryReport.created_at >= VerificationReport.created_at,
        )
        result = await self.session.execute(
            select(VerificationReport.id)
            .where(stale_or_missing)
            .order_by(VerificationReport.created_at.desc())
            .limit(limit)
        )
        inputs: list[DecisionDiscoveryInput] = []
        for report_id in result.scalars().all():
            item = await self.discovery_input_for_verification(report_id)
            if item is not None:
                inputs.append(item)
        return inputs

    async def discovery_input_for_verification(
        self,
        verification_report_id: UUID,
        *,
        force_refresh: bool = False,
    ) -> DecisionDiscoveryInput | None:
        verification = await self.session.get(VerificationReport, verification_report_id)
        if verification is None:
            return None
        return await self._build_input(
            company_id=verification.company_id,
            opportunity_id=verification.opportunity_id,
            enrichment_report_id=verification.enrichment_report_id,
            verification_report_id=verification.id,
            verification_payload=dict(verification.result_payload or {}),
            force_refresh=force_refresh,
        )

    async def discovery_input_for_company(
        self,
        company_id: UUID,
        *,
        force_refresh: bool = False,
    ) -> DecisionDiscoveryInput | None:
        verification = await self.session.scalar(
            select(VerificationReport)
            .where(VerificationReport.company_id == company_id)
            .order_by(VerificationReport.created_at.desc())
            .limit(1)
        )
        if verification is not None:
            return await self.discovery_input_for_verification(
                verification.id,
                force_refresh=force_refresh,
            )

        opportunity = await self.session.scalar(
            select(Opportunity)
            .where(Opportunity.company_id == company_id)
            .order_by(Opportunity.opportunity_score.desc(), Opportunity.created_at.desc())
            .limit(1)
        )
        if opportunity is None:
            return None
        enrichment = await self.session.scalar(
            select(EnrichmentReport)
            .where(EnrichmentReport.opportunity_id == opportunity.id)
            .order_by(EnrichmentReport.created_at.desc())
            .limit(1)
        )
        return await self._build_input(
            company_id=company_id,
            opportunity_id=opportunity.id,
            enrichment_report_id=enrichment.id if enrichment else None,
            verification_report_id=None,
            verification_payload={},
            force_refresh=force_refresh,
        )

    async def discovery_input_for_opportunity(
        self,
        opportunity_id: UUID,
        *,
        force_refresh: bool = False,
    ) -> DecisionDiscoveryInput | None:
        opportunity = await self.session.get(Opportunity, opportunity_id)
        if opportunity is None:
            return None
        verification = await self.session.scalar(
            select(VerificationReport)
            .where(VerificationReport.opportunity_id == opportunity_id)
            .order_by(VerificationReport.created_at.desc())
            .limit(1)
        )
        if verification is not None:
            return await self.discovery_input_for_verification(
                verification.id,
                force_refresh=force_refresh,
            )
        enrichment = await self.session.scalar(
            select(EnrichmentReport)
            .where(EnrichmentReport.opportunity_id == opportunity_id)
            .order_by(EnrichmentReport.created_at.desc())
            .limit(1)
        )
        return await self._build_input(
            company_id=opportunity.company_id,
            opportunity_id=opportunity_id,
            enrichment_report_id=enrichment.id if enrichment else None,
            verification_report_id=None,
            verification_payload={},
            force_refresh=force_refresh,
        )

    async def _build_input(
        self,
        *,
        company_id: UUID,
        opportunity_id: UUID,
        enrichment_report_id: UUID | None,
        verification_report_id: UUID | None,
        verification_payload: dict[str, Any],
        force_refresh: bool,
    ) -> DecisionDiscoveryInput | None:
        company = await self.session.get(Company, company_id)
        opportunity = await self.session.get(Opportunity, opportunity_id)
        if company is None or opportunity is None:
            return None

        enrichment = None
        if enrichment_report_id is not None:
            enrichment = await self.session.get(EnrichmentReport, enrichment_report_id)
        if enrichment is None:
            enrichment = await self.session.scalar(
                select(EnrichmentReport)
                .where(EnrichmentReport.opportunity_id == opportunity_id)
                .order_by(EnrichmentReport.created_at.desc())
                .limit(1)
            )

        lead_profile = dict(enrichment.lead_profile or {}) if enrichment else {}
        solution = await self.session.scalar(
            select(SolutionMatch)
            .where(SolutionMatch.opportunity_id == opportunity_id)
            .order_by(SolutionMatch.created_at.desc())
            .limit(1)
        )
        playbook = await self.session.scalar(
            select(SalesPlaybook)
            .where(SalesPlaybook.opportunity_id == opportunity_id)
            .order_by(SalesPlaybook.created_at.desc())
            .limit(1)
        )
        revenue = {
            "recommended_service": (
                (playbook.recommended_service if playbook else None)
                or lead_profile.get("recommended_service")
                or "Unknown"
            ),
            "business_pain": (
                (playbook.business_pain if playbook else None)
                or lead_profile.get("business_pain")
                or opportunity.narrative
            ),
            "buyer_persona": (
                (playbook.decision_maker if playbook else None)
                or lead_profile.get("buyer_persona")
            ),
            "priority": lead_profile.get("priority"),
            "confidence": float(
                (solution.confidence if solution else None)
                or (lead_profile.get("enrichment_confidence") or {}).get("overall_enrichment_confidence")
                or 0
            ),
        }

        profile = await self.session.scalar(
            select(CompanyProfile)
            .where(CompanyProfile.company_id == company_id)
            .order_by(CompanyProfile.created_at.desc())
            .limit(1)
        )
        context_intelligence = {
            "industry": profile.industry if profile else company.industry,
            "company_stage": profile.company_stage if profile else None,
            "hiring_pattern": profile.hiring_pattern if profile else None,
            "technology_stack": list(profile.technology_stack) if profile else [],
        }

        people_rows = await self._enrichment_people(enrichment.id if enrichment else None, company_id)
        contact_rows = await self._enrichment_contacts(enrichment.id if enrichment else None, company_id)
        profile_rows = await self._enrichment_profiles(enrichment.id if enrichment else None, company_id)
        known_people = await self._known_people(company_id)

        return DecisionDiscoveryInput(
            company_id=company.id,
            opportunity_id=opportunity.id,
            company_name=company.name,
            domain=company.primary_domain,
            website=f"https://{company.primary_domain}" if company.primary_domain else None,
            opportunity_score=opportunity.opportunity_score,
            opportunity_status=opportunity.status,
            business_pain=str(revenue.get("business_pain") or opportunity.narrative),
            recommended_service=str(revenue.get("recommended_service") or "Unknown"),
            buyer_persona=str(revenue.get("buyer_persona")) if revenue.get("buyer_persona") else None,
            revenue_recommendation=revenue,
            lead_profile=lead_profile,
            verification_payload=verification_payload,
            context_intelligence=context_intelligence,
            known_people=known_people,
            enrichment_contacts=contact_rows,
            enrichment_people=people_rows,
            enrichment_profiles=profile_rows,
            enrichment_report_id=enrichment.id if enrichment else None,
            verification_report_id=verification_report_id,
            force_refresh=force_refresh,
        )

    async def store_discovery(self, result: DecisionMakerReport) -> UUID:
        report = DecisionDiscoveryReport(
            company_id=result.company_id,
            opportunity_id=result.opportunity_id,
            enrichment_report_id=result.enrichment_report_id,
            verification_report_id=result.verification_report_id,
            company_name=result.company_name,
            opportunity_score=result.opportunity_score,
            business_pain=result.business_pain,
            recommended_service=result.recommended_service,
            primary_decision_maker_name=result.primary_decision_maker.name if result.primary_decision_maker else None,
            primary_decision_maker_role=result.primary_decision_maker.role if result.primary_decision_maker else None,
            secondary_decision_maker_name=result.secondary_decision_maker.name if result.secondary_decision_maker else None,
            secondary_decision_maker_role=result.secondary_decision_maker.role if result.secondary_decision_maker else None,
            buyer_match_confidence=result.buyer_match_confidence,
            overall_discovery_score=result.confidence.overall_discovery_score,
            reason=result.reason,
            no_public_contact_message=result.no_public_contact_message,
            best_outreach_sequence=[item.model_dump(mode="json") for item in result.best_outreach_sequence],
            evidence_chain=[item.model_dump(mode="json") for item in result.evidence_chain],
            source_attribution=[item.model_dump(mode="json") for item in result.source_attribution],
            report_payload=result.report_payload,
            processing_latency_ms=result.processing_latency_ms,
        )
        self.session.add(report)
        await self.session.flush()

        for maker in result.decision_makers:
            self.session.add(
                DecisionMaker(
                    discovery_report_id=report.id,
                    company_id=result.company_id,
                    name=maker.name,
                    role=maker.role,
                    normalized_role=maker.normalized_role.value,
                    department=maker.department,
                    seniority_rank=maker.seniority_rank,
                    work_email=maker.work_email,
                    business_phone=maker.business_phone,
                    linkedin_url=maker.linkedin_url,
                    is_primary=maker.is_primary,
                    is_secondary=maker.is_secondary,
                    buyer_match_score=maker.buyer_match_score,
                    confidence=maker.confidence,
                    source=maker.source.value,
                    source_url=maker.source_url,
                    evidence=maker.evidence,
                )
            )
        for department in result.departments:
            self.session.add(
                CompanyDepartment(
                    discovery_report_id=report.id,
                    company_id=result.company_id,
                    name=department.name,
                    signal_strength=department.signal_strength,
                    headcount_signal=department.headcount_signal,
                    source=department.source.value,
                    source_url=department.source_url,
                    evidence=department.evidence,
                )
            )
        for channel in result.contact_channels:
            self.session.add(
                CompanyContactChannel(
                    discovery_report_id=report.id,
                    company_id=result.company_id,
                    kind=channel.kind.value,
                    value=channel.value,
                    label=channel.label,
                    rank=channel.rank,
                    confidence=channel.confidence,
                    source=channel.source.value,
                    source_url=channel.source_url,
                    is_verified_public=channel.is_verified_public,
                    evidence=channel.evidence,
                )
            )
        for profile in result.public_profiles:
            self.session.add(
                CompanyPublicProfile(
                    discovery_report_id=report.id,
                    company_id=result.company_id,
                    platform=profile.platform,
                    url=profile.url,
                    handle=profile.handle,
                    confidence=profile.confidence,
                    source=profile.source.value,
                    source_url=profile.source_url,
                )
            )
        for leader in result.leadership:
            self.session.add(
                CompanyLeadership(
                    discovery_report_id=report.id,
                    company_id=result.company_id,
                    name=leader.name,
                    title=leader.title,
                    department=leader.department,
                    confidence=leader.confidence,
                    source=leader.source.value,
                    source_url=leader.source_url,
                    evidence=leader.evidence,
                )
            )
        self.session.add(
            DecisionConfidence(
                discovery_report_id=report.id,
                company_id=result.company_id,
                leadership_confidence=result.confidence.leadership_confidence,
                department_confidence=result.confidence.department_confidence,
                contact_confidence=result.confidence.contact_confidence,
                buyer_match_confidence=result.confidence.buyer_match_confidence,
                overall_discovery_score=result.confidence.overall_discovery_score,
            )
        )
        self.session.add(
            DecisionHistory(
                discovery_report_id=report.id,
                company_id=result.company_id,
                opportunity_id=result.opportunity_id,
                action="discovered",
                actor="system",
                details={
                    "overall_discovery_score": result.confidence.overall_discovery_score,
                    "primary": result.primary_decision_maker.name if result.primary_decision_maker else None,
                },
                occurred_at=datetime.now(UTC),
            )
        )
        await self.session.flush()
        return report.id

    async def latest_report_for_company(self, company_id: UUID) -> DecisionDiscoveryReport | None:
        return await self.session.scalar(
            select(DecisionDiscoveryReport)
            .where(DecisionDiscoveryReport.company_id == company_id)
            .order_by(DecisionDiscoveryReport.created_at.desc())
            .limit(1)
        )

    async def latest_report_for_opportunity(self, opportunity_id: UUID) -> DecisionDiscoveryReport | None:
        return await self.session.scalar(
            select(DecisionDiscoveryReport)
            .where(DecisionDiscoveryReport.opportunity_id == opportunity_id)
            .order_by(DecisionDiscoveryReport.created_at.desc())
            .limit(1)
        )

    async def report_bundle(self, report: DecisionDiscoveryReport) -> dict[str, Any]:
        makers = list(
            (
                await self.session.scalars(
                    select(DecisionMaker)
                    .where(DecisionMaker.discovery_report_id == report.id)
                    .order_by(DecisionMaker.buyer_match_score.desc(), DecisionMaker.seniority_rank.desc())
                )
            ).all()
        )
        departments = list(
            (
                await self.session.scalars(
                    select(CompanyDepartment).where(CompanyDepartment.discovery_report_id == report.id)
                )
            ).all()
        )
        channels = list(
            (
                await self.session.scalars(
                    select(CompanyContactChannel)
                    .where(CompanyContactChannel.discovery_report_id == report.id)
                    .order_by(CompanyContactChannel.rank.asc())
                )
            ).all()
        )
        profiles = list(
            (
                await self.session.scalars(
                    select(CompanyPublicProfile).where(CompanyPublicProfile.discovery_report_id == report.id)
                )
            ).all()
        )
        leadership = list(
            (
                await self.session.scalars(
                    select(CompanyLeadership).where(CompanyLeadership.discovery_report_id == report.id)
                )
            ).all()
        )
        confidence = await self.session.scalar(
            select(DecisionConfidence)
            .where(DecisionConfidence.discovery_report_id == report.id)
            .limit(1)
        )
        return {
            "report": report,
            "decision_makers": makers,
            "departments": departments,
            "contact_channels": channels,
            "public_profiles": profiles,
            "leadership": leadership,
            "confidence": confidence,
        }

    async def search(
        self,
        *,
        query: str | None,
        role: str | None,
        limit: int,
        offset: int,
    ) -> list[DecisionMaker]:
        stmt = select(DecisionMaker)
        if query:
            pattern = f"%{query.strip()}%"
            stmt = stmt.where(or_(DecisionMaker.name.ilike(pattern), DecisionMaker.role.ilike(pattern)))
        if role:
            stmt = stmt.where(DecisionMaker.normalized_role.ilike(role.strip()))
        stmt = stmt.order_by(DecisionMaker.buyer_match_score.desc(), DecisionMaker.created_at.desc()).offset(offset).limit(limit)
        return list((await self.session.scalars(stmt)).all())

    async def _enrichment_people(self, enrichment_report_id: UUID | None, company_id: UUID) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if enrichment_report_id is not None:
            people = (
                await self.session.scalars(
                    select(CompanyPerson).where(CompanyPerson.enrichment_report_id == enrichment_report_id)
                )
            ).all()
            for person in people:
                rows.append(
                    {
                        "name": person.name,
                        "role": person.role,
                        "department": person.department,
                        "linkedin_url": person.linkedin_url,
                        "work_email": person.work_email,
                        "business_phone": person.business_phone,
                        "confidence": person.confidence,
                        "source": person.source,
                        "source_url": person.source_url,
                        "is_public": True,
                    }
                )
        if not rows:
            people = (
                await self.session.scalars(
                    select(CompanyPerson)
                    .where(CompanyPerson.company_id == company_id)
                    .order_by(CompanyPerson.created_at.desc())
                    .limit(50)
                )
            ).all()
            for person in people:
                rows.append(
                    {
                        "name": person.name,
                        "role": person.role,
                        "department": person.department,
                        "linkedin_url": person.linkedin_url,
                        "work_email": person.work_email,
                        "business_phone": person.business_phone,
                        "confidence": person.confidence,
                        "source": person.source,
                        "source_url": person.source_url,
                        "is_public": True,
                    }
                )
        return rows

    async def _enrichment_contacts(self, enrichment_report_id: UUID | None, company_id: UUID) -> list[dict[str, Any]]:
        stmt = select(CompanyContact).where(CompanyContact.is_public.is_(True))
        if enrichment_report_id is not None:
            stmt = stmt.where(CompanyContact.enrichment_report_id == enrichment_report_id)
        else:
            stmt = stmt.where(CompanyContact.company_id == company_id).limit(50)
        contacts = (await self.session.scalars(stmt)).all()
        return [
            {
                "kind": contact.kind,
                "value": contact.value,
                "label": contact.label,
                "confidence": contact.confidence,
                "source": contact.source,
                "source_url": contact.source_url,
                "is_public": contact.is_public,
            }
            for contact in contacts
        ]

    async def _enrichment_profiles(self, enrichment_report_id: UUID | None, company_id: UUID) -> list[dict[str, Any]]:
        stmt = select(CompanySocialProfile)
        if enrichment_report_id is not None:
            stmt = stmt.where(CompanySocialProfile.enrichment_report_id == enrichment_report_id)
        else:
            stmt = stmt.where(CompanySocialProfile.company_id == company_id).limit(50)
        profiles = (await self.session.scalars(stmt)).all()
        return [
            {
                "platform": profile.platform,
                "url": profile.url,
                "handle": profile.handle,
                "confidence": profile.confidence,
                "source": profile.source,
            }
            for profile in profiles
        ]

    async def _known_people(self, company_id: UUID) -> list[dict[str, Any]]:
        people = (
            await self.session.scalars(select(Person).where(Person.company_id == company_id).limit(50))
        ).all()
        rows: list[dict[str, Any]] = []
        for person in people:
            attributes = dict(person.attributes or {})
            rows.append(
                {
                    "name": person.name,
                    "title": person.title,
                    "role": person.title,
                    "linkedin_url": attributes.get("linkedin_url"),
                    "email": attributes.get("email"),
                    "confidence": float(attributes.get("confidence") or 70.0),
                    "source": "beacon_intelligence",
                    "is_public": True,
                }
            )
        return rows
