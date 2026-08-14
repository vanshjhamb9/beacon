"""IGF rebuild metrics — Identity Resolution Funnel."""

from __future__ import annotations

from collections import Counter

from identity_graph.models.types import IgfFunnelMetrics, IgfSnapshot, IgfVerdict, SourceRole


class IgfRebuildEngine:
    def build(self, snapshots: list[IgfSnapshot]) -> IgfFunnelMetrics:
        candidates = sum(1 for s in snapshots if s.candidate.name.lower() != "unknown")
        evidence_n = sum(len(s.evidence_items) for s in snapshots)
        websites = {s.domain for s in snapshots if s.domain and s.admission.admitted}
        verified = sum(1 for s in snapshots if s.admission.admitted)
        merged = sum(1 for s in snapshots if s.admission.verdict == IgfVerdict.MERGED)
        rejected = sum(1 for s in snapshots if s.admission.verdict == IgfVerdict.REJECTED)
        pending = sum(1 for s in snapshots if s.admission.verdict == IgfVerdict.PENDING)

        identity_snaps = [s for s in snapshots if s.source_role == SourceRole.IDENTITY]
        precision = (verified / len(identity_snaps) * 100.0) if identity_snaps else 0.0

        sources = Counter(s.source for s in snapshots if s.admission.admitted)
        failures: Counter[str] = Counter()
        for s in snapshots:
            for r in s.admission.reasons:
                failures[r.value] += 1

        return IgfFunnelMetrics(
            signals=len(snapshots),
            candidates=candidates,
            evidence_collected=evidence_n,
            official_websites=len(websites),
            verified_companies=verified,
            merged=merged,
            rejected=rejected,
            pending=pending,
            identity_precision=round(precision, 2),
            top_sources=dict(sources.most_common(12)),
            top_failures=dict(failures.most_common(12)),
        )
