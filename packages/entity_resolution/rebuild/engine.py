"""Rebuild metrics for EROWD acceptance reporting."""

from __future__ import annotations

from collections import Counter, defaultdict

from entity_resolution.models.types import ErowdRebuildReport, ErowdSnapshot, ErowdVerdict


class ErowdRebuildEngine:
    def build(self, snapshots: list[ErowdSnapshot], *, sales_ready: int = 0) -> ErowdRebuildReport:
        total = len(snapshots)
        admitted = [s for s in snapshots if s.verdict == ErowdVerdict.ADMITTED]
        rejected = [s for s in snapshots if s.verdict != ErowdVerdict.ADMITTED]
        with_website = [s for s in snapshots if s.website.discovered]
        verified = [s for s in admitted if s.validation.verified]

        # Unique candidates by domain/name
        seen: set[str] = set()
        candidates = 0
        for s in snapshots:
            key = (s.website.domain or s.entity.normalized_key or s.signal_id).lower()
            if key in seen:
                continue
            if s.entity.name != "unknown" or s.website.discovered:
                seen.add(key)
                candidates += 1

        reasons: Counter[str] = Counter()
        for s in rejected:
            for r in s.admission.reasons:
                reasons[r.value] += 1

        buckets = {"0-49": 0, "50-69": 0, "70-89": 0, "90-100": 0}
        for s in snapshots:
            sc = s.score.score
            if sc < 50:
                buckets["0-49"] += 1
            elif sc < 70:
                buckets["50-69"] += 1
            elif sc < 90:
                buckets["70-89"] += 1
            else:
                buckets["90-100"] += 1

        by_source: dict[str, list[ErowdSnapshot]] = defaultdict(list)
        for s in snapshots:
            by_source[s.source].append(s)
        precision: dict[str, dict[str, float | int]] = {}
        for src, items in by_source.items():
            adm = sum(1 for i in items if i.verdict == ErowdVerdict.ADMITTED)
            precision[src] = {
                "signals": len(items),
                "admitted": adm,
                "websites_found": sum(1 for i in items if i.website.discovered),
                "precision_pct": round(100.0 * adm / max(len(items), 1), 2),
            }

        # False positives: admitted without verified website (should be 0)
        false_positives = sum(1 for s in admitted if not s.validation.verified or not s.website.discovered)

        top = [
            {
                "company": s.identity.company_name,
                "website": s.identity.official_website,
                "domain": s.identity.domain,
                "confidence": s.score.score,
                "verified": s.validation.verified,
                "source": s.attribution.discovery_source,
                "collector": s.attribution.collector,
                "signal_id": s.signal_id,
                "evidence": s.website.evidence[:6],
            }
            for s in verified[:50]
        ]
        examples = [
            {
                "title": (getattr(s, "signal_id", "")),
                "source": s.source,
                "reason": s.admission.explanation,
                "score": s.score.score,
                "domain": s.website.domain,
            }
            for s in rejected[:25]
        ]

        return ErowdRebuildReport(
            total_signals=total,
            entity_candidates=candidates,
            official_websites=len({s.website.domain for s in with_website if s.website.domain}),
            verified_companies=len({s.website.domain for s in verified if s.website.domain}),
            sales_ready=sales_ready,
            admitted=len(admitted),
            rejected=len(rejected),
            discovery_rate=round(100.0 * len(with_website) / max(total, 1), 2),
            verification_rate=round(100.0 * len(verified) / max(len(with_website), 1), 2) if with_website else 0.0,
            false_positives=false_positives,
            identity_confidence_distribution=buckets,
            source_precision=precision,
            top_verified=top,
            rejected_examples=examples,
            evidence=[
                f"signals:{total}",
                f"websites:{len(with_website)}",
                f"admitted:{len(admitted)}",
                f"false_positives:{false_positives}",
            ],
        )
