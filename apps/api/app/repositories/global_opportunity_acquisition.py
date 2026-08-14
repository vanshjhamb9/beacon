from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.global_opportunity_acquisition import (
    CommunitySignalRow,
    ConnectorBenchmarkRow,
    ConnectorHistoryRow,
    ConnectorScoreRow,
    FundingEventRow,
    HiringEventRow,
    OpportunityGraphEdgeRow,
    OpportunityGraphNodeRow,
    ReviewSignalRow,
    SourceAlertRow,
    SourceConnectorRow,
    SourceRunRow,
    TechnologyProfileRow,
    WebsiteProfileRow,
)
from app.models.intelligence import Company
from global_opportunity_acquisition import GlobalOpportunityAcquisitionService
from global_opportunity_acquisition.connectors.catalog import connector_catalog
from global_opportunity_acquisition.models.types import (
    CompanyObservation,
    GOAPDecision,
    GOAPInput,
    RawSignal,
)


def _as_str_list(raw: Any) -> list[str]:
    """Normalize attribute lists to strings (RRP/ODU store decision_makers as dicts)."""
    if raw is None:
        return []
    if not isinstance(raw, list):
        raw = [raw]
    out: list[str] = []
    for item in raw:
        if item is None:
            continue
        if isinstance(item, str):
            text = item.strip()
            if text:
                out.append(text)
            continue
        if isinstance(item, dict):
            name = str(item.get("name") or item.get("full_name") or "").strip()
            role = str(item.get("role") or item.get("title") or item.get("job_title") or "").strip()
            if name and role:
                out.append(f"{name} ({role})")
            elif name:
                out.append(name)
            elif role:
                out.append(role)
            continue
        text = str(item).strip()
        if text:
            out.append(text)
    return out


class GlobalOpportunityAcquisitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def build_input(self, *, limit: int = 40) -> GOAPInput:
        companies = list(
            (await self.session.execute(select(Company).order_by(Company.updated_at.desc()).limit(limit))).scalars().all()
        )
        observations: list[CompanyObservation] = []
        signals: list[RawSignal] = []
        for company in companies:
            attrs = company.attributes or {}
            # Prefer domain from RRP/OFC attributes when legacy domain missing
            domain = (
                str(attrs.get("domain") or attrs.get("official_domain") or company.primary_domain or "").strip()
                or None
            )
            dms = _as_str_list(attrs.get("decision_makers"))
            if not dms and attrs.get("decision_maker"):
                dms = _as_str_list([attrs.get("decision_maker")])
            if not dms and isinstance(attrs.get("rrp_decision_maker"), dict):
                dms = _as_str_list([attrs.get("rrp_decision_maker")])
            obs = CompanyObservation(
                company_id=company.id,
                company_name=company.name,
                company_domain=domain,
                industry=company.industry or attrs.get("industry"),
                source_texts=_as_str_list(attrs.get("source_texts") or [company.name]),
                source_connector_ids=_as_str_list(attrs.get("source_connector_ids") or [attrs.get("source") or "rss"]),
                html_hints=_as_str_list(attrs.get("html_hints") or []),
                job_titles=_as_str_list(attrs.get("job_titles") or []),
                funding_text=_as_str_list(attrs.get("funding_text") or []),
                review_text=_as_str_list(attrs.get("review_text") or []),
                community_text=_as_str_list(attrs.get("community_text") or []),
                procurement_text=_as_str_list(attrs.get("procurement_text") or []),
                decision_makers=dms,
                competitors=_as_str_list(attrs.get("competitors") or []),
                campaigns=_as_str_list(attrs.get("campaigns") or []),
                meetings=_as_str_list(attrs.get("meetings") or []),
                revenue_notes=_as_str_list(attrs.get("revenue_notes") or []),
                outcomes=_as_str_list(attrs.get("outcomes") or []),
                history=_as_str_list(attrs.get("history") or []),
                verified=bool(attrs.get("verified") or attrs.get("rrp_revenue_ready") or company.primary_domain),
                last_seen_hours=float(attrs.get("last_seen_hours") or 24),
                engagement_score=float(attrs.get("engagement_score") or 50),
                activity_score=float(attrs.get("activity_score") or 50),
            )
            observations.append(obs)
            for cid in obs.source_connector_ids[:3]:
                signals.append(
                    RawSignal(
                        signal_id=f"{company.id}-{cid}",
                        connector_id=cid,
                        company_name=company.name,
                        company_domain=obs.company_domain,
                        title=company.name,
                        body=" ".join(obs.source_texts)[:500],
                    )
                )
        outcomes = {}
        for c in connector_catalog():
            outcomes[c.connector_id] = {
                "opportunities": 1 if c.status.value == "active" else 0,
                "quality": 60.0,
                "coverage": 40.0,
            }
        return GOAPInput(raw_signals=signals, companies=observations, connector_outcomes=outcomes)

    async def store_decision(self, decision: GOAPDecision) -> dict[str, Any]:
        for definition in connector_catalog():
            existing = await self.session.scalar(
                select(SourceConnectorRow).where(SourceConnectorRow.connector_id == definition.connector_id).limit(1)
            )
            if existing is None:
                self.session.add(
                    SourceConnectorRow(
                        connector_id=definition.connector_id,
                        connector_name=definition.connector_name,
                        access_mode=definition.access_mode.value,
                        status=definition.status.value,
                        category=definition.category,
                        payload=definition.model_dump(mode="json"),
                        evidence=[definition.notes],
                        scoring_version=decision.scoring_version,
                    )
                )
        for m in decision.connectors:
            self.session.add(
                SourceRunRow(
                    connector_id=m.connector_id,
                    signals_found=m.signals_found,
                    companies_found=m.companies_found,
                    opportunities_found=m.opportunities_found,
                    duplicates=m.duplicates,
                    latency_ms=m.latency_ms,
                    errors=m.errors,
                    payload=m.model_dump(mode="json"),
                    evidence=list(m.evidence),
                )
            )
            self.session.add(
                ConnectorScoreRow(
                    connector_id=m.connector_id,
                    quality_score=m.quality_score,
                    trust_score=m.trust_score,
                    coverage_score=m.coverage_score,
                    freshness_score=m.freshness_score,
                    roi_score=m.roi_score,
                    payload=m.model_dump(mode="json"),
                    evidence=list(m.evidence),
                )
            )
            self.session.add(
                ConnectorHistoryRow(
                    connector_id=m.connector_id,
                    event_type="score_refresh",
                    payload=m.model_dump(mode="json"),
                    evidence=list(m.evidence),
                    immutable=True,
                )
            )
        for b in decision.benchmarks:
            self.session.add(
                ConnectorBenchmarkRow(
                    connector_id=b.connector_id,
                    rank=b.rank,
                    recommendation=b.recommendation.value,
                    payload=b.model_dump(mode="json"),
                    evidence=list(b.evidence),
                )
            )
        for pack in decision.companies[:100]:
            key = pack.canonical_key
            if pack.graph:
                for node in pack.graph.nodes[:200]:
                    self.session.add(
                        OpportunityGraphNodeRow(
                            company_key=key,
                            node_id=node.node_id,
                            node_type=node.node_type.value,
                            label=node.label,
                            payload=node.payload,
                            evidence=list(node.evidence),
                            immutable=True,
                        )
                    )
                for edge in pack.graph.edges[:400]:
                    self.session.add(
                        OpportunityGraphEdgeRow(
                            company_key=key,
                            edge_id=edge.edge_id,
                            source_id=edge.source_id,
                            target_id=edge.target_id,
                            relation=edge.relation,
                            evidence=list(edge.evidence),
                            immutable=True,
                        )
                    )
            if pack.website:
                self.session.add(
                    WebsiteProfileRow(
                        company_key=key,
                        company_name=pack.company_name,
                        domain=pack.website.domain,
                        modernization_score=pack.website.modernization_score,
                        opportunity_score=pack.website.opportunity_score,
                        payload=pack.website.model_dump(mode="json"),
                        evidence=list(pack.website.evidence),
                    )
                )
            for tech in pack.technologies[:30]:
                self.session.add(
                    TechnologyProfileRow(
                        company_key=key,
                        technology=tech.technology,
                        category=tech.category,
                        confidence=tech.confidence,
                        payload=tech.model_dump(mode="json"),
                        evidence=list(tech.evidence),
                    )
                )
            for f in pack.funding[:10]:
                self.session.add(
                    FundingEventRow(
                        company_key=key,
                        round=f.round,
                        confidence=f.confidence,
                        payload=f.model_dump(mode="json"),
                        evidence=list(f.evidence),
                    )
                )
            if pack.hiring:
                self.session.add(
                    HiringEventRow(
                        company_key=key,
                        growth=pack.hiring.growth,
                        payload=pack.hiring.model_dump(mode="json"),
                        evidence=list(pack.hiring.evidence),
                    )
                )
            if pack.reviews:
                self.session.add(
                    ReviewSignalRow(
                        company_key=key,
                        payload=pack.reviews.model_dump(mode="json"),
                        evidence=list(pack.reviews.evidence),
                    )
                )
            if pack.community:
                self.session.add(
                    CommunitySignalRow(
                        company_key=key,
                        confidence=pack.community.confidence,
                        payload=pack.community.model_dump(mode="json"),
                        evidence=list(pack.community.evidence),
                    )
                )
        if decision.daily_report:
            for alert in decision.daily_report.alerts[:20]:
                self.session.add(
                    SourceAlertRow(
                        alert_type="benchmark",
                        message=alert,
                        connector_id=None,
                        payload={"alert": alert},
                        evidence=["daily_report"],
                    )
                )
        await self.session.flush()
        return {"companies": len(decision.companies), "connectors": len(decision.connectors)}

    async def list_connectors(self) -> list[SourceConnectorRow]:
        rows = list((await self.session.execute(select(SourceConnectorRow).order_by(SourceConnectorRow.connector_id))).scalars().all())
        if rows:
            return rows
        return []

    async def get_connector(self, connector_id: str) -> SourceConnectorRow | None:
        return await self.session.scalar(
            select(SourceConnectorRow).where(SourceConnectorRow.connector_id == connector_id).limit(1)
        )

    async def graph_for_company(self, company_key: str) -> dict[str, Any]:
        nodes = list(
            (
                await self.session.execute(
                    select(OpportunityGraphNodeRow)
                    .where(OpportunityGraphNodeRow.company_key == company_key)
                    .order_by(OpportunityGraphNodeRow.created_at.desc())
                    .limit(200)
                )
            )
            .scalars()
            .all()
        )
        edges = list(
            (
                await self.session.execute(
                    select(OpportunityGraphEdgeRow)
                    .where(OpportunityGraphEdgeRow.company_key == company_key)
                    .order_by(OpportunityGraphEdgeRow.created_at.desc())
                    .limit(400)
                )
            )
            .scalars()
            .all()
        )
        return {
            "company_key": company_key,
            "nodes": [{"node_id": n.node_id, "type": n.node_type, "label": n.label, "payload": n.payload} for n in nodes],
            "edges": [{"edge_id": e.edge_id, "source": e.source_id, "target": e.target_id, "relation": e.relation} for e in edges],
        }

    async def latest_websites(self, *, limit: int = 50) -> list[WebsiteProfileRow]:
        return list(
            (await self.session.execute(select(WebsiteProfileRow).order_by(WebsiteProfileRow.created_at.desc()).limit(limit)))
            .scalars()
            .all()
        )

    async def latest_tech(self, *, limit: int = 50) -> list[TechnologyProfileRow]:
        return list(
            (
                await self.session.execute(
                    select(TechnologyProfileRow).order_by(TechnologyProfileRow.created_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def latest_funding(self, *, limit: int = 50) -> list[FundingEventRow]:
        return list(
            (await self.session.execute(select(FundingEventRow).order_by(FundingEventRow.created_at.desc()).limit(limit)))
            .scalars()
            .all()
        )

    async def latest_hiring(self, *, limit: int = 50) -> list[HiringEventRow]:
        return list(
            (await self.session.execute(select(HiringEventRow).order_by(HiringEventRow.created_at.desc()).limit(limit)))
            .scalars()
            .all()
        )

    async def latest_reviews(self, *, limit: int = 50) -> list[ReviewSignalRow]:
        return list(
            (await self.session.execute(select(ReviewSignalRow).order_by(ReviewSignalRow.created_at.desc()).limit(limit)))
            .scalars()
            .all()
        )

    async def latest_community(self, *, limit: int = 50) -> list[CommunitySignalRow]:
        return list(
            (
                await self.session.execute(
                    select(CommunitySignalRow).order_by(CommunitySignalRow.created_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def latest_benchmarks(self, *, limit: int = 50) -> list[ConnectorBenchmarkRow]:
        return list(
            (
                await self.session.execute(
                    select(ConnectorBenchmarkRow).order_by(ConnectorBenchmarkRow.created_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def company_by_id(self, company_id: UUID) -> Company | None:
        return await self.session.get(Company, company_id)
