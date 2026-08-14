from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intelligence import (
    ClassifiedSignal,
    Company,
    CompanyAlias,
    CompanyTimeline,
    Domain,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    SignalEntity,
)


class IntelligenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_companies(self, *, limit: int = 100, offset: int = 0) -> Sequence[Company]:
        result = await self.session.execute(
            select(Company)
            .where(Company.deleted_at.is_(None))
            .order_by(Company.last_seen_at.desc().nullslast(), Company.name)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_company(self, company_id: UUID) -> Company | None:
        result = await self.session.execute(
            select(Company).where(Company.id == company_id, Company.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def company_names(self) -> list[str]:
        result = await self.session.execute(select(Company.name).where(Company.deleted_at.is_(None)))
        return list(result.scalars().all())

    async def alias_map(self) -> dict[str, str]:
        result = await self.session.execute(
            select(CompanyAlias.normalized_alias, Company.name).join(
                Company,
                Company.id == CompanyAlias.company_id,
            )
        )
        return {alias: name for alias, name in result.all()}

    async def domain_map(self) -> dict[str, str]:
        result = await self.session.execute(
            select(Domain.domain, Company.name).join(Company, Company.id == Domain.company_id)
        )
        return {domain: name for domain, name in result.all()}

    async def upsert_company(
        self,
        *,
        name: str,
        normalized_name: str,
        primary_domain: str | None,
        last_seen_at: datetime,
        attributes: dict[str, Any],
    ) -> Company:
        statement = (
            insert(Company)
            .values(
                name=name,
                normalized_name=normalized_name,
                primary_domain=primary_domain,
                last_seen_at=last_seen_at,
                signal_frequency=0,
                attributes=attributes,
            )
            .on_conflict_do_update(
                index_elements=["normalized_name"],
                set_={
                    "last_seen_at": func.greatest(Company.last_seen_at, last_seen_at),
                    "primary_domain": func.coalesce(Company.primary_domain, primary_domain),
                },
            )
            .returning(Company.id)
        )
        result = await self.session.execute(statement)
        company_id = result.scalar_one()
        company = await self.get_company(company_id)
        if company is None:
            raise LookupError("Company upsert did not return a readable company.")
        return company

    async def update_company_memory(
        self,
        company: Company,
        *,
        last_seen_at: datetime,
        signal_frequency_increment: int,
        memory_summary: str,
        attributes: dict[str, Any],
    ) -> Company:
        company.last_seen_at = last_seen_at
        company.signal_frequency += signal_frequency_increment
        company.memory_summary = memory_summary
        company.attributes = attributes
        await self.session.flush()
        await self.session.refresh(company)
        return company

    async def upsert_domain(
        self,
        *,
        domain: str,
        company_id: UUID,
        seen_at: datetime,
        confidence: float,
        evidence: dict[str, Any],
    ) -> Domain:
        statement = (
            insert(Domain)
            .values(
                domain=domain,
                company_id=company_id,
                first_seen_at=seen_at,
                last_seen_at=seen_at,
                confidence=confidence,
                evidence=evidence,
            )
            .on_conflict_do_update(
                index_elements=["domain"],
                set_={"last_seen_at": seen_at, "confidence": func.greatest(Domain.confidence, confidence)},
            )
            .returning(Domain.id)
        )
        result = await self.session.execute(statement)
        domain_id = result.scalar_one()
        domain_model = await self.session.get(Domain, domain_id)
        if domain_model is None:
            raise LookupError("Domain upsert did not return a readable domain.")
        return domain_model

    async def insert_signal_entity(self, values: dict[str, Any]) -> SignalEntity:
        entity = SignalEntity(**values)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def insert_classified_signal_once(self, values: dict[str, Any]) -> bool:
        statement = (
            insert(ClassifiedSignal.__table__)
            .values(**values)
            .on_conflict_do_nothing(
                index_elements=["event_id", "company_id", "category"],
            )
        )
        result = await self.session.execute(statement)
        return result.rowcount == 1

    async def insert_timeline_once(self, values: dict[str, Any]) -> bool:
        statement = (
            insert(CompanyTimeline.__table__)
            .values(**values)
            .on_conflict_do_nothing(
                index_elements=["company_id", "event_id", "signal_type"],
            )
        )
        result = await self.session.execute(statement)
        return result.rowcount == 1

    async def upsert_graph_node(
        self,
        *,
        node_type: str,
        external_id: str,
        label: str,
        properties: dict[str, Any],
    ) -> UUID:
        statement = (
            insert(KnowledgeGraphNode)
            .values(node_type=node_type, external_id=external_id, label=label, properties=properties)
            .on_conflict_do_update(
                index_elements=["node_type", "external_id"],
                set_={"label": label, "properties": properties},
            )
            .returning(KnowledgeGraphNode.id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def insert_graph_edge_once(
        self,
        *,
        from_node_id: UUID,
        to_node_id: UUID,
        edge_type: str,
        confidence: float,
        evidence_event_id: UUID | None,
        properties: dict[str, Any],
    ) -> bool:
        statement = (
            insert(KnowledgeGraphEdge.__table__)
            .values(
                from_node_id=from_node_id,
                to_node_id=to_node_id,
                edge_type=edge_type,
                confidence=confidence,
                evidence_event_id=evidence_event_id,
                properties=properties,
            )
            .on_conflict_do_nothing(
                index_elements=["from_node_id", "to_node_id", "edge_type"],
            )
        )
        result = await self.session.execute(statement)
        return result.rowcount == 1

    async def company_timeline(self, company_id: UUID, *, limit: int = 100) -> Sequence[CompanyTimeline]:
        result = await self.session.execute(
            select(CompanyTimeline)
            .where(CompanyTimeline.company_id == company_id)
            .order_by(CompanyTimeline.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def company_signals(self, company_id: UUID, *, limit: int = 100) -> Sequence[ClassifiedSignal]:
        result = await self.session.execute(
            select(ClassifiedSignal)
            .where(ClassifiedSignal.company_id == company_id)
            .order_by(ClassifiedSignal.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def list_signals(
        self,
        *,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ClassifiedSignal]:
        query: Select[tuple[ClassifiedSignal]] = select(ClassifiedSignal)
        if category:
            query = query.where(ClassifiedSignal.category == category)
        result = await self.session.execute(
            query.order_by(ClassifiedSignal.created_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def knowledge_node(self, node_id: UUID) -> KnowledgeGraphNode | None:
        return await self.session.get(KnowledgeGraphNode, node_id)

    async def knowledge_edges(self, node_id: UUID) -> Sequence[KnowledgeGraphEdge]:
        result = await self.session.execute(
            select(KnowledgeGraphEdge).where(
                (KnowledgeGraphEdge.from_node_id == node_id) | (KnowledgeGraphEdge.to_node_id == node_id)
            )
        )
        return result.scalars().all()
