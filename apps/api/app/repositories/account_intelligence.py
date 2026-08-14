from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_intelligence import (
    AIPBuyingCommitteeRow,
    AIPCompanyLocationRow,
    AIPTechnologyProfileRow,
    AIReadinessReportRow,
    AccountProfileRow,
    BusinessProfileRow,
    CompanyDepartmentRow,
    ConfidenceReportRow,
    ContactVerificationRow,
    FieldSourceRow,
    FinancialProfileRow,
    GrowthProfileRow,
    IndustryBenchmarkRow,
    RelationshipGraphEdgeRow,
    RelationshipGraphNodeRow,
    SalesReadinessReportRow,
    VerificationHistoryRow,
    VerifiedContactRow,
    WebsiteProfileV2Row,
)
from app.models.decision import DecisionMaker
from app.models.intelligence import Company
from account_intelligence import AccountIntelligenceService
from account_intelligence.models.types import AccountIntelligenceDecision, AccountIntelligenceInput, ObservedContact


class AccountIntelligenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def build_input(self, company_id: UUID) -> AccountIntelligenceInput | None:
        company = await self.session.get(Company, company_id)
        if company is None:
            return None
        attrs = company.attributes or {}
        dms = list(
            (await self.session.execute(select(DecisionMaker).where(DecisionMaker.company_id == company_id).limit(20)))
            .scalars()
            .all()
        )
        contacts = []
        for dm in dms:
            contacts.append(
                ObservedContact(
                    full_name=dm.name,
                    role=dm.role,
                    business_email=dm.work_email,
                    source="decision_makers",
                    evidence=[f"dm_id:{dm.id}", "fabricated:false"],
                )
            )
        for raw in attrs.get("observed_contacts") or []:
            if isinstance(raw, dict) and raw.get("full_name") and raw.get("source"):
                contacts.append(ObservedContact.model_validate(raw))
        return AccountIntelligenceInput(
            company_id=company.id,
            company_name=company.name,
            website=str(attrs.get("website") or "") or None,
            domain=str(attrs.get("domain") or "") or None,
            legal_name=str(attrs.get("legal_name") or "") or None,
            industry=company.industry,
            sub_industry=str(attrs.get("sub_industry") or "") or None,
            business_model=str(attrs.get("business_model") or "") or None,
            country=str(attrs.get("country") or "") or None,
            state=str(attrs.get("state") or "") or None,
            city=str(attrs.get("city") or "") or None,
            founded=str(attrs.get("founded") or "") or None,
            employee_count=int(attrs["employee_count"]) if attrs.get("employee_count") is not None else None,
            revenue_estimate=float(attrs["revenue_estimate"]) if attrs.get("revenue_estimate") is not None else None,
            funding=str(attrs.get("funding") or "") or None,
            latest_funding_round=str(attrs.get("latest_funding_round") or "") or None,
            investors=list(attrs.get("investors") or []),
            offices=list(attrs.get("offices") or []),
            locations=list(attrs.get("locations") or []),
            time_zone=str(attrs.get("time_zone") or "") or None,
            languages=list(attrs.get("languages") or []),
            parent_company=str(attrs.get("parent_company") or "") or None,
            subsidiaries=list(attrs.get("subsidiaries") or []),
            is_public=attrs.get("is_public") if "is_public" in attrs else None,
            ipo_status=str(attrs.get("ipo_status") or "") or None,
            annual_growth=float(attrs["annual_growth"]) if attrs.get("annual_growth") is not None else None,
            hiring_trend=float(attrs["hiring_trend"]) if attrs.get("hiring_trend") is not None else None,
            expansion_score=float(attrs["expansion_score"]) if attrs.get("expansion_score") is not None else None,
            html_hints=list(attrs.get("html_hints") or []),
            tech_hints=list(attrs.get("tech_hints") or []),
            observed_contacts=contacts,
            campaigns=list(attrs.get("campaigns") or []),
            emails=list(attrs.get("emails") or []),
            replies=list(attrs.get("replies") or []),
            meetings=list(attrs.get("meetings") or []),
            proposals=list(attrs.get("proposals") or []),
            revenue_notes=list(attrs.get("revenue_notes") or []),
            referrals=list(attrs.get("referrals") or []),
            history=list(attrs.get("history") or []),
            buying_intent=float(attrs.get("buying_intent") or 50),
            source_attribution=str(attrs.get("source_attribution") or "goap"),
            field_sources=dict(attrs.get("field_sources") or {}),
        )

    async def store_decision(self, decision: AccountIntelligenceDecision) -> AccountProfileRow:
        key = decision.relationship_graph.company_key
        row = AccountProfileRow(
            company_id=decision.company_id,
            company_name=decision.company_name,
            domain=str(decision.profile.website.value or "") or None,
            sales_readiness_score=decision.sales_readiness.score,
            sales_readiness_category=decision.sales_readiness.category.value,
            ai_readiness_score=decision.ai_readiness.overall,
            overall_confidence=decision.confidence.overall,
            payload=decision.model_dump(mode="json"),
            evidence_chain=list(decision.evidence_chain),
            scoring_version=decision.scoring_version,
        )
        self.session.add(row)
        for loc in decision.locations[:20]:
            self.session.add(
                AIPCompanyLocationRow(company_key=key, label=loc.label, payload=loc.model_dump(mode="json"), evidence=list(loc.evidence))
            )
        for dept in decision.departments[:20]:
            self.session.add(CompanyDepartmentRow(company_key=key, name=dept, payload={"name": dept}, evidence=["structure:aip"]))
        for m in decision.buying_committee[:50]:
            self.session.add(
                AIPBuyingCommitteeRow(
                    company_key=key,
                    full_name=m.full_name,
                    role=m.role,
                    confidence=m.confidence,
                    fabricated=False,
                    payload=m.model_dump(mode="json"),
                    evidence=list(m.evidence),
                )
            )
        for c in decision.verified_contacts[:50]:
            self.session.add(
                VerifiedContactRow(
                    company_key=key,
                    full_name=c.full_name,
                    business_email=c.business_email,
                    accepted=c.accepted,
                    confidence=c.confidence,
                    payload=c.model_dump(mode="json"),
                    evidence=list(c.evidence),
                )
            )
            self.session.add(
                ContactVerificationRow(
                    company_key=key,
                    field=c.full_name,
                    status=c.verification,
                    payload=c.model_dump(mode="json"),
                    evidence=list(c.evidence),
                )
            )
        self.session.add(
            AIPTechnologyProfileRow(
                company_key=key,
                confidence=decision.technology.confidence,
                payload=decision.technology.model_dump(mode="json"),
                evidence=list(decision.technology.evidence),
            )
        )
        self.session.add(
            WebsiteProfileV2Row(
                company_key=key,
                confidence=decision.website.confidence,
                payload=decision.website.model_dump(mode="json"),
                evidence=list(decision.website.evidence),
            )
        )
        self.session.add(
            FinancialProfileRow(company_key=key, payload=decision.financial.model_dump(mode="json"), evidence=list(decision.financial.evidence))
        )
        self.session.add(
            BusinessProfileRow(
                company_key=key,
                growth_stage=decision.business.growth_stage,
                payload=decision.business.model_dump(mode="json"),
                evidence=list(decision.business.evidence),
            )
        )
        self.session.add(
            GrowthProfileRow(company_key=key, payload=decision.growth.model_dump(mode="json"), evidence=list(decision.growth.evidence))
        )
        self.session.add(
            AIReadinessReportRow(
                company_key=key,
                overall=decision.ai_readiness.overall,
                payload=decision.ai_readiness.model_dump(mode="json"),
                evidence=list(decision.ai_readiness.evidence),
            )
        )
        self.session.add(
            SalesReadinessReportRow(
                company_key=key,
                score=decision.sales_readiness.score,
                category=decision.sales_readiness.category.value,
                payload=decision.sales_readiness.model_dump(mode="json"),
                evidence=list(decision.sales_readiness.evidence),
            )
        )
        for n in decision.relationship_graph.nodes[:200]:
            self.session.add(
                RelationshipGraphNodeRow(
                    company_key=key,
                    node_id=n.node_id,
                    node_type=n.node_type,
                    label=n.label,
                    payload=n.payload,
                    evidence=list(n.evidence),
                    immutable=True,
                )
            )
        for e in decision.relationship_graph.edges[:400]:
            self.session.add(
                RelationshipGraphEdgeRow(
                    company_key=key,
                    edge_id=e.edge_id,
                    source_id=e.source_id,
                    target_id=e.target_id,
                    relation=e.relation,
                    evidence=list(e.evidence),
                    immutable=True,
                )
            )
        self.session.add(
            ConfidenceReportRow(
                company_key=key,
                overall=decision.confidence.overall,
                payload=decision.confidence.model_dump(mode="json"),
                evidence=list(decision.confidence.evidence),
            )
        )
        for v in decision.verification_history[:100]:
            self.session.add(
                VerificationHistoryRow(
                    company_key=key,
                    field=v.field,
                    status=v.status,
                    payload=v.model_dump(mode="json"),
                    evidence=list(v.evidence),
                )
            )
            self.session.add(
                FieldSourceRow(
                    company_key=key,
                    field=v.field,
                    source=v.source,
                    confidence=v.confidence,
                    payload=v.model_dump(mode="json"),
                    evidence=list(v.evidence),
                )
            )
        if decision.industry_benchmark:
            self.session.add(
                IndustryBenchmarkRow(
                    industry=decision.industry_benchmark.industry,
                    payload=decision.industry_benchmark.model_dump(mode="json"),
                    evidence=list(decision.industry_benchmark.evidence),
                )
            )
        await self.session.flush()
        return row

    async def latest_for_company(self, company_id: UUID) -> AccountProfileRow | None:
        return await self.session.scalar(
            select(AccountProfileRow).where(AccountProfileRow.company_id == company_id).order_by(AccountProfileRow.created_at.desc()).limit(1)
        )

    async def recent(self, *, limit: int = 50) -> list[AccountProfileRow]:
        return list(
            (await self.session.execute(select(AccountProfileRow).order_by(AccountProfileRow.created_at.desc()).limit(limit)))
            .scalars()
            .all()
        )

    async def company_ids(self, *, limit: int = 40) -> list[UUID]:
        return list((await self.session.execute(select(Company.id).order_by(Company.updated_at.desc()).limit(limit))).scalars().all())
