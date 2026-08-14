from __future__ import annotations

from typing import Any

from ground_truth.models.types import GtSnapshot, GtVerdict, QualityFunnel, RejectionReason


class QualityFunnelEngine:
    """Rule 8 — show where companies die in the funnel."""

    def compute(self, snapshots: list[GtSnapshot] | list[dict[str, Any]]) -> QualityFunnel:
        rows = [s.model_dump(mode="json") if isinstance(s, GtSnapshot) else dict(s) for s in snapshots]
        n = len(rows)
        rejected = sum(1 for r in rows if r.get("verdict") == GtVerdict.REJECTED.value)
        sales = sum(1 for r in rows if r.get("verdict") == GtVerdict.SALES_READY.value)
        enterprise = sum(1 for r in rows if r.get("verdict") == GtVerdict.ENTERPRISE_READY.value)

        by_reason: dict[str, int] = {}
        fake = 0
        missing_website = 0
        missing_evidence = 0
        for r in rows:
            rej = r.get("rejection") or {}
            reasons = rej.get("reasons") or []
            for reason in reasons:
                by_reason[reason] = by_reason.get(reason, 0) + 1
                if reason == RejectionReason.FAKE.value:
                    fake += 1
                if reason == RejectionReason.NO_WEBSITE.value:
                    missing_website += 1
                if reason == RejectionReason.NO_EVIDENCE.value:
                    missing_evidence += 1
            # Also count from questions missing
            missing = ((r.get("questions") or {}).get("missing") or [])
            if "what_do_they_do" in missing or "who_are_they" in missing:
                pass

        return QualityFunnel(
            companies=n,
            rejected=rejected,
            fake=fake,
            missing_website=missing_website,
            missing_evidence=missing_evidence,
            sales_ready=sales,
            enterprise_ready=enterprise,
            by_rejection_reason=by_reason,
            evidence=[
                f"companies:{n}",
                f"rejected:{rejected}",
                f"sales_ready:{sales}",
                f"enterprise:{enterprise}",
            ],
        )
