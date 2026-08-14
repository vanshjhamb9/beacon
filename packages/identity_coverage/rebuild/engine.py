"""ICE funnel + audit metrics."""

from __future__ import annotations

from collections import Counter
from typing import Any

from identity_coverage.collector_metrics.engine import CollectorPerformanceEngine
from identity_coverage.models.types import (
    BusinessImpact,
    CoverageFunnel,
    FunnelStage,
    IceAuditReport,
    IceSnapshot,
)


class IceRebuildEngine:
    def funnel(self, snaps: list[IceSnapshot], *, extras: dict[str, int] | None = None) -> CoverageFunnel:
        extras = extras or {}
        signals = len(snaps)
        candidates = sum(1 for s in snaps if s.alias and s.alias.primary_name.lower() != "unknown")
        website_found = sum(1 for s in snaps if s.website)
        website_verified = sum(1 for s in snaps if s.domain and s.ranked.get("dns_ok") and getattr(s.ranked.get("dns_ok"), "value", None) == "true")
        # If DNS not probed, treat domain presence as verified website for funnel
        if website_verified == 0:
            website_verified = sum(1 for s in snaps if s.domain)
        companies = extras.get("companies", website_verified)
        emails = extras.get("business_emails", sum(1 for s in snaps if s.ranked.get("business_email")))
        dms = extras.get("decision_makers", sum(1 for s in snaps if s.ranked.get("decision_maker")))
        sales = extras.get("sales_ready", 0)
        rr = extras.get("revenue_ready", 0)

        def stage(name: str, count: int, prev: int, reasons: list[str] | None = None) -> FunnelStage:
            conv = (count / prev * 100.0) if prev else 0.0
            drop = max(0.0, 100.0 - conv) if prev else 0.0
            return FunnelStage(name=name, count=count, conversion_pct=round(conv, 2), drop_pct=round(drop, 2), reasons=reasons or [])

        stages = [
            stage("Signals", signals, signals),
            stage("Candidates", candidates, signals or 1),
            stage("Website Found", website_found, candidates or 1, ["No Official Website"]),
            stage("Website Verified", website_verified, website_found or 1),
            stage("Company Created", companies, website_verified or 1),
            stage("Business Email", emails, companies or 1, ["No Contact"]),
            stage("Decision Maker", dms, emails or 1, ["No Decision Maker"]),
            stage("Sales Ready", sales, dms or 1),
            stage("Revenue Ready", rr, sales or 1),
        ]
        return CoverageFunnel(stages=stages)

    def audit(
        self,
        *,
        before: dict[str, Any],
        after: dict[str, Any],
        snaps: list[IceSnapshot],
        collector_rows: list[dict[str, Any]] | None = None,
        top_rr: list[dict[str, Any]] | None = None,
    ) -> IceAuditReport:
        extras = {
            "companies": int(after.get("verified_companies") or after.get("companies") or 0),
            "business_emails": int(after.get("business_emails") or 0),
            "decision_makers": int(after.get("decision_makers") or 0),
            "sales_ready": int(after.get("sales_ready") or 0),
            "revenue_ready": int(after.get("revenue_ready") or 0),
        }
        funnel = self.funnel(snaps, extras=extras)
        collectors = CollectorPerformanceEngine().score(collector_rows or [])
        signals = max(1, int(after.get("signals") or len(snaps) or 1))
        companies = extras["companies"]
        coverage = companies / signals * 100.0
        recovery_attempts = sum(len(s.recovery) for s in snaps)
        recovery_fixed = sum(1 for s in snaps if s.admitted_hint and s.recovery)
        recovery_rate = (recovery_fixed / recovery_attempts * 100.0) if recovery_attempts else 0.0
        rejections: Counter[str] = Counter()
        for s in snaps:
            for r in s.recovery:
                rejections[r.value] += 1
            if not s.website:
                rejections["No Official Website"] += 1

        rr = extras["revenue_ready"]
        emails = extras["business_emails"]
        dms = extras["decision_makers"]
        impact = BusinessImpact(
            revenue_ready=rr,
            emails_ready=emails,
            decision_makers_ready=dms,
            meetings_possible=min(rr, dms, emails),
            pipeline_value=f"${rr * 25}k-${rr * 40}k" if rr else "$0",
            revenue_yield=round(rr / companies * 100.0, 2) if companies else 0.0,
        )
        answer = "YES" if rr >= 20 and emails >= 20 and dms >= 20 else "NO"
        return IceAuditReport(
            before=before,
            after=after,
            funnel=funnel,
            collectors=collectors,
            recovery_success_rate=round(recovery_rate, 2),
            coverage_pct=round(coverage, 2),
            duplicate_pct=float(after.get("duplicate_pct") or 0),
            top_rejections=dict(rejections.most_common(12)),
            business_impact=impact,
            top_revenue_ready=top_rr or [],
            vansh_ready_answer=answer,
        )
