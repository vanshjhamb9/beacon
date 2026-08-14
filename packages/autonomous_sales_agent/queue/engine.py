from __future__ import annotations

from autonomous_sales_agent.models.types import (
    AutonomousSalesAgentInput,
    FounderWorkItem,
    NextActionKind,
    NextBestAction,
    SalesWorkflowStage,
)


class FounderWorkQueueEngine:
    """Founder only sees meetings, proposals, negotiation, approvals, high-intent, urgent follow-ups."""

    def build(
        self,
        item: AutonomousSalesAgentInput,
        *,
        stage: SalesWorkflowStage,
        next_action: NextBestAction,
    ) -> list[FounderWorkItem]:
        items: list[FounderWorkItem] = []
        for m in item.meetings_today:
            items.append(
                FounderWorkItem(
                    kind="meet_today",
                    company_id=item.company_id,
                    company_name=str(m.get("company_name") or item.company_name),
                    priority="P0",
                    summary=str(m.get("summary") or "Meeting today — open meeting pack"),
                    evidence=["queue:meet_today"],
                )
            )
        for p in item.proposal_queue:
            items.append(
                FounderWorkItem(
                    kind="proposal_pending",
                    company_id=item.company_id,
                    company_name=str(p.get("company_name") or item.company_name),
                    priority="P0",
                    summary=str(p.get("summary") or "Proposal pending founder authorship"),
                    evidence=["queue:proposal_pending"],
                )
            )
        for n in item.negotiation_queue:
            items.append(
                FounderWorkItem(
                    kind="negotiation",
                    company_id=item.company_id,
                    company_name=str(n.get("company_name") or item.company_name),
                    priority="P0",
                    summary=str(n.get("summary") or "Negotiation — founder close path"),
                    evidence=["queue:negotiation"],
                )
            )
        for a in item.pending_approvals:
            items.append(
                FounderWorkItem(
                    kind="needs_approval",
                    company_id=item.company_id,
                    company_name=str(a.get("company_name") or item.company_name),
                    priority="P1",
                    summary=str(a.get("summary") or "Campaign needs founder approval"),
                    evidence=["queue:needs_approval"],
                )
            )
        for r in item.high_intent_replies:
            items.append(
                FounderWorkItem(
                    kind="high_intent_reply",
                    company_id=item.company_id,
                    company_name=str(r.get("company_name") or item.company_name),
                    priority="P0",
                    summary=str(r.get("summary") or "High-intent reply — respond now"),
                    evidence=["queue:high_intent_reply"],
                )
            )
        if next_action.action == NextActionKind.SEND_FOLLOW_UP and next_action.confidence >= 80:
            items.append(
                FounderWorkItem(
                    kind="urgent_follow_up",
                    company_id=item.company_id,
                    company_name=item.company_name,
                    priority="P1",
                    summary=next_action.reason,
                    evidence=next_action.evidence,
                )
            )
        # Stage-derived founder-only items when queues empty but stage demands founder
        if stage == SalesWorkflowStage.FOUNDER_APPROVAL and not any(i.kind == "needs_approval" for i in items):
            items.append(
                FounderWorkItem(
                    kind="needs_approval",
                    company_id=item.company_id,
                    company_name=item.company_name,
                    priority="P1",
                    summary="Approve outreach campaign",
                    evidence=["stage:founder_approval"],
                )
            )
        if stage == SalesWorkflowStage.MEETING_BOOKED and not any(i.kind == "meet_today" for i in items):
            items.append(
                FounderWorkItem(
                    kind="meet_today",
                    company_id=item.company_id,
                    company_name=item.company_name,
                    priority="P0",
                    summary="Attend discovery meeting",
                    evidence=["stage:meeting_booked"],
                )
            )
        if stage == SalesWorkflowStage.PROPOSAL_PENDING and not any(i.kind == "proposal_pending" for i in items):
            items.append(
                FounderWorkItem(
                    kind="proposal_pending",
                    company_id=item.company_id,
                    company_name=item.company_name,
                    priority="P0",
                    summary="Write and send proposal",
                    evidence=["stage:proposal_pending"],
                )
            )
        if stage == SalesWorkflowStage.NEGOTIATION and not any(i.kind == "negotiation" for i in items):
            items.append(
                FounderWorkItem(
                    kind="negotiation",
                    company_id=item.company_id,
                    company_name=item.company_name,
                    priority="P0",
                    summary="Final negotiation / close",
                    evidence=["stage:negotiation"],
                )
            )
        return items
