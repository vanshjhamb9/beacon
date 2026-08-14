from __future__ import annotations

from revenue_hunter.models.types import (
    PriorityGrade,
    RevenueDossier,
    WorkQueueAction,
    WorkQueueItem,
    WorkQueueStatus,
)


class WorkQueueBuilder:
    """Founder wake-up queue: Approve / Send / Reply / Book Meeting only."""

    DEFAULT_ACTIONS = [
        WorkQueueAction.APPROVE,
        WorkQueueAction.SEND,
        WorkQueueAction.REPLY,
        WorkQueueAction.BOOK_MEETING,
    ]

    def build(self, dossiers: list[RevenueDossier], *, limit: int = 25) -> list[WorkQueueItem]:
        eligible = [
            d
            for d in dossiers
            if d.priority_grade in {PriorityGrade.A_PLUS, PriorityGrade.A} and d.proceed_to_campaign
        ]
        eligible.sort(key=lambda d: (-d.revenue_score, d.company_name))
        items: list[WorkQueueItem] = []
        for idx, d in enumerate(eligible[:limit], start=1):
            primary = d.decision_makers[0] if d.decision_makers else None
            why_today = d.why_now.why_today if d.why_now else "Priority outreach today."
            items.append(
                WorkQueueItem(
                    company_id=d.company_id,
                    company_name=d.company_name,
                    priority_grade=d.priority_grade,
                    recommended_service=d.recommended_service,
                    why_today=why_today,
                    expected_budget=d.expected_budget,
                    probability=d.probability,
                    primary_contact=primary,
                    status=WorkQueueStatus.PENDING,
                    allowed_actions=list(self.DEFAULT_ACTIONS),
                    rank=idx,
                )
            )
        return items

    def apply_action(self, item: WorkQueueItem, action: WorkQueueAction) -> WorkQueueItem:
        mapping = {
            WorkQueueAction.APPROVE: WorkQueueStatus.APPROVED,
            WorkQueueAction.SEND: WorkQueueStatus.SENT,
            WorkQueueAction.REPLY: WorkQueueStatus.REPLIED,
            WorkQueueAction.BOOK_MEETING: WorkQueueStatus.MEETING_BOOKED,
            WorkQueueAction.SKIP: WorkQueueStatus.SKIPPED,
            WorkQueueAction.DEFER: WorkQueueStatus.DEFERRED,
        }
        if action not in item.allowed_actions and action not in {
            WorkQueueAction.SKIP,
            WorkQueueAction.DEFER,
        }:
            raise ValueError(f"Action {action.value} not allowed for this queue item")
        return item.model_copy(update={"status": mapping[action]})
