"""Learning engine — observe only. Never changes scoring."""

from __future__ import annotations

from collections import Counter
from typing import Any

from revenue_validation.models.types import UNKNOWN


class LearningEngine:
    def observe(
        self,
        *,
        records: list[dict[str, Any]],
        outcomes: list[dict[str, Any]],
        objections: list[dict[str, Any]],
        attribution: dict[str, Any],
    ) -> dict[str, Any]:
        industries: Counter[str] = Counter()
        services: Counter[str] = Counter()
        connectors: Counter[str] = Counter()
        why: Counter[str] = Counter()
        roles: Counter[str] = Counter()
        email_patterns: Counter[str] = Counter()

        active = [
            r
            for r in records
            if str(r.get("status"))
            in {"REPLIED", "MEETING_BOOKED", "PROPOSAL_SENT", "NEGOTIATION", "WON", "CONTACTED"}
        ] or records

        for r in active:
            brief = r.get("brief") or {}
            industries[str(brief.get("industry") or UNKNOWN)] += 1
            services[str(brief.get("recommended_service") or UNKNOWN)] += 1
            why[str(brief.get("why_now") or UNKNOWN)[:100]] += 1
            connectors[str((r.get("payload") or {}).get("source") or brief.get("source") or "yc")] += 1
            dm = str(brief.get("decision_maker") or "")
            role = dm.rsplit("(", 1)[1][:-1] if "(" in dm and dm.endswith(")") else "Unknown"
            roles[role] += 1
            email = str(brief.get("business_email") or brief.get("decision_maker_email") or "")
            local = email.split("@")[0] if "@" in email else ""
            if local:
                pattern = "role" if local.split("+")[0] in {"info", "sales", "support", "hello", "contact", "marketing"} else "other"
                email_patterns[pattern] += 1

        obj = Counter(str(o.get("label")) for o in objections)
        return {
            "best_industries": _top(industries),
            "best_services": _top(services),
            "best_company_size": [{"label": "unknown", "count": len(records)}],
            "best_connectors": _top(connectors),
            "best_why_now": _top(why),
            "best_email_pattern": _top(email_patterns),
            "best_dm_role": _top(roles),
            "most_common_objection": _top(obj) or [{"label": "No Reply", "count": 0}],
            "average_days_to_reply": None,
            "average_days_to_meeting": None,
            "average_days_to_close": attribution.get("average_sales_cycle"),
            "note": "Analytics only. Never auto-changes scoring or readiness rules.",
        }


def _top(c: Counter[str], n: int = 5) -> list[dict[str, Any]]:
    return [{"label": k, "count": v} for k, v in c.most_common(n)]
