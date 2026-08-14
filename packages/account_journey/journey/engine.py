from __future__ import annotations

from datetime import UTC, datetime

from account_journey.models.types import AccountJourneyInput, JourneyStage, JourneyTransition


class AccountJourneyEngine:
    def infer_stage(self, item: AccountJourneyInput) -> JourneyStage:
        if item.won:
            return JourneyStage.WON
        if item.lost:
            return JourneyStage.LOST
        if item.reactivated:
            return JourneyStage.REACTIVATED
        if item.dormant_days >= 20 and not item.replied and not item.meeting_scheduled:
            return JourneyStage.DORMANT
        if item.negotiation:
            return JourneyStage.NEGOTIATION
        if item.proposal_requested:
            return JourneyStage.PROPOSAL_REQUESTED
        if item.meeting_scheduled or item.calendar_booked:
            return JourneyStage.MEETING_SCHEDULED
        if item.replied:
            return JourneyStage.REPLIED
        if item.clicked or item.cta_clicks > 0:
            return JourneyStage.CLICKED
        if item.opened:
            return JourneyStage.OPENED
        if item.emailed or item.whatsapp_sent:
            return JourneyStage.CONTACTED
        if item.campaign_active:
            return JourneyStage.CAMPAIGN_ACTIVE
        if item.outreach_ready:
            return JourneyStage.OUTREACH_READY
        if item.has_decision_makers or item.decision_makers:
            return JourneyStage.DECISION_MAKERS
        if item.enriched:
            return JourneyStage.ENRICHED
        if item.qualified or item.probability >= 40:
            return JourneyStage.QUALIFIED
        return JourneyStage.DISCOVERED

    def build_transitions(self, item: AccountJourneyInput, stage: JourneyStage) -> list[JourneyTransition]:
        now = item.now or datetime.now(UTC)
        return [
            JourneyTransition(
                from_stage=None,
                to_stage=stage,
                timestamp=now,
                reason="inferred_from_signals",
                evidence=[f"stage:{stage.value}", f"probability:{item.probability}"],
                actor="system",
            )
        ]
