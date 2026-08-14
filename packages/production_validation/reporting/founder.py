from __future__ import annotations

from production_validation.models.types import FounderActionBoard, ProductionValidationInput


class FounderExperienceEngine:
    """Home board answers: who to contact, who replied, who booked, what to do now."""

    def build(self, item: ProductionValidationInput) -> FounderActionBoard:
        q = item.founder_queues or {}
        contact = list(q.get("contact_now") or [])
        replied = list(q.get("replied") or [])
        booked = list(q.get("booked") or [])
        proposals = list(q.get("needs_proposal") or [])
        follow = list(q.get("needs_follow_up") or [])
        stuck = list(q.get("revenue_stuck") or [])
        do_now: list[str] = []
        if contact:
            do_now.append(f"Contact {contact[0].get('company_name') or 'top account'} now")
        if replied:
            do_now.append(f"Reply to {replied[0].get('company_name') or 'inbound'} within 1 hour")
        if booked:
            do_now.append(f"Open meeting pack for {booked[0].get('company_name') or 'meeting'}")
        if proposals:
            do_now.append(f"Send proposal to {proposals[0].get('company_name') or 'opportunity'}")
        if follow:
            do_now.append(f"Follow up {follow[0].get('company_name') or 'warm lead'}")
        if stuck:
            do_now.append(f"Unblock revenue on {stuck[0].get('company_name') or 'stuck deal'}")
        if not do_now:
            do_now.append("Review Approval Center for pending campaigns")
        return FounderActionBoard(
            contact_now=contact[:10],
            replied=replied[:10],
            booked=booked[:10],
            needs_proposal=proposals[:10],
            needs_follow_up=follow[:10],
            revenue_stuck=stuck[:10],
            do_now=do_now[:6],
            evidence=[f"actions:{len(do_now)}"],
        )
