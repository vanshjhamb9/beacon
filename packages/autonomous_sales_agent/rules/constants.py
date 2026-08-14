from __future__ import annotations

from autonomous_sales_agent.models.types import FollowUpConfig, SalesWorkflowStage


# Deterministic business rules — configurable constants only
DEFAULT_FOLLOW_UP = FollowUpConfig()

FOUNDER_ONLY_STAGES: frozenset[SalesWorkflowStage] = frozenset(
    {
        SalesWorkflowStage.FOUNDER_APPROVAL,
        SalesWorkflowStage.MEETING_BOOKED,
        SalesWorkflowStage.PROPOSAL_PENDING,
        SalesWorkflowStage.NEGOTIATION,
    }
)

FOUNDER_QUEUE_KINDS: frozenset[str] = frozenset(
    {
        "meet_today",
        "proposal_pending",
        "negotiation",
        "needs_approval",
        "high_intent_reply",
        "urgent_follow_up",
    }
)
