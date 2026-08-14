from __future__ import annotations

import hashlib

from global_opportunity_acquisition.company_resolution.engine import CompanyResolutionEngine
from global_opportunity_acquisition.models.types import (
    CommunitySignal,
    CompanyObservation,
    DetectedIntent,
    FundingEvent,
    GraphEdge,
    GraphNode,
    GraphNodeType,
    HiringInsight,
    OpportunityGraph,
    ReviewSignal,
    TechnologyHit,
    WebsiteProfile,
)


class OpportunityGraphEngine:
    """Append-only opportunity graph builder for a company."""

    def build(
        self,
        company: CompanyObservation,
        *,
        intents: list[DetectedIntent],
        technologies: list[TechnologyHit],
        website: WebsiteProfile | None,
        hiring: HiringInsight | None,
        funding: list[FundingEvent],
        reviews: ReviewSignal | None,
        community: CommunitySignal | None,
    ) -> OpportunityGraph:
        resolver = CompanyResolutionEngine()
        key = resolver.resolve(company.company_name, company.company_domain)
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        def add(node_type: GraphNodeType, label: str, payload: dict | None = None) -> str:
            nid = hashlib.sha256(f"{key}|{node_type.value}|{label}".encode()).hexdigest()[:16]
            nodes.append(
                GraphNode(
                    node_id=nid,
                    node_type=node_type,
                    label=label,
                    payload=payload or {},
                    evidence=[f"type:{node_type.value}", "append_only:true"],
                )
            )
            return nid

        def link(src: str, tgt: str, relation: str) -> None:
            eid = hashlib.sha256(f"{src}|{tgt}|{relation}".encode()).hexdigest()[:16]
            edges.append(GraphEdge(edge_id=eid, source_id=src, target_id=tgt, relation=relation, evidence=[f"rel:{relation}"]))

        company_id = add(GraphNodeType.COMPANY, company.company_name, {"domain": company.company_domain})
        if company.industry:
            ind = add(GraphNodeType.INDUSTRY, company.industry)
            link(company_id, ind, "in_industry")
        for ev in funding:
            fid = add(GraphNodeType.FUNDING, ev.round, {"confidence": ev.confidence})
            link(company_id, fid, "has_funding")
        if hiring and (hiring.roles or hiring.growth > 0):
            hid = add(GraphNodeType.HIRING, f"growth:{hiring.growth}", hiring.model_dump())
            link(company_id, hid, "has_hiring")
        for tech in technologies:
            tid = add(GraphNodeType.TECHNOLOGY, tech.technology, {"category": tech.category})
            link(company_id, tid, "uses_technology")
        for dm in company.decision_makers[:8]:
            did = add(GraphNodeType.DECISION_MAKER, dm)
            link(company_id, did, "has_decision_maker")
        if website:
            wid = add(GraphNodeType.WEBSITE, website.domain or company.company_name, {"opportunity_score": website.opportunity_score})
            link(company_id, wid, "has_website")
        for intent in intents:
            bid = add(GraphNodeType.BUYING_SIGNAL, intent.intent.value, {"confidence": intent.confidence})
            link(company_id, bid, "has_buying_signal")
        if reviews:
            for pain in reviews.pain_points[:8]:
                pid = add(GraphNodeType.PAIN_POINT, pain)
                link(company_id, pid, "has_pain_point")
            for comp in reviews.competitor_mentions[:8]:
                cid = add(GraphNodeType.COMPETITOR, comp)
                link(company_id, cid, "mentions_competitor")
        if community:
            for need in community.needs[:8]:
                pid = add(GraphNodeType.PAIN_POINT, need)
                link(company_id, pid, "community_need")
        for c in company.campaigns[:5]:
            cid = add(GraphNodeType.CAMPAIGN, c)
            link(company_id, cid, "has_campaign")
        for m in company.meetings[:5]:
            mid = add(GraphNodeType.MEETING, m)
            link(company_id, mid, "has_meeting")
        for r in company.revenue_notes[:5]:
            rid = add(GraphNodeType.REVENUE, r)
            link(company_id, rid, "has_revenue")
        for h in company.history[:5]:
            hid = add(GraphNodeType.HISTORY, h)
            link(company_id, hid, "has_history")
        for o in company.outcomes[:5]:
            oid = add(GraphNodeType.OUTCOME, o)
            link(company_id, oid, "has_outcome")

        return OpportunityGraph(
            company_key=key,
            company_name=company.company_name,
            nodes=nodes,
            edges=edges,
            evidence=[f"nodes:{len(nodes)}", f"edges:{len(edges)}", "append_only:true"],
        )
