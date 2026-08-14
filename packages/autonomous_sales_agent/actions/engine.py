from __future__ import annotations

from autonomous_sales_agent.models.types import (
    AutonomousSalesAgentInput,
    FollowUpChannel,
    FollowUpRecommendation,
    NextActionKind,
    NextBestAction,
    SalesWorkflowStage,
)


class NextBestActionEngine:
    """Recommend exactly ONE next action per company."""

    def recommend(
        self,
        item: AutonomousSalesAgentInput,
        *,
        stage: SalesWorkflowStage,
        follow_up: FollowUpRecommendation,
    ) -> NextBestAction:
        if item.won or item.lost or stage == SalesWorkflowStage.ARCHIVED:
            return NextBestAction(
                action=NextActionKind.CLOSE_FILE,
                confidence=95.0,
                reason="Deal terminal — archive and capture outcome notes.",
                evidence=[f"stage:{stage.value}"],
                expected_impact="Clean pipeline hygiene",
            )
        if stage == SalesWorkflowStage.FOUNDER_APPROVAL or (item.has_campaign and not item.campaign_approved):
            return NextBestAction(
                action=NextActionKind.APPROVE_CAMPAIGN,
                confidence=92.0,
                reason="Campaign ready — founder approval required before send.",
                evidence=["campaign:needs_approval"],
                expected_impact="Unlock outreach",
            )
        if stage == SalesWorkflowStage.MEETING_BOOKED:
            return NextBestAction(
                action=NextActionKind.ATTEND_MEETING,
                confidence=94.0,
                reason="Meeting booked — prepare pack and attend.",
                evidence=["meeting:booked"],
                expected_impact="Advance to proposal",
            )
        if stage in {SalesWorkflowStage.PROPOSAL_PENDING, SalesWorkflowStage.MEETING_BOOKED} and item.meeting_completed:
            return NextBestAction(
                action=NextActionKind.WRITE_PROPOSAL,
                confidence=90.0,
                reason="Meeting done — founder should write/send proposal.",
                evidence=["proposal:pending"],
                expected_impact="Convert meeting to commercial next step",
            )
        if stage == SalesWorkflowStage.PROPOSAL_PENDING:
            return NextBestAction(
                action=NextActionKind.PREPARE_PROPOSAL,
                confidence=88.0,
                reason="Proposal pending founder authorship.",
                evidence=["stage:proposal_pending"],
                expected_impact="Create commercial momentum",
            )
        if stage == SalesWorkflowStage.NEGOTIATION:
            return NextBestAction(
                action=NextActionKind.NEGOTIATE,
                confidence=91.0,
                reason="Deal in negotiation — founder-led close path.",
                evidence=["stage:negotiation"],
                expected_impact="Win or clarify loss reason",
            )
        if item.reply_received and not item.meeting_booked and not item.meeting_requested:
            if "meet" in " ".join(item.recent_activity).lower() or item.buying_intent_score >= 70:
                return NextBestAction(
                    action=NextActionKind.BOOK_MEETING,
                    confidence=86.0,
                    reason="High-intent reply — book discovery meeting.",
                    evidence=[f"intent:{item.buying_intent_score}"],
                    expected_impact="Create meeting opportunity",
                )
            return NextBestAction(
                action=NextActionKind.CALL,
                confidence=78.0,
                reason="Reply received — personal call or reply recommended.",
                evidence=["reply:true"],
                expected_impact="Qualify next step",
            )
        if follow_up.due:
            if follow_up.channel == FollowUpChannel.WHATSAPP:
                return NextBestAction(
                    action=NextActionKind.WHATSAPP,
                    confidence=82.0,
                    reason=follow_up.message_hint,
                    evidence=follow_up.evidence,
                    expected_impact="Re-engage via WhatsApp",
                )
            if follow_up.channel == FollowUpChannel.VALUE_EMAIL:
                return NextBestAction(
                    action=NextActionKind.SEND_CASE_STUDY,
                    confidence=80.0,
                    reason=follow_up.message_hint,
                    evidence=follow_up.evidence,
                    expected_impact="Re-engage with proof",
                )
            if follow_up.channel == FollowUpChannel.ARCHIVE:
                return NextBestAction(
                    action=NextActionKind.CLOSE_FILE,
                    confidence=85.0,
                    reason=follow_up.message_hint,
                    evidence=follow_up.evidence,
                    expected_impact="Free founder attention",
                )
            return NextBestAction(
                action=NextActionKind.SEND_FOLLOW_UP,
                confidence=84.0,
                reason=follow_up.message_hint,
                evidence=follow_up.evidence,
                expected_impact="Recover silent lead",
            )
        return NextBestAction(
            action=NextActionKind.WAIT,
            confidence=70.0,
            reason="No founder action required — automation continues.",
            evidence=[f"stage:{stage.value}", f"days:{item.days_since_last_touch}"],
            expected_impact="Protect founder focus",
        )
