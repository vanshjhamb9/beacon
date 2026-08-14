"""Evidence ranking — every field exposes value/source/confidence/verified."""

from __future__ import annotations

from identity_coverage.models.types import CoverageEvidence, RankedField, UNKNOWN


class EvidenceRankingEngine:
    def rank(self, evidence: list[CoverageEvidence]) -> dict[str, RankedField]:
        by_field: dict[str, list[CoverageEvidence]] = {}
        for ev in evidence:
            by_field.setdefault(ev.field, []).append(ev)
        out: dict[str, RankedField] = {}
        for field, items in by_field.items():
            best = sorted(items, key=lambda e: (e.verification, e.confidence, -e.priority), reverse=True)[0]
            out[field] = RankedField(
                value=best.value or UNKNOWN,
                source=best.source,
                collector=best.collector,
                confidence=best.confidence,
                verified=best.verification,
                collected_at=best.timestamp,
                last_verified=best.timestamp if best.verification else None,
                evidence_count=len(items),
            )
        return out
