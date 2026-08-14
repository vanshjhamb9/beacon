from __future__ import annotations

from datetime import UTC, datetime

from autonomous_sales_agent.models.types import (
    AutonomousSalesAgentInput,
    SalesWorkflowStage,
    WorkflowTransition,
)


ALLOWED: dict[SalesWorkflowStage, set[SalesWorkflowStage]] = {
    SalesWorkflowStage.LEAD_DISCOVERED: {SalesWorkflowStage.QUALIFIED, SalesWorkflowStage.ARCHIVED},
    SalesWorkflowStage.QUALIFIED: {SalesWorkflowStage.RESEARCH_COMPLETE, SalesWorkflowStage.ARCHIVED},
    SalesWorkflowStage.RESEARCH_COMPLETE: {SalesWorkflowStage.DECISION_MAKERS_FOUND, SalesWorkflowStage.ARCHIVED},
    SalesWorkflowStage.DECISION_MAKERS_FOUND: {SalesWorkflowStage.SALES_PACKAGE_READY, SalesWorkflowStage.ARCHIVED},
    SalesWorkflowStage.SALES_PACKAGE_READY: {SalesWorkflowStage.CAMPAIGN_CREATED, SalesWorkflowStage.ARCHIVED},
    SalesWorkflowStage.CAMPAIGN_CREATED: {SalesWorkflowStage.FOUNDER_APPROVAL, SalesWorkflowStage.ARCHIVED},
    SalesWorkflowStage.FOUNDER_APPROVAL: {
        SalesWorkflowStage.EMAIL_SENT,
        SalesWorkflowStage.WHATSAPP_SENT,
        SalesWorkflowStage.ARCHIVED,
    },
    SalesWorkflowStage.EMAIL_SENT: {
        SalesWorkflowStage.WHATSAPP_SENT,
        SalesWorkflowStage.REPLY_RECEIVED,
        SalesWorkflowStage.FOLLOW_UP,
        SalesWorkflowStage.ARCHIVED,
    },
    SalesWorkflowStage.WHATSAPP_SENT: {
        SalesWorkflowStage.REPLY_RECEIVED,
        SalesWorkflowStage.FOLLOW_UP,
        SalesWorkflowStage.ARCHIVED,
    },
    SalesWorkflowStage.REPLY_RECEIVED: {
        SalesWorkflowStage.MEETING_REQUESTED,
        SalesWorkflowStage.PROPOSAL_PENDING,
        SalesWorkflowStage.FOLLOW_UP,
        SalesWorkflowStage.LOST,
    },
    SalesWorkflowStage.MEETING_REQUESTED: {SalesWorkflowStage.MEETING_BOOKED, SalesWorkflowStage.FOLLOW_UP, SalesWorkflowStage.LOST},
    SalesWorkflowStage.MEETING_BOOKED: {SalesWorkflowStage.PROPOSAL_PENDING, SalesWorkflowStage.FOLLOW_UP, SalesWorkflowStage.LOST},
    SalesWorkflowStage.PROPOSAL_PENDING: {SalesWorkflowStage.PROPOSAL_SENT, SalesWorkflowStage.FOLLOW_UP, SalesWorkflowStage.LOST},
    SalesWorkflowStage.PROPOSAL_SENT: {SalesWorkflowStage.NEGOTIATION, SalesWorkflowStage.WON, SalesWorkflowStage.LOST, SalesWorkflowStage.FOLLOW_UP},
    SalesWorkflowStage.NEGOTIATION: {SalesWorkflowStage.WON, SalesWorkflowStage.LOST, SalesWorkflowStage.FOLLOW_UP},
    SalesWorkflowStage.FOLLOW_UP: {
        SalesWorkflowStage.EMAIL_SENT,
        SalesWorkflowStage.WHATSAPP_SENT,
        SalesWorkflowStage.REPLY_RECEIVED,
        SalesWorkflowStage.ARCHIVED,
        SalesWorkflowStage.LOST,
    },
    SalesWorkflowStage.WON: set(),
    SalesWorkflowStage.LOST: {SalesWorkflowStage.FOLLOW_UP},
    SalesWorkflowStage.ARCHIVED: set(),
}


