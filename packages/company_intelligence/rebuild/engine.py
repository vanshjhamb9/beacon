"""CIR rebuild metrics / acceptance reporting."""

from __future__ import annotations

from collections import Counter
from time import perf_counter

from company_intelligence.models.types import (
    UNKNOWN,
    CirClassification,
    CirRebuildReport,
    CirSnapshot,
    CirVerdict,
)


class CirRebuildEngine:
    def build(self, snapshots: list[CirSnapshot]) -> CirRebuildReport:
        t0 = perf_counter()
        total = len(snapshots)
        active = [s for s in snapshots if s.verdict != CirVerdict.SKIPPED]
        reconstructed = [s for s in active if s.verdict in {CirVerdict.RECONSTRUCTED, CirVerdict.PARTIAL}]

        business_ok = sum(
            1
            for s in active
            if s.business.description.value != UNKNOWN or s.business.industry.value != UNKNOWN
        )
        industry_icp = sum(
            1
            for s in active
            if s.business.industry.value != UNKNOWN and s.icp.primary_icp.value != UNKNOWN
        )
        tech_service = sum(1 for s in active if s.technologies and s.service_matches)
        contacts_ok = sum(
            1
            for s in active
            if any(c.name != UNKNOWN or c.email != UNKNOWN for c in s.contacts)
        )

        classes = Counter(s.readiness.classification.value for s in active)
        revenue_ready = classes.get(CirClassification.REVENUE_READY.value, 0)
        priority = classes.get(CirClassification.PRIORITY_ACCOUNT.value, 0)
        founder_queue = sum(1 for s in active if s.founder_queue_eligible)

        # Fabrication check: readiness without any evidence strings
        false_fabs = sum(1 for s in active if s.readiness.total > 0 and not s.readiness.evidence)

        top = [
            {
                "company": s.company_name,
                "website": s.website,
                "score": s.readiness.total,
                "class": s.readiness.classification.value,
                "best_service": s.founder_card.best_service,
                "signals": s.founder_card.buying_signals[:3],
            }
            for s in sorted(active, key=lambda x: x.readiness.total, reverse=True)[:40]
        ]

        elapsed = (perf_counter() - t0) * 1000
        n = max(len(active), 1)
        return CirRebuildReport(
            total_companies=total,
            reconstructed=len(reconstructed),
            business_profile_pct=round(100.0 * business_ok / n, 2),
            industry_icp_pct=round(100.0 * industry_icp / n, 2),
            technology_service_pct=round(100.0 * tech_service / n, 2),
            contact_pct=round(100.0 * contacts_ok / n, 2),
            revenue_ready=revenue_ready,
            priority_accounts=priority,
            founder_queue=founder_queue,
            false_fabrications=false_fabs,
            elapsed_ms=round(elapsed, 2),
            classification_distribution=dict(classes),
            top_accounts=top,
            evidence=[
                f"total:{total}",
                f"active:{len(active)}",
                f"business_pct:{round(100.0 * business_ok / n, 2)}",
                f"founder_queue:{founder_queue}",
            ],
        )
