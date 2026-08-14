"""CIR Founder Queue — only Revenue Ready / Priority Account. No exceptions."""

from __future__ import annotations

from company_intelligence.models.types import CirClassification, CirSnapshot, FounderIntelligenceCard

ELIGIBLE = frozenset({CirClassification.REVENUE_READY, CirClassification.PRIORITY_ACCOUNT})


class CirFounderQueueEngine:
    def eligible(self, snap: CirSnapshot) -> bool:
        return snap.readiness.classification in ELIGIBLE and snap.erowd_admitted

    def build(self, snapshots: list[CirSnapshot], *, limit: int = 50) -> list[FounderIntelligenceCard]:
        eligible = [s for s in snapshots if self.eligible(s)]
        eligible.sort(key=lambda s: (s.readiness.total, s.readiness.trust), reverse=True)
        out: list[FounderIntelligenceCard] = []
        seen: set[str] = set()
        for s in eligible:
            if s.company_id in seen:
                continue
            seen.add(s.company_id)
            out.append(s.founder_card)
            if len(out) >= limit:
                break
        return out