class SalesWorkflowEngine:
    def infer_stage(self, item: AutonomousSalesAgentInput) -> SalesWorkflowStage:
        if item.won:
            return SalesWorkflowStage.WON
        if item.lost:
            return SalesWorkflowStage.LOST
        if item.negotiation:
            return SalesWorkflowStage.NEGOTIATION
        if item.proposal_sent:
            return SalesWorkflowStage.PROPOSAL_SENT
        if item.proposal_pending or item.meeting_completed:
            return SalesWorkflowStage.PROPOSAL_PENDING
        if item.meeting_booked:
            return SalesWorkflowStage.MEETING_BOOKED
        if item.meeting_requested:
            return SalesWorkflowStage.MEETING_REQUESTED
        if item.reply_received:
            return SalesWorkflowStage.REPLY_RECEIVED
        if item.whatsapp_sent and not item.email_sent:
            return SalesWorkflowStage.WHATSAPP_SENT
        if item.email_sent:
            return SalesWorkflowStage.EMAIL_SENT
        if item.has_campaign and not item.campaign_approved:
            return SalesWorkflowStage.FOUNDER_APPROVAL
        if item.has_campaign:
            return SalesWorkflowStage.CAMPAIGN_CREATED
        if item.has_sales_package:
            return SalesWorkflowStage.SALES_PACKAGE_READY
        if item.has_decision_makers:
            return SalesWorkflowStage.DECISION_MAKERS_FOUND
        if item.stage_hint == "research_complete" or item.pains:
            return SalesWorkflowStage.RESEARCH_COMPLETE
        if item.priority_grade in {"A+", "A", "B"} or item.probability >= 40:
            return SalesWorkflowStage.QUALIFIED
        return SalesWorkflowStage.LEAD_DISCOVERED

    def can_transition(self, current: SalesWorkflowStage, target: SalesWorkflowStage) -> bool:
        if current == target:
            return True
        return target in ALLOWED.get(current, set())

    def transition(
        self,
        current: SalesWorkflowStage,
        target: SalesWorkflowStage,
        *,
        reason: str,
        evidence: list[str] | None = None,
        actor: str = "system",
        next_action: str = "continue",
        now: datetime | None = None,
    ) -> WorkflowTransition:
        if not self.can_transition(current, target):
            raise ValueError(f"Invalid ASA transition: {current.value} -> {target.value}")
        return WorkflowTransition(
            from_stage=current,
            to_stage=target,
            timestamp=now or datetime.now(UTC),
            reason=reason,
            evidence=evidence or [],
            actor=actor,
            next_action=next_action,
        )

    def build_transitions(self, item: AutonomousSalesAgentInput, stage: SalesWorkflowStage) -> list[WorkflowTransition]:
        now = item.now or datetime.now(UTC)
        return [
            WorkflowTransition(
                from_stage=None,
                to_stage=stage,
                timestamp=now,
                reason="inferred_from_signals",
                evidence=[f"stage:{stage.value}", f"probability:{item.probability}"],
                actor="system",
                next_action=self._default_next(stage),
            )
        ]

    def _default_next(self, stage: SalesWorkflowStage) -> str:
        mapping = {
            SalesWorkflowStage.FOUNDER_APPROVAL: "approve_campaign",
            SalesWorkflowStage.MEETING_BOOKED: "attend_meeting",
            SalesWorkflowStage.PROPOSAL_PENDING: "write_proposal",
            SalesWorkflowStage.NEGOTIATION: "negotiate",
            SalesWorkflowStage.FOLLOW_UP: "send_follow_up",
            SalesWorkflowStage.WON: "close_file",
            SalesWorkflowStage.LOST: "close_file",
        }
        return mapping.get(stage, "continue")
