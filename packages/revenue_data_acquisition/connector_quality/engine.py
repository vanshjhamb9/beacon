"""Connector quality scoreboard — Excellent → Disabled."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from revenue_data_acquisition.models.types import ConnectorGrade, ConnectorScore, SourceClass
from revenue_data_acquisition.source_roles.engine import SourceClassificationEngine


class ConnectorQualityEngine:
    def __init__(self) -> None:
        self.roles = SourceClassificationEngine()

    def score(self, rows: list[dict[str, Any]]) -> list[ConnectorScore]:
        buckets: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for row in rows:
            c = str(row.get("connector") or row.get("source") or "unknown")
            b = buckets[c]
            b["signals"] += 1
            if row.get("candidate"):
                b["candidates"] += 1
            if row.get("company") or row.get("verified_company"):
                b["verified_companies"] += 1
            if row.get("website"):
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

        out: list[ConnectorScore] = []
        for connector, b in buckets.items():
            signals = max(1, int(b["signals"]))
            companies = int(b["verified_companies"])
            websites = int(b["official_websites"])
            emails = int(b["business_emails"])
            dms = int(b["decision_makers"])
            rr = int(b["revenue_ready"])
            web_pct = websites / signals * 100.0
            email_pct = emails / max(1, companies) * 100.0
            dm_pct = dms / max(1, companies) * 100.0
            yield_pct = rr / signals * 100.0
            avg_conf = b["confidence_sum"] / signals
            dup = b["duplicates"] / signals * 100.0
            roles = self.roles.roles(connector)
            if SourceClass.IDENTITY not in roles and companies == 0:
                grade = ConnectorGrade.DISABLED
            elif yield_pct >= 2 or (companies >= 10 and email_pct >= 40):
                grade = ConnectorGrade.EXCELLENT
            elif companies >= 5 or web_pct >= 10:
                grade = ConnectorGrade.GOOD
            elif companies >= 1 or web_pct >= 2:
                grade = ConnectorGrade.AVERAGE
            else:
                grade = ConnectorGrade.POOR
            out.append(
                ConnectorScore(
                    connector=connector,
                    grade=grade,
                    signals=int(b["signals"]),
                    candidates=int(b["candidates"]),
                    verified_companies=companies,
                    official_websites=websites,
                    business_emails=emails,
                    decision_makers=dms,
                    sales_ready=int(b["sales_ready"]),
                    revenue_ready=rr,
                    duplicate_pct=round(dup, 2),
                    website_recovery_pct=round(web_pct, 2),
                    email_recovery_pct=round(email_pct, 2),
                    dm_recovery_pct=round(dm_pct, 2),
                    average_confidence=round(avg_conf, 2),
                    revenue_yield=round(yield_pct, 2),
                    roles=roles,
                )
            )
        return sorted(out, key=lambda x: (x.revenue_ready, x.verified_companies, x.business_emails), reverse=True)
