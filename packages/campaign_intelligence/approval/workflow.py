from __future__ import annotations

from campaign_intelligence.models.types import CampaignStatus

ALLOWED_TRANSITIONS: dict[CampaignStatus, set[CampaignStatus]] = {
    CampaignStatus.DRAFT: {CampaignStatus.NEEDS_REVIEW, CampaignStatus.CANCELLED, CampaignStatus.REJECTED},
    CampaignStatus.NEEDS_REVIEW: {
        CampaignStatus.APPROVED,
        CampaignStatus.REJECTED,
        CampaignStatus.CANCELLED,
        CampaignStatus.DRAFT,
    },
    CampaignStatus.APPROVED: {CampaignStatus.SCHEDULED, CampaignStatus.PAUSED, CampaignStatus.CANCELLED},
    CampaignStatus.SCHEDULED: {CampaignStatus.PAUSED, CampaignStatus.COMPLETED, CampaignStatus.CANCELLED},
    CampaignStatus.PAUSED: {CampaignStatus.SCHEDULED, CampaignStatus.APPROVED, CampaignStatus.CANCELLED},
    CampaignStatus.COMPLETED: set(),
    CampaignStatus.CANCELLED: set(),
    CampaignStatus.REJECTED: {CampaignStatus.DRAFT, CampaignStatus.NEEDS_REVIEW},
}


class ApprovalWorkflow:
    def can_transition(self, current: CampaignStatus, target: CampaignStatus) -> bool:
        if current == target:
            return True
        return target in ALLOWED_TRANSITIONS.get(current, set())

    def transition(self, current: CampaignStatus, target: CampaignStatus) -> CampaignStatus:
        if not self.can_transition(current, target):
            raise ValueError(f"Invalid campaign transition: {current.value} -> {target.value}")
        return target

    def approve(self, current: CampaignStatus) -> CampaignStatus:
        return self.transition(current, CampaignStatus.APPROVED)

    def reject(self, current: CampaignStatus) -> CampaignStatus:
        return self.transition(current, CampaignStatus.REJECTED)

    def pause(self, current: CampaignStatus) -> CampaignStatus:
        return self.transition(current, CampaignStatus.PAUSED)

    def cancel(self, current: CampaignStatus) -> CampaignStatus:
        return self.transition(current, CampaignStatus.CANCELLED)

    def schedule(self, current: CampaignStatus) -> CampaignStatus:
        # Approving implies readiness; move approved campaigns to scheduled planning state.
        if current == CampaignStatus.NEEDS_REVIEW:
            current = CampaignStatus.APPROVED
        return self.transition(current, CampaignStatus.SCHEDULED)
