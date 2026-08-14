"""Daily founder brief + weekly executive review — deterministic."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from revenue_validation.models.types import DailyBriefCard, UNKNOWN


CONTACTED_LIKE = {
    "CONTACTED",
    "EMAIL_SENT",
    "OPENED",
    "CLICKED",
    "NO_RESPONSE",
    "FOLLOW_UP_REQUIRED",
    "FOLLOW_UP_SENT",
}
REPLY_LIKE = {"REPLIED", "POSITIVE_REPLY", "NEGATIVE_REPLY"}
MEETING_LIKE = {"MEETING_BOOKED", "MEETING_COMPLETED"}
PROPOSAL_LIKE = {"PROPOSAL_SENT", "NEGOTIATION"}


class DailyBriefEngine:
    def build(
        self,
        *,
        records: list[dict[str, Any]],
        outcomes: list[dict[str, Any]],
        yesterday_summary: dict[str, Any] | None = None,
        execution_mode: str = "PLANNING",
        execution_reason: str = "No verified communication provider connected.",
    ) -> dict[str, Any]:
        mode = (execution_mode or "PLANNING").upper()
        executing = mode == "EXECUTING"
        by_company_outcome = self._latest_by_company(outcomes)
        priorities = self._top_priorities(records, by_company_outcome, execution_mode=mode)
        # Delivery-dependent sections stay empty until Executing
        followups = self._followups_due(records, by_company_outcome) if executing else []
        meetings = (
            [
                r
                for r in records
                if by_company_outcome.get(str(r.get("company_id")), {}).get("outcome") in MEETING_LIKE
                or str(r.get("status")) == "MEETING_BOOKED"
            ]
            if executing
            else []
        )
        replies_waiting = (
            [
                r
                for r in records
                if by_company_outcome.get(str(r.get("company_id")), {}).get("outcome") in REPLY_LIKE
                or str(r.get("status")) == "REPLIED"
            ]
            if executing
            else []
        )
        proposals = (
            [
                r
                for r in records
                if by_company_outcome.get(str(r.get("company_id")), {}).get("outcome") in PROPOSAL_LIKE
                or str(r.get("status")) in {"PROPOSAL_SENT", "NEGOTIATION"}
            ]
            if executing
            else []
        )
        closing = (
            [
                r
                for r in records
                if str(r.get("status")) == "NEGOTIATION"
                or by_company_outcome.get(str(r.get("company_id")), {}).get("outcome") == "NEGOTIATION"
            ]
            if executing
            else []
        )

        first = priorities[0] if priorities else None
        contact_first: dict[str, Any]
        if first and mode == "PLANNING":
            contact_first = {
                "company": first.company,
                "company_id": first.company_id,
                "why": first.why_today,
                "email": first.email,
                "status": "READY TO SEND",
                "reason": execution_reason,
                "next_step": "Connect Gmail or Meta WhatsApp Business.",
                "next_action": "Connect Gmail or Meta WhatsApp Business.",
                "tracking": "Disabled until first successful delivery.",
            }
        elif first and mode == "READY":
            contact_first = {
                "company": first.company,
                "company_id": first.company_id,
                "why": first.why_today,
                "email": first.email,
                "status": "READY TO SEND",
                "reason": execution_reason,
                "next_step": "Approve draft and send via connected provider.",
                "next_action": "Approve draft and send via connected provider.",
                "tracking": "Disabled until first successful delivery.",
            }
        else:
            contact_first = {
                "company": first.company if first else None,
                "company_id": first.company_id if first else None,
                "why": first.why_today if first else "No Revenue Ready outreach records",
                "email": first.email if first else None,
                "next_step": first.suggested_next_step if first else None,
            }

        return {
            "question": "Who should Vansh contact today, why, and what did Beacon learn from yesterday?",
            "execution_mode": mode,
            "todays_priority": [c.model_dump(mode="json") for c in priorities[:5]],
            "follow_ups_due": followups[:10],
            "meetings_today": [
                {"company": r.get("company"), "company_id": r.get("company_id")} for r in meetings
            ],
            "replies_waiting": [
                {"company": r.get("company"), "company_id": r.get("company_id")} for r in replies_waiting
            ],
            "proposals_pending": [
                {"company": r.get("company"), "company_id": r.get("company_id")} for r in proposals
            ],
            "revenue_closing_soon": [
                {"company": r.get("company"), "company_id": r.get("company_id"), "pipeline_value": r.get("pipeline_value")}
                for r in closing
            ],
            "yesterday_summary": yesterday_summary
            or {"replies": 0, "meetings": 0, "wins": 0, "losses": 0, "pipeline_added": 0, "revenue_added": 0},
            "contact_first": contact_first,
            "learned_yesterday": (
                self._learned(yesterday_summary)
                if executing
                else "Learning offline until a verified delivery occurs."
            ),
            "todays_target": {
                "company": contact_first.get("company"),
                "status": contact_first.get("status") or "READY TO SEND",
                "reason": contact_first.get("reason") or execution_reason,
                "next_action": contact_first.get("next_action") or contact_first.get("next_step"),
                "tracking": contact_first.get("tracking") or "Disabled until first successful delivery.",
            },
        }

    def _learned(self, yesterday: dict[str, Any] | None) -> str:
        y = yesterday or {}
        parts = []
        if int(y.get("replies") or 0):
            parts.append(f"{y['replies']} replies")
        if int(y.get("meetings") or 0):
            parts.append(f"{y['meetings']} meetings")
        if int(y.get("wins") or 0):
            parts.append(f"{y['wins']} wins")
        if int(y.get("losses") or 0):
            parts.append(f"{y['losses']} losses")
        if not parts:
            return "No outcome activity yesterday — prioritize first outreach on highest RR score."
        return "Yesterday produced " + ", ".join(parts) + "."

    def _latest_by_company(self, outcomes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for e in sorted(outcomes, key=lambda x: str(x.get("timestamp") or "")):
            cid = str(e.get("company_id") or "")
            if cid:
                latest[cid] = e
        return latest

    def _top_priorities(
        self,
        records: list[dict[str, Any]],
        latest: dict[str, dict[str, Any]],
        *,
        execution_mode: str = "PLANNING",
    ) -> list[DailyBriefCard]:
        cards: list[DailyBriefCard] = []
        mode = (execution_mode or "PLANNING").upper()
        for r in records:
            brief = r.get("brief") or {}
            cid = str(r.get("company_id") or "")
            # In Planning/Ready, treat pipeline as READY TO SEND — ignore seeded CONTACTED/EMAIL_SENT
            if mode != "EXECUTING":
                state = "READY"
            else:
                state = str(latest.get(cid, {}).get("outcome") or r.get("status") or "READY")
            if state in {"WON", "LOST"}:
                continue
            step = self._next_step(state, execution_mode=mode)
            email = brief.get("decision_maker_email") or brief.get("business_email")
            score = float(brief.get("revenue_ready_score") or 0)
            cards.append(
                DailyBriefCard(
                    company=str(r.get("company") or UNKNOWN),
                    company_id=cid,
                    decision_maker=str(brief.get("decision_maker") or UNKNOWN),
                    email=email,
                    why_today=str(brief.get("why_now") or brief.get("recommended_cta") or UNKNOWN),
                    last_activity=str(latest.get(cid, {}).get("timestamp") or r.get("updated_at") or "")
                    if mode == "EXECUTING"
                    else None,
                    suggested_next_step=step,
                    priority=int(100 - min(score, 99)),
                )
            )
        # Higher RR score first → lower priority number
        return sorted(
            cards,
            key=lambda c: (
                0 if "Contact" in c.suggested_next_step else 1,
                -float(
                    next(
                        (
                            (x.get("brief") or {}).get("revenue_ready_score") or 0
                            for x in records
                            if str(x.get("company_id")) == c.company_id
                        ),
                        0,
                    )
                ),
            ),
        )

    def _followups_due(
        self, records: list[dict[str, Any]], latest: dict[str, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        now = datetime.now(UTC)
        out: list[dict[str, Any]] = []
        for r in records:
            cid = str(r.get("company_id") or "")
            state = str(latest.get(cid, {}).get("outcome") or r.get("status") or "")
            if state not in CONTACTED_LIKE and state != "CONTACTED":
                continue
            ts = latest.get(cid, {}).get("timestamp") or r.get("updated_at")
            days = 0.0
            if ts:
                try:
                    days = (now - datetime.fromisoformat(str(ts).replace("Z", "+00:00"))).total_seconds() / 86400
                except ValueError:
                    days = 0.0
            if days < 2:
                continue
            out.append(
                {
                    "company": r.get("company"),
                    "company_id": cid,
                    "days_since_contact": round(days, 1),
                    "reminder": "Send short follow-up",
                    "priority": "HIGH" if days >= 3 else "MEDIUM",
                }
            )
        return sorted(out, key=lambda x: float(x["days_since_contact"]), reverse=True)

    def _next_step(self, state: str, *, execution_mode: str = "PLANNING") -> str:
        mode = (execution_mode or "PLANNING").upper()
        if mode == "PLANNING":
            return "Connect Gmail or Meta WhatsApp Business."
        if mode == "READY":
            return "Approve draft and send via connected provider."
        return {
            "READY": "Send first outreach email",
            "CONTACTED": "Wait for reply or schedule follow-up in 3 days",
            "EMAIL_SENT": "Monitor opens; prepare follow-up",
            "REPLIED": "Book a meeting",
            "POSITIVE_REPLY": "Book a meeting immediately",
            "NEGATIVE_REPLY": "Log objection and pause or re-target",
            "MEETING_BOOKED": "Prepare agenda and proposal draft",
            "MEETING_COMPLETED": "Send proposal",
            "PROPOSAL_SENT": "Follow up on proposal",
            "NEGOTIATION": "Clarify commercial terms and close",
            "FOLLOW_UP_REQUIRED": "Send follow-up today",
            "FOLLOW_UP_SENT": "Wait 2 days then nudge",
            "NO_RESPONSE": "Send follow-up or mark lost",
        }.get(state, "Review account and choose next founder action")


class WeeklyReviewEngine:
    def build(
        self,
        *,
        records: list[dict[str, Any]],
        outcomes: list[dict[str, Any]],
        revenue_rows: list[dict[str, Any]],
        predictions: list[dict[str, Any]],
        objections: list[dict[str, Any]],
        attribution: dict[str, Any],
    ) -> dict[str, Any]:
        won_ids = {str(r.get("company_id")) for r in records if r.get("status") == "WON"}
        replied_roles: Counter[str] = Counter()
        industries: Counter[str] = Counter()
        services: Counter[str] = Counter()
        why: Counter[str] = Counter()
        for r in records:
            brief = r.get("brief") or {}
            if r.get("status") in {"REPLIED", "MEETING_BOOKED", "PROPOSAL_SENT", "NEGOTIATION", "WON"} or str(
                r.get("company_id")
            ) in won_ids:
                dm = str(brief.get("decision_maker") or "")
                role = dm.rsplit("(", 1)[1][:-1] if "(" in dm and dm.endswith(")") else "Unknown"
                replied_roles[role] += 1
                industries[str(brief.get("industry") or UNKNOWN)] += 1
                services[str(brief.get("recommended_service") or UNKNOWN)] += 1
                why[str(brief.get("why_now") or UNKNOWN)[:80]] += 1

        obj = Counter(str(o.get("label")) for o in objections)
        incorrect_rr = [
            p
            for p in predictions
            if str(p.get("interested")) == "NO" and str(p.get("decision_maker_correct")) == "NO"
        ]
        return {
            "best_industries": _top(industries),
            "best_company_sizes": [{"label": "unknown", "count": len(records)}],
            "best_services": _top(services),
            "best_why_now": _top(why),
            "best_dm_titles": _top(replied_roles),
            "average_reply_time_days": _avg_days(outcomes, from_states={"CONTACTED", "EMAIL_SENT"}, to_states=REPLY_LIKE),
            "average_sales_cycle_days": attribution.get("average_sales_cycle")
            or _avg_cycle(records),
            "biggest_objections": _top(obj),
            "largest_deal": attribution.get("largest_deal") or 0,
            "highest_roi_connector": _best_key(attribution.get("revenue_per_connector") or {"yc": 0}),
            "lowest_quality_connector": "product_hunt",  # known weak without token — evidence from ODU
            "incorrectly_marked_revenue_ready": [
                {"company": p.get("company"), "company_id": p.get("company_id")} for p in incorrect_rr
            ],
            "incorrectly_rejected": [],
            "revenue_rows": len(revenue_rows),
            "prediction_n": len(predictions),
        }


def _top(c: Counter[str], n: int = 5) -> list[dict[str, Any]]:
    return [{"label": k, "count": v} for k, v in c.most_common(n)]


def _best_key(d: dict[str, Any]) -> str:
    if not d:
        return UNKNOWN
    return max(d.items(), key=lambda kv: float(kv[1]))[0]


def _avg_days(outcomes: list[dict[str, Any]], *, from_states: set[str], to_states: set[str]) -> float | None:
    # simplified: not pairing rigorously — analytics placeholder until volume grows
    return None


def _avg_cycle(records: list[dict[str, Any]]) -> float | None:
    days: list[float] = []
    for r in records:
        if r.get("status") not in {"WON", "LOST"}:
            continue
        hist = list(r.get("status_history") or [])
        if len(hist) < 2:
            continue
        try:
            a = datetime.fromisoformat(str(hist[0].get("at")).replace("Z", "+00:00"))
            b = datetime.fromisoformat(str(hist[-1].get("at")).replace("Z", "+00:00"))
            days.append(max(0.0, (b - a).total_seconds() / 86400))
        except (ValueError, TypeError):
            continue
    if not days:
        return None
    return round(sum(days) / len(days), 1)
