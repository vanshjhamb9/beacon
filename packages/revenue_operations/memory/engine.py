from __future__ import annotations

from revenue_operations.models.types import MemoryRecord, RevenueOperationsInput


class AgencyMemoryEngine:
    """Append-only searchable agency memory composed from opportunity signals."""

    RECORD_TYPES = {
        "meeting",
        "email",
        "reply",
        "proposal",
        "negotiation",
        "objection",
        "pricing",
        "industry",
        "service",
        "case_study",
        "client",
        "founder_note",
    }

    def build(self, item: RevenueOperationsInput) -> list[MemoryRecord]:
        records: list[MemoryRecord] = []
        for seed in item.memory_seeds:
            rtype = str(seed.get("record_type") or "founder_note")
            title = str(seed.get("title") or rtype)
            body = str(seed.get("body") or "")
            tags = list(seed.get("tags") or [])
            searchable = " ".join([rtype, title, body, *tags]).lower()
            records.append(
                MemoryRecord(
                    record_type=rtype if rtype in self.RECORD_TYPES else "founder_note",
                    company_id=seed.get("company_id"),
                    company_name=str(seed.get("company_name") or "") or None,
                    title=title,
                    body=body,
                    tags=tags,
                    searchable_text=searchable,
                    evidence=["source:seed"],
                )
            )
        for opp in item.opportunities:
            if opp.meeting_today or opp.meeting_count:
                records.append(self._rec("meeting", opp, f"Meeting activity ({opp.meeting_count})", "calendar"))
            if opp.reply_waiting:
                records.append(self._rec("reply", opp, "Reply waiting", "inbox"))
            if opp.proposal_pending or opp.proposal_count:
                records.append(self._rec("proposal", opp, f"Proposal activity ({opp.proposal_count})", "proposal"))
            if opp.negotiation:
                records.append(self._rec("negotiation", opp, "Negotiation active", "commercial"))
            for obj in opp.objections:
                records.append(self._rec("objection", opp, obj, "objection"))
            if opp.budget:
                records.append(self._rec("pricing", opp, opp.budget, "pricing"))
            if opp.industry:
                records.append(self._rec("industry", opp, opp.industry, "industry"))
            if opp.service:
                records.append(self._rec("service", opp, opp.service, "service"))
            if opp.won:
                records.append(self._rec("client", opp, "Won client", "won"))
            for note in opp.founder_notes:
                records.append(self._rec("founder_note", opp, note, "founder"))
        return records

    def search(self, records: list[MemoryRecord], query: str) -> list[MemoryRecord]:
        q = query.strip().lower()
        if not q:
            return list(records)
        return [r for r in records if q in r.searchable_text]

    def _rec(self, rtype: str, opp, title: str, tag: str) -> MemoryRecord:
        body = f"{opp.company_name} · {opp.stage or 'n/a'} · p={opp.probability}"
        searchable = " ".join([rtype, title, body, tag, opp.company_name, opp.industry or "", opp.service or ""]).lower()
        return MemoryRecord(
            record_type=rtype,
            company_id=opp.company_id,
            company_name=opp.company_name,
            title=title[:200],
            body=body,
            tags=[tag],
            searchable_text=searchable,
            evidence=[f"opp:{opp.opportunity_id or opp.company_id or opp.company_name}"],
        )
