from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from account_intelligence.models.types import (
    AccountIntelligenceInput,
    CommitteeMember,
    ContactValidationResult,
    GraphEdge,
    GraphNode,
    RelationshipGraph,
    TechnologyProfile,
    TimelineEvent,
    VerificationRecord,
)


class RelationshipGraphEngine:
    def build(
        self,
        item: AccountIntelligenceInput,
        *,
        committee: list[CommitteeMember],
        verified: list[ContactValidationResult],
        tech: TechnologyProfile,
        departments: list[str],
    ) -> RelationshipGraph:
        key = hashlib.sha256((item.domain or item.company_name).lower().encode()).hexdigest()[:16]
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        def add(ntype: str, label: str, payload: dict | None = None) -> str:
            nid = hashlib.sha256(f"{key}|{ntype}|{label}".encode()).hexdigest()[:16]
            nodes.append(GraphNode(node_id=nid, node_type=ntype, label=label, payload=payload or {}, evidence=[f"type:{ntype}", "append_only:true"]))
            return nid

        def link(a: str, b: str, rel: str) -> None:
            eid = hashlib.sha256(f"{a}|{b}|{rel}".encode()).hexdigest()[:16]
            edges.append(GraphEdge(edge_id=eid, source_id=a, target_id=b, relation=rel, evidence=[f"rel:{rel}"]))

        company = add("company", item.company_name)
        for dept in departments[:12]:
            link(company, add("department", dept), "has_department")
        for m in committee[:20]:
            mid = add("decision_maker", m.full_name, {"role": m.role})
            link(company, mid, "has_decision_maker")
        for t in (tech.frontend + tech.backend + tech.crm + tech.ai_stack)[:20]:
            link(company, add("technology", t), "uses_technology")
        for c in item.campaigns[:8]:
            link(company, add("campaign", c), "has_campaign")
        for e in item.emails[:8]:
            link(company, add("email", e), "has_email")
        for r in item.replies[:8]:
            link(company, add("reply", r), "has_reply")
        for m in item.meetings[:8]:
            link(company, add("meeting", m), "has_meeting")
        for p in item.proposals[:8]:
            link(company, add("proposal", p), "has_proposal")
        for r in item.revenue_notes[:8]:
            link(company, add("revenue", r), "has_revenue")
        for r in item.referrals[:8]:
            link(company, add("referral", r), "has_referral")
        for h in item.history[:8]:
            link(company, add("history", h), "has_history")
        for v in verified[:10]:
            if v.accepted:
                link(company, add("verified_contact", v.full_name), "has_verified_contact")
        return RelationshipGraph(company_key=key, nodes=nodes, edges=edges, evidence=[f"nodes:{len(nodes)}", "append_only:true"])


class VerificationEngine:
    def history(
        self,
        *,
        profile_fields: dict[str, tuple[float, str]],
        verified_contacts: list[ContactValidationResult],
        now: datetime | None = None,
    ) -> list[VerificationRecord]:
        now = now or datetime.now(UTC)
        out: list[VerificationRecord] = []
        for name, (conf, source) in profile_fields.items():
            out.append(
                VerificationRecord(
                    field=name,
                    status="verified" if conf >= 70 else ("observed" if conf > 0 else "missing"),
                    source=source,
                    confidence=conf,
                    last_verified=now if conf > 0 else None,
                    evidence=[f"field:{name}"],
                )
            )
        for c in verified_contacts:
            out.append(
                VerificationRecord(
                    field=f"contact:{c.full_name}",
                    status=c.verification,
                    source=c.source,
                    confidence=c.confidence,
                    last_verified=c.last_verified or now,
                    evidence=list(c.evidence),
                )
            )
        return out


class TimelineEngine:
    def build(self, item: AccountIntelligenceInput, *, events: list[str] | None = None) -> list[TimelineEvent]:
        now = item.now or datetime.now(UTC)
        out: list[TimelineEvent] = [
            TimelineEvent(event_type="enrichment", title="Account intelligence evaluated", timestamp=now, evidence=["aip:v1"]),
        ]
        for label in events or []:
            out.append(TimelineEvent(event_type="signal", title=label, timestamp=now, evidence=["append_only:true"]))
        for m in item.meetings[:5]:
            out.append(TimelineEvent(event_type="meeting", title=m, timestamp=now, evidence=["source:input"]))
        return out


class CompanyStructureEngine:
    def departments(self, committee: list[CommitteeMember]) -> list[str]:
        deps = []
        for m in committee:
            if m.department:
                deps.append(m.department)
            elif m.role:
                deps.append(m.role.split()[0] if m.role else "General")
        # map common roles to departments
        mapped = []
        for m in committee:
            role = m.role.lower()
            if "engineer" in role or "cto" in role or "ai" in role:
                mapped.append("Engineering")
            elif "market" in role:
                mapped.append("Marketing")
            elif "sales" in role:
                mapped.append("Sales")
            elif "finance" in role:
                mapped.append("Finance")
            elif "operat" in role or "coo" in role:
                mapped.append("Operations")
            elif "ceo" in role or "founder" in role:
                mapped.append("Executive")
            elif m.department:
                mapped.append(m.department)
        return list(dict.fromkeys(mapped + deps))[:20]


class CompanyLocationsEngine:
    def from_profile(self, locations):
        return list(locations)
