"""Collector performance — KEEP / LIMIT / DISABLE recommendations."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from identity_coverage.models.types import CollectorKpis, ProviderAction


class CollectorPerformanceEngine:
    def score(self, rows: list[dict[str, Any]]) -> list[CollectorKpis]:
        buckets: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for row in rows:
            c = str(row.get("collector") or row.get("source") or "unknown")
            b = buckets[c]
            b["signals"] += 1
            if row.get("candidate"):
                b["candidates"] += 1
            if row.get("company") or row.get("admitted"):
                b["companies"] += 1
            if row.get("website") or row.get("official_website"):
                b["official_websites"] += 1
            if row.get("business_email"):
                b["business_emails"] += 1
            if row.get("decision_maker"):
                b["decision_makers"] += 1
            if row.get("sales_ready"):
                b["sales_ready"] += 1
            if row.get("revenue_ready"):
                b["revenue_ready"] += 1
            b["confidence_sum"] += float(row.get("confidence") or 0)
            b["duplicates"] += float(row.get("duplicate") or 0)

        out: list[CollectorKpis] = []
        for collector, b in buckets.items():
            signals = int(b["signals"]) or 1
            companies = int(b["companies"])
            websites = int(b["official_websites"])
            precision = (websites / companies * 100.0) if companies else 0.0
            recall = (companies / signals * 100.0) if signals else 0.0
            dup = (b["duplicates"] / signals) * 100.0
            avg_conf = b["confidence_sum"] / signals
            if companies == 0 and websites == 0:
                rec = ProviderAction.DISABLE
            elif recall < 2.0 or precision < 50.0:
                rec = ProviderAction.LIMIT
            else:
                rec = ProviderAction.KEEP
            out.append(
                CollectorKpis(
                    collector=collector,
                    signals=int(b["signals"]),
                    candidates=int(b["candidates"]),
                    companies=companies,
                    official_websites=websites,
                    business_emails=int(b["business_emails"]),
                    decision_makers=int(b["decision_makers"]),
                    sales_ready=int(b["sales_ready"]),
                    revenue_ready=int(b["revenue_ready"]),
                    duplicate_rate=round(dup, 2),
                    identity_precision=round(precision, 2),
                    identity_recall=round(recall, 2),
                    average_confidence=round(avg_conf, 2),
                    recommendation=rec,
                )
            )
        return sorted(out, key=lambda x: x.revenue_ready * 1000 + x.companies, reverse=True)
