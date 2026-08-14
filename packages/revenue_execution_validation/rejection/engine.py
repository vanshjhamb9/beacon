"""Rejection analysis — taxonomy + windows / connector / industry."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from revenue_execution_validation.models.types import RejectionReason, RevSnapshot


class RejectionAnalysisEngine:
    REASONS = tuple(RejectionReason)

    def analyze(
        self,
        snapshots: list[RevSnapshot],
        *,
        now: datetime | None = None,
        industries: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        now = now or datetime.now(UTC)
        industries = industries or {}

        def bucket(snaps: list[RevSnapshot]) -> list[dict[str, Any]]:
            c: Counter[str] = Counter()
            for s in snaps:
                for r in s.rejection_reasons or s.check.rejection_reasons:
                    c[r.value if hasattr(r, "value") else str(r)] += 1
            return [{"reason": k, "count": v} for k, v in c.most_common(20)]

        # Without timestamps on snaps, treat all as last 24h for synthetic; use processing as proxy
        all_rej = [s for s in snapshots if not s.check.is_revenue_ready]
        per_connector: dict[str, list[dict[str, Any]]] = {}
        by_conn: dict[str, list[RevSnapshot]] = defaultdict(list)
        for s in all_rej:
            by_conn[s.source or "unknown"].append(s)
        for src, items in by_conn.items():
            per_connector[src] = bucket(items)

        by_ind: dict[str, list[RevSnapshot]] = defaultdict(list)
        for s in all_rej:
            ind = industries.get(s.company_id) or s.check.industry or "UNKNOWN"
            by_ind[str(ind)].append(s)
        per_industry = {k: bucket(v) for k, v in by_ind.items()}

        return {
            "top_rejection_reasons": bucket(all_rej),
            "last_24_hours": bucket(all_rej),  # compose: full set when no event time
            "last_7_days": bucket(all_rej),
            "per_connector": per_connector,
            "per_industry": per_industry,
            "total_rejected": len(all_rej),
            "taxonomy": [r.value for r in RejectionReason],
            "generated_at": now.isoformat(),
        }

    def reasons_for(self, check_reasons: list[RejectionReason]) -> list[str]:
        return [r.value for r in check_reasons]
