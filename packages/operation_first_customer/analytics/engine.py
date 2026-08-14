"""OFC analytics — funnel + learning. Never auto-change scoring."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from operation_first_customer.models.types import DEFAULT_PIPELINE_VALUE, OutreachStatus


FUNNEL_ORDER = [
    OutreachStatus.READY,
    OutreachStatus.CONTACTED,
    OutreachStatus.REPLIED,
    OutreachStatus.MEETING_BOOKED,
    OutreachStatus.PROPOSAL_SENT,
    OutreachStatus.WON,
    OutreachStatus.LOST,
]


class OfcAnalyticsEngine:
    def funnel(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        counts = Counter(str(r.get("status") or OutreachStatus.READY) for r in records)
        # Cumulative-style funnel for conversion display
        contacted = sum(
            counts[s]
            for s in (
                OutreachStatus.CONTACTED,
                OutreachStatus.REPLIED,
                OutreachStatus.MEETING_BOOKED,
                OutreachStatus.PROPOSAL_SENT,
                OutreachStatus.NEGOTIATION,
                OutreachStatus.WON,
                OutreachStatus.LOST,
            )
        )
        replies = sum(
            counts[s]
            for s in (
                OutreachStatus.REPLIED,
                OutreachStatus.MEETING_BOOKED,
                OutreachStatus.PROPOSAL_SENT,
                OutreachStatus.NEGOTIATION,
                OutreachStatus.WON,
            )
        )
        meetings = sum(
            counts[s]
            for s in (
                OutreachStatus.MEETING_BOOKED,
                OutreachStatus.PROPOSAL_SENT,
                OutreachStatus.NEGOTIATION,
                OutreachStatus.WON,
            )
        )
        proposals = sum(
            counts[s]
            for s in (OutreachStatus.PROPOSAL_SENT, OutreachStatus.NEGOTIATION, OutreachStatus.WON)
        )
        won = counts[OutreachStatus.WON]
        lost = counts[OutreachStatus.LOST]
        ready = len(records)
        return [
            {"name": "Revenue Ready", "count": ready},
            {"name": "Contacted", "count": contacted},
            {"name": "Replies", "count": replies},
            {"name": "Meetings", "count": meetings},
            {"name": "Proposals", "count": proposals},
            {"name": "Won", "count": won},
            {"name": "Lost", "count": lost},
        ]

    def conversion_rates(self, funnel: list[dict[str, Any]]) -> dict[str, float]:
        def n(name: str) -> int:
            return next((int(x["count"]) for x in funnel if x["name"] == name), 0)

        ready, contacted, replies, meetings, proposals, won = (
            n("Revenue Ready"),
            n("Contacted"),
            n("Replies"),
            n("Meetings"),
            n("Proposals"),
            n("Won"),
        )
        return {
            "contact_rate": round(100.0 * contacted / ready, 1) if ready else 0.0,
            "reply_rate": round(100.0 * replies / contacted, 1) if contacted else 0.0,
            "meeting_rate": round(100.0 * meetings / replies, 1) if replies else 0.0,
            "proposal_rate": round(100.0 * proposals / meetings, 1) if meetings else 0.0,
            "win_rate": round(100.0 * won / proposals, 1) if proposals else 0.0,
            "overall_win_rate": round(100.0 * won / contacted, 1) if contacted else 0.0,
        }

    def learning(self, records: list[dict[str, Any]], objections: list[dict[str, Any]]) -> dict[str, Any]:
        won = [r for r in records if r.get("status") == OutreachStatus.WON]
        lost = [r for r in records if r.get("status") == OutreachStatus.LOST]
        pool = won or records

        def top_field(items: list[dict[str, Any]], path: str) -> list[dict[str, Any]]:
            c: Counter[str] = Counter()
            for item in items:
                brief = item.get("brief") or {}
                val = brief.get(path) or item.get(path) or UNKNOWN_LABEL
                # decision maker role = text in parentheses
                if path == "decision_maker_role":
                    dm = str(brief.get("decision_maker") or "")
                    if "(" in dm and dm.endswith(")"):
                        val = dm.rsplit("(", 1)[1][:-1].strip()
                    else:
                        val = "Unknown role"
                c[str(val)] += 1
            return [{"label": k, "count": v} for k, v in c.most_common(5)]

        obj_counts = Counter(str(o.get("label")) for o in objections)
        worst = [{"label": k, "count": v} for k, v in obj_counts.most_common(8)]

        return {
            "best_industries": top_field(pool, "industry"),
            "best_company_sizes": [{"label": "unknown", "count": len(pool)}],
            "best_services": top_field(pool, "recommended_service"),
            "best_why_now_triggers": top_field(pool, "why_now"),
            "best_decision_maker_roles": top_field(pool, "decision_maker_role"),
            "worst_rejection_reasons": worst
            or [{"label": o, "count": 0} for o in ("No Reply", "No Budget", "Wrong Contact")],
            "won_count": len(won),
            "lost_count": len(lost),
        }

    def pipeline_value(self, records: list[dict[str, Any]]) -> float:
        active = {
            OutreachStatus.READY,
            OutreachStatus.CONTACTED,
            OutreachStatus.REPLIED,
            OutreachStatus.MEETING_BOOKED,
            OutreachStatus.PROPOSAL_SENT,
            OutreachStatus.NEGOTIATION,
        }
        total = 0.0
        for r in records:
            if r.get("status") in active or r.get("status") == OutreachStatus.WON:
                total += float(r.get("pipeline_value") or DEFAULT_PIPELINE_VALUE)
        return round(total, 2)

    def average_sales_cycle_days(self, records: list[dict[str, Any]]) -> float | None:
        days: list[float] = []
        for r in records:
            hist = list(r.get("status_history") or [])
            if not hist:
                continue
            start = _parse(hist[0].get("at"))
            end_status = str(r.get("status"))
            if end_status not in {OutreachStatus.WON, OutreachStatus.LOST}:
                continue
            end = _parse(hist[-1].get("at"))
            if start and end:
                days.append(max(0.0, (end - start).total_seconds() / 86400.0))
        if not days:
            return None
        return round(sum(days) / len(days), 1)


UNKNOWN_LABEL = "unknown"


def _parse(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None
