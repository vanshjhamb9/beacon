from __future__ import annotations

from client_execution.models.types import ClientExecutionInput, KnowledgeRecord


class ClientKnowledgeBaseEngine:
    RECORD_TYPES = {
        "requirement",
        "meeting_note",
        "architecture",
        "document",
        "revision",
        "feedback",
        "approval",
    }

    def build(self, item: ClientExecutionInput) -> list[KnowledgeRecord]:
        records: list[KnowledgeRecord] = []
        for req in item.requirements:
            records.append(self._rec("requirement", req, req, ["requirements"]))
        for note in item.meeting_history:
            title = str(note.get("summary") if isinstance(note, dict) else note)
            records.append(self._rec("meeting_note", title, title, ["meetings"]))
        for note in item.architecture_notes:
            records.append(self._rec("architecture", note, note, ["architecture"]))
        for doc in item.documents:
            records.append(self._rec("document", doc, doc, ["documents"]))
        for rev in item.revisions:
            records.append(self._rec("revision", rev, rev, ["revisions"]))
        for fb in item.feedback:
            records.append(self._rec("feedback", fb, fb, ["feedback"]))
        for ap in item.approvals:
            records.append(self._rec("approval", ap, ap, ["approvals"]))
        for note in item.founder_notes:
            records.append(self._rec("meeting_note", f"Founder: {note}", note, ["founder"]))
        return records

    def search(self, records: list[KnowledgeRecord], query: str) -> list[KnowledgeRecord]:
        q = query.strip().lower()
        if not q:
            return list(records)
        return [r for r in records if q in r.searchable_text]

    def _rec(self, rtype: str, title: str, body: str, tags: list[str]) -> KnowledgeRecord:
        searchable = " ".join([rtype, title, body, *tags]).lower()
        return KnowledgeRecord(
            record_type=rtype if rtype in self.RECORD_TYPES else "document",
            title=title[:200],
            body=body[:2000],
            tags=tags,
            searchable_text=searchable,
            evidence=[f"type:{rtype}", "append_only:true"],
        )
