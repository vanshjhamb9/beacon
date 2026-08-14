from __future__ import annotations

from datetime import UTC, datetime

from live_revenue_execution.models.types import LREInput, LREStage


# Append-only lifecycle map — orchestration only, does not replace campaign statuses.
ALLOWED_LRE_TRANSITIONS: dict[LREStage, set[LREStage]] = {
    LREStage.DISCOVERED: {LREStage.VERIFIED, LREStage.STOPPED},
    LREStage.VERIFIED: {LREStage.ENRICHED, LREStage.STOPPED},
    LREStage.ENRICHED: {LREStage.DECISION_MAKER_FOUND, LREStage.STOPPED},
    LREStage.DECISION_MAKER_FOUND: {LREStage.RANKED_A_PLUS, LREStage.STRATEGY_READY, LREStage.STOPPED},
    LREStage.RANKED_A_PLUS: {LREStage.STRATEGY_READY, LREStage.STOPPED},
    LREStage.STRATEGY_READY: {LREStage.OUTREACH_READY, LREStage.STOPPED},
    LREStage.OUTREACH_READY: {LREStage.AWAITING_APPROVAL, LREStage.STOPPED},
    LREStage.AWAITING_APPROVAL: {LREStage.APPROVED, LREStage.STOPPED},
    LREStage.APPROVED: {LREStage.EMAIL_SENT, LREStage.WHATSAPP_SENT, LREStage.STOPPED},
    LREStage.EMAIL_SENT: {LREStage.OPENED, LREStage.CLICKED, LREStage.REPLIED, LREStage.WHATSAPP_SENT, LREStage.STOPPED},
    LREStage.OPENED: {LREStage.CLICKED, LREStage.REPLIED, LREStage.WHATSAPP_SENT, LREStage.STOPPED},
    LREStage.CLICKED: {LREStage.REPLIED, LREStage.WHATSAPP_SENT, LREStage.STOPPED},
    LREStage.WHATSAPP_SENT: {LREStage.REPLIED, LREStage.STOPPED},
    LREStage.REPLIED: {LREStage.MEETING_BOOKED, LREStage.PROPOSAL_READY, LREStage.STOPPED, LREStage.LOST},
    LREStage.MEETING_BOOKED: {LREStage.MEETING_PACK_READY, LREStage.STOPPED},
    LREStage.MEETING_PACK_READY: {LREStage.PROPOSAL_READY, LREStage.STOPPED},
    LREStage.PROPOSAL_READY: {LREStage.PROPOSAL_SENT, LREStage.STOPPED},
    LREStage.PROPOSAL_SENT: {LREStage.WON, LREStage.LOST, LREStage.STOPPED},
    LREStage.WON: set(),
    LREStage.LOST: set(),
    LREStage.STOPPED: set(),
}


class CampaignLifecycleEngine:
    def infer_stage(self, item: LREInput) -> LREStage:
        counts = item.funnel_counts or {}
        if counts.get("won"):
            return LREStage.WON
        if counts.get("lost"):
            return LREStage.LOST
        if counts.get("proposal_sent"):
            return LREStage.PROPOSAL_SENT
        if counts.get("meeting_booked"):
            return LREStage.MEETING_BOOKED
        if counts.get("replies"):
            return LREStage.REPLIED
        if counts.get("whatsapp_sent"):
            return LREStage.WHATSAPP_SENT
        if counts.get("clicked"):
            return LREStage.CLICKED
        if counts.get("opened"):
            return LREStage.OPENED
        if counts.get("emails"):
            return LREStage.EMAIL_SENT
        if item.campaign_id and item.email_body:
            return LREStage.AWAITING_APPROVAL
        if item.priority_grade in {"A+", "A"}:
            return LREStage.RANKED_A_PLUS if item.buying_intent_score else LREStage.OUTREACH_READY
        if item.decision_makers:
            return LREStage.DECISION_MAKER_FOUND
        return LREStage.STRATEGY_READY

    def can_transition(self, current: LREStage, target: LREStage) -> bool:
        if current == target:
            return True
        return target in ALLOWED_LRE_TRANSITIONS.get(current, set())

    def transition(self, current: LREStage, target: LREStage) -> LREStage:
        if not self.can_transition(current, target):
            raise ValueError(f"Invalid LRE transition: {current.value} -> {target.value}")
        return target

    def event(self, *, stage: LREStage, detail: str, actor: str = "system") -> dict:
        return {
            "stage": stage.value,
            "detail": detail,
            "actor": actor,
            "occurred_at": datetime.now(UTC).isoformat(),
            "immutable": True,
        }
