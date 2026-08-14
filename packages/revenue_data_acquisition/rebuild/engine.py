"""RDAP funnel + live audit."""

from __future__ import annotations

from collections import Counter
from typing import Any

from revenue_data_acquisition.connector_quality.engine import ConnectorQualityEngine
from revenue_data_acquisition.models.types import FunnelStage, RdapAudit, RdapSnapshot
from revenue_data_acquisition.revenue_yield.engine import RevenueYieldEngine


class RdapRebuildEngine:
    def funnel(self, snaps: list[RdapSnapshot], *, extras: dict[str, int] | None = None) -> list[FunnelStage]:
        extras = extras or {}
        signals = len(snaps)
        candidates = sum(1 for s in snaps if s.can_create_identity)
        websites = sum(1 for s in snaps if s.website)
        companies = extras.get("verified_companies", sum(1 for s in snaps if s.domain))
        emails = extras.get("business_emails", sum(1 for s in snaps if s.emails))
        dms = extras.get("decision_makers", sum(1 for s in snaps if s.decision_makers))
        sales = extras.get("sales_ready", sum(1 for s in snaps if s.dossier and s.dossier.sales_ready))
        rr = extras.get("revenue_ready", sum(1 for s in snaps if s.dossier and s.dossier.revenue_ready))

        def st(name: str, count: int, prev: int) -> FunnelStage:
            return FunnelStage(name=name, count=count, conversion_pct=round((count / prev * 100.0) if prev else 0.0, 2))

        return [
            st("Signals", signals, signals or 1),
            st("Identity Candidates", candidates, signals or 1),
            st("Official Websites", websites, candidates or 1),
            st("Verified Companies", companies, websites or 1),
            st("Business Emails", emails, companies or 1),
            st("Decision Makers", dms, emails or 1),
            st("Sales Ready", sales, dms or 1),
            st("Revenue Ready", rr, sales or 1),
        ]

    def audit(
        self,
        *,
        before: dict[str, Any],
        after: dict[str, Any],
        snaps: list[RdapSnapshot],
        collector_rows: list[dict[str, Any]],
        top_rr: list[dict[str, Any]] | None = None,
    ) -> RdapAudit:
        extras = {
            "verified_companies": int(after.get("verified_companies") or 0),
            "business_emails": int(after.get("business_emails") or 0),
            "decision_makers": int(after.get("decision_makers") or 0),
            "sales_ready": int(after.get("sales_ready") or 0),
            "revenue_ready": int(after.get("revenue_ready") or 0),
        }
        rej: Counter[str] = Counter()
        for s in snaps:
            for r in s.recovery:
                rej[r.value] += 1
        rr = extras["revenue_ready"]
        sales = extras["sales_ready"]
        emails = extras["business_emails"]
        dms = extras["decision_makers"]
        websites = extras["verified_companies"]
        # CTO question: ≥5 outreach-ready companies (site + email + named DM + buying intent)
        answer = (
            "YES"
            if websites >= 5 and emails >= 5 and dms >= 5 and (sales >= 5 or rr >= 5)
            else "NO"
        )
        return RdapAudit(
            before=before,
            after=after,
            funnel=self.funnel(snaps, extras=extras),
            connectors=ConnectorQualityEngine().score(collector_rows),
            yields=RevenueYieldEngine().compute(collector_rows),
            top_rejections=dict(rej.most_common(12)),
            top_revenue_ready=top_rr or [],
            vansh_ready_answer=answer,
        )
