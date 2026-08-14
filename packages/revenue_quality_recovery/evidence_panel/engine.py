from __future__ import annotations

from typing import Any

from revenue_quality_recovery.models.types import EvidenceItem, EvidencePanel, UNKNOWN


class EvidencePanelEngine:
    """Rule 6 — founder-visible evidence: collected_from, URL, date, collector, evidence, reason."""

    def build(self, payload: dict[str, Any]) -> EvidencePanel:
        items: list[EvidenceItem] = []
        evidence: list[str] = []

        for row in payload.get("evidence_timeline") or payload.get("timeline") or []:
            if isinstance(row, dict):
                items.append(
                    EvidenceItem(
                        collected_from=str(row.get("collected_from") or row.get("source") or payload.get("source") or UNKNOWN),
                        url=str(row.get("url") or row.get("source_url") or UNKNOWN),
                        date=row.get("date") or row.get("timestamp") or row.get("at") or payload.get("collected_at"),
                        collector=str(row.get("collector") or row.get("collector_name") or row.get("source") or UNKNOWN),
                        evidence=str(row.get("evidence") or row.get("summary") or row.get("signal_type") or UNKNOWN),
                        reason=str(row.get("reason") or row.get("why") or payload.get("why_collected") or UNKNOWN),
                    )
                )

        for row in payload.get("evidence") or []:
            if isinstance(row, dict):
                items.append(
                    EvidenceItem(
                        collected_from=str(row.get("collected_from") or row.get("source") or payload.get("source") or UNKNOWN),
                        url=str(row.get("url") or row.get("source_url") or UNKNOWN),
                        date=row.get("date") or row.get("collected_at") or payload.get("collected_at"),
                        collector=str(row.get("collector") or row.get("source") or UNKNOWN),
                        evidence=str(row.get("evidence") or row.get("summary") or row.get("text") or UNKNOWN),
                        reason=str(row.get("reason") or payload.get("why_collected") or UNKNOWN),
                    )
                )
            elif isinstance(row, str):
                items.append(
                    EvidenceItem(
                        collected_from=str(payload.get("source") or UNKNOWN),
                        url=str(payload.get("source_url") or payload.get("website") or UNKNOWN),
                        date=payload.get("collected_at"),
                        collector=str(payload.get("collector") or payload.get("source") or UNKNOWN),
                        evidence=row,
                        reason=str(payload.get("why_collected") or "collection_evidence"),
                    )
                )

        # Deduplicate by evidence+url
        seen: set[str] = set()
        unique: list[EvidenceItem] = []
        for item in items:
            key = f"{item.evidence}|{item.url}|{item.collected_from}"
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)

        complete = len(unique) > 0 and all(
            i.collected_from != UNKNOWN and i.evidence != UNKNOWN for i in unique
        )
        if complete:
            evidence.append("evidence_panel:complete")
        else:
            evidence.append("evidence_panel:incomplete" if unique else "evidence_panel:empty")

        return EvidencePanel(items=unique[:40], complete=complete, evidence=evidence)
