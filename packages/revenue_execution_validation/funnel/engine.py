"""Reality Funnel — vanity-free pipeline counts."""

from __future__ import annotations

from collections import Counter
from typing import Any

from revenue_execution_validation.models.types import FunnelStage, RealityFunnel, RevSnapshot


STAGE_ORDER = (
    "Signals Collected",
    "Verified Companies",
    "Identity Complete",
    "Website Verified",
    "Intent Detected",
    "Service Match",
    "Business Email",
    "Decision Maker",
    "Revenue Ready",
    "Founder Queue",
    "Approved",
    "Sent",
    "Replies",
    "Meetings",
    "Won",
)


class RealityFunnelEngine:
    def build(
        self,
        snapshots: list[RevSnapshot],
        *,
        signals_collected: int | None = None,
        approved: int = 0,
        sent: int = 0,
        replies: int = 0,
        meetings: int = 0,
        won: int = 0,
        founder_queue_ids: set[str] | None = None,
    ) -> RealityFunnel:
        n = max(len(snapshots), 1)
        signals = signals_collected if signals_collected is not None else len(snapshots)

        def count(pred) -> int:
            return sum(1 for s in snapshots if pred(s))

        verified = count(lambda s: s.check.checks.get("erowd") or s.check.website_verified)
        identity = count(lambda s: s.check.identity_complete)
        website = count(lambda s: s.check.website_verified)
        intent = count(lambda s: s.check.intent_detected)
        service = count(lambda s: s.check.service_match)
        email = count(lambda s: s.check.business_email)
        dm = count(lambda s: s.check.decision_maker)
        ready = count(lambda s: s.check.is_revenue_ready)
        fq = len(founder_queue_ids) if founder_queue_ids is not None else ready

        reason_counter = Counter()
        for s in snapshots:
            for r in s.rejection_reasons or s.check.rejection_reasons:
                reason_counter[r.value if hasattr(r, "value") else str(r)] += 1
        top_fail = [{"reason": k, "count": v} for k, v in reason_counter.most_common(8)]

        source_counter = Counter(s.source or "unknown" for s in snapshots)
        top_sources = [{"source": k, "count": v} for k, v in source_counter.most_common(8)]
        avg_ms = round(sum(s.processing_ms for s in snapshots) / n, 2)

        counts = {
            "Signals Collected": signals,
            "Verified Companies": verified,
            "Identity Complete": identity,
            "Website Verified": website,
            "Intent Detected": intent,
            "Service Match": service,
            "Business Email": email,
            "Decision Maker": dm,
            "Revenue Ready": ready,
            "Founder Queue": fq,
            "Approved": approved,
            "Sent": sent,
            "Replies": replies,
            "Meetings": meetings,
            "Won": won,
        }
        base = max(signals, 1)
        stages = [
            FunnelStage(
                name=name,
                count=counts[name],
                percent=round(100.0 * counts[name] / base, 2),
                top_failure_reasons=top_fail if name in {"Revenue Ready", "Identity Complete", "Business Email"} else [],
                avg_processing_ms=avg_ms,
                top_sources=top_sources,
            )
            for name in STAGE_ORDER
        ]
        return RealityFunnel(
            stages=stages,
            total_signals=signals,
            revenue_ready=ready,
            founder_queue=fq,
            evidence=[f"signals:{signals}", f"ready:{ready}", f"fq:{fq}"],
        )
