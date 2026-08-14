"""Rebuild metrics from CRE snapshots — Phase 9–10 acceptance reporting."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from company_resolution.models.types import CreRebuildReport, CreSnapshot, CreVerdict


class CreRebuildEngine:
    def build(self, snapshots: list[CreSnapshot], *, sales_ready_ids: set[str] | None = None) -> CreRebuildReport:
        sales_ready_ids = sales_ready_ids or set()
        total = len(snapshots)
        admitted = [s for s in snapshots if s.verdict == CreVerdict.ADMITTED]
        rejected = [s for s in snapshots if s.verdict != CreVerdict.ADMITTED]

        reason_counter: Counter[str] = Counter()
        for s in rejected:
            for r in s.admission.reasons:
                reason_counter[r.value] += 1
            if not s.admission.reasons:
                reason_counter["Rejected"] += 1

        # Identity confidence buckets
        buckets = {"0-49": 0, "50-69": 0, "70-89": 0, "90-100": 0}
        for s in snapshots:
            score = s.identity.score
            if score < 50:
                buckets["0-49"] += 1
            elif score < 70:
                buckets["50-69"] += 1
            elif score < 90:
                buckets["70-89"] += 1
            else:
                buckets["90-100"] += 1

        # Source precision
        by_source: dict[str, list[CreSnapshot]] = defaultdict(list)
        for s in snapshots:
            by_source[s.source].append(s)
        source_precision: dict[str, dict[str, float | int]] = {}
        for source, items in by_source.items():
            adm = sum(1 for i in items if i.verdict == CreVerdict.ADMITTED)
            source_precision[source] = {
                "signals": len(items),
                "admitted": adm,
                "precision_pct": round(100.0 * adm / max(len(items), 1), 2),
            }

        # Dedupe admitted by domain for unique companies
        seen_domains: set[str] = set()
        unique_companies: list[CreSnapshot] = []
        for s in admitted:
            key = (s.company_domain or s.company_name or s.signal_id).lower()
            if key in seen_domains:
                continue
            seen_domains.add(key)
            unique_companies.append(s)

        verified = [s for s in unique_companies if s.website.valid and s.identity.passed]
        sales_ready = sum(
            1
            for s in verified
            if (s.company_domain or "") in sales_ready_ids or (s.company_name or "") in sales_ready_ids
        )

        top_verified = [
            {
                "company": s.company_name,
                "domain": s.company_domain,
                "source": s.source,
                "signal_id": s.signal_id,
                "attribution_url": s.attribution.source_url,
                "identity_confidence": s.identity.score,
                "website_valid": s.website.valid,
                "evidence": s.organization.evidence[:8],
            }
            for s in verified[:50]
        ]

        rejected_examples = [
            {
                "title": s.signal.title[:120],
                "source": s.source,
                "reason": s.admission.explanation,
                "identity_score": s.identity.score,
                "domain": s.organization.official_domain,
            }
            for s in rejected[:25]
            if s.false_positive_example or s.admission.reasons
        ]

        success_rate = round(100.0 * len(unique_companies) / max(total, 1), 2)
        return CreRebuildReport(
            total_raw_signals=total,
            resolved_companies=len(unique_companies),
            verified_companies=len(verified),
            sales_ready=sales_ready,
            companies_created=len(unique_companies),
            companies_rejected=len(rejected),
            resolution_success_rate=success_rate,
            rejection_reasons=dict(reason_counter.most_common()),
            identity_confidence_distribution=buckets,
            source_precision=source_precision,
            top_verified=top_verified,
            rejected_examples=rejected_examples,
            evidence=[
                f"signals:{total}",
                f"created:{len(unique_companies)}",
                f"verified:{len(verified)}",
                f"success_rate:{success_rate}",
            ],
        )
