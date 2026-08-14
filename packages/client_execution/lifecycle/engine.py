from __future__ import annotations

from client_execution.models.types import ClientExecutionInput, ClientLifecycleStage


class ClientLifecycleEngine:
    def infer_stage(self, item: ClientExecutionInput) -> ClientLifecycleStage:
        if item.archived:
            return ClientLifecycleStage.ARCHIVE
        if item.lost_client:
            return ClientLifecycleStage.LOST_CLIENT
        if item.referral_made:
            return ClientLifecycleStage.REFERRAL
        if item.renewal_due:
            return ClientLifecycleStage.RENEWAL
        if item.upsell_signal and item.launched:
            return ClientLifecycleStage.UPSELL_OPPORTUNITY
        if item.in_support:
            return ClientLifecycleStage.SUPPORT
        if item.launched:
            return ClientLifecycleStage.LAUNCH
        if item.in_review:
            return ClientLifecycleStage.REVIEW
        if item.testing_active:
            return ClientLifecycleStage.TESTING
        if item.development_active:
            return ClientLifecycleStage.DEVELOPMENT
        if item.design_complete:
            return ClientLifecycleStage.DESIGN
        if item.planning_complete:
            return ClientLifecycleStage.PLANNING
        if item.requirements_complete or (item.requirements and item.kickoff_scheduled):
            return ClientLifecycleStage.REQUIREMENTS_GATHERING
        if item.kickoff_scheduled:
            return ClientLifecycleStage.KICKOFF_SCHEDULED
        if item.won and not item.contract_signed:
            return ClientLifecycleStage.CONTRACT_PENDING
        if item.stage_hint:
            try:
                return ClientLifecycleStage(item.stage_hint)
            except ValueError:
                pass
        return ClientLifecycleStage.WON
