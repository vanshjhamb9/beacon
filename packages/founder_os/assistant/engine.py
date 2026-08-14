from __future__ import annotations

from uuid import UUID

from founder_os.models.types import ContactRecommendation, FounderAssistantBrief, FounderOsInput


class FounderAssistantEngine:
    """Deterministic VP-of-Sales answers. Optional Sales Copilot stays outside this engine."""

    def brief(self, data: FounderOsInput, *, limit: int = 10) -> FounderAssistantBrief:
        contacts: list[ContactRecommendation] = []
        for idx, row in enumerate(data.top_companies[:limit], start=1):
            company_id = self._uuid(row.get("company_id"))
            if company_id is None:
                continue
            name = str(row.get("company_name") or "Unknown")
            service = str(row.get("recommended_service") or row.get("what_to_sell") or "Custom AI")
            why_them = str(
                row.get("why_them")
                or row.get("company_summary")
                or f"{name} matches ICP with grade {row.get('priority_grade', 'A')}."
            )
            why_today = str(row.get("why_today") or row.get("why_now") or "Buying pressure is active today.")
            budget = str(row.get("expected_budget") or row.get("budget_range") or "$25k–$55k")
            probability = float(row.get("probability") or row.get("expected_close_probability") or 55.0)
            evidence = [str(e) for e in (row.get("evidence") or row.get("evidence_chain") or [])][:12]
            if not evidence:
                evidence = [
                    f"service:{service}",
                    f"budget:{budget}",
                    f"probability:{probability}",
                    f"grade:{row.get('priority_grade', 'n/a')}",
                ]
            next_action = str(
                row.get("next_action")
                or ("Approve and send outreach" if row.get("proceed_to_campaign") else "Review dossier then contact")
            )
            contacts.append(
                ContactRecommendation(
                    company_id=company_id,
                    company_name=name,
                    why_them=why_them,
                    why_today=why_today if why_today.startswith("Why") else f"Why today: {why_today}",
                    what_to_sell=service,
                    expected_budget=budget,
                    expected_close_probability=round(min(95.0, max(5.0, probability)), 4),
                    next_action=next_action,
                    evidence=evidence,
                    priority_grade=str(row.get("priority_grade")) if row.get("priority_grade") else None,
                    rank=idx,
                )
            )

        mission = (
            f"Contact {len(contacts)} priority accounts, clear "
            f"{data.campaigns_waiting_approval} campaign approvals and "
            f"{data.replies_waiting} replies, run {data.meetings_today} meetings."
        )
        summary = (
            f"Who: {', '.join(c.company_name for c in contacts[:5]) or 'no A+/A accounts yet'}. "
            f"Sell with evidence-backed budgets. Expected revenue ${data.expected_revenue:,.0f}."
        )
        evidence = [
            f"contacts:{len(contacts)}",
            f"a_plus:{data.a_plus_opportunities}",
            f"pipeline:{data.estimated_pipeline:.0f}",
        ]
        return FounderAssistantBrief(
            greeting="Good morning — here is your revenue mission.",
            mission=mission,
            contacts=contacts,
            summary=summary,
            evidence=evidence,
        )

    def _uuid(self, value: object) -> UUID | None:
        if value is None:
            return None
        try:
            return value if isinstance(value, UUID) else UUID(str(value))
        except (TypeError, ValueError):
            return None
