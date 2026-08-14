"""Opportunity Lifecycle — every opportunity moves through stages.

NEW → REVIEW → APPROVED → OUTREACH_READY → CONTACTED → REPLIED → MEETING
→ PROPOSAL → NEGOTIATION → WON → LOST → ARCHIVED → SPAM → NOT_ICP

Every transition: append-only, timestamped, auditable.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from . import OpportunityStage


class StageTransition:
    """Single stage transition record."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.from_stage: str = data.get("from_stage", "unknown")
        self.to_stage: str = data.get("to_stage", "unknown")
        self.action: str = data.get("action", "unknown")
        self.reason: str = data.get("reason", "")
        self.actor: str = data.get("actor", "system")
        self.timestamp: datetime = data.get("timestamp", datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "action": self.action,
            "reason": self.reason,
            "actor": self.actor,
            "timestamp": self.timestamp.isoformat(),
        }


class LifecycleManager:
    """Manages opportunity lifecycle transitions."""

    VALID_TRANSITIONS = {
        OpportunityStage.NEW.value: [
            OpportunityStage.REVIEW.value,
            OpportunityStage.APPROVED.value,
            OpportunityStage.ARCHIVED.value,
            OpportunityStage.SPAM.value,
            OpportunityStage.NOT_ICP.value,
        ],
        OpportunityStage.REVIEW.value: [
            OpportunityStage.APPROVED.value,
            OpportunityStage.ARCHIVED.value,
            OpportunityStage.SPAM.value,
            OpportunityStage.NOT_ICP.value,
        ],
        OpportunityStage.APPROVED.value: [
            OpportunityStage.OUTREACH_READY.value,
            OpportunityStage.ARCHIVED.value,
        ],
        OpportunityStage.OUTREACH_READY.value: [
            OpportunityStage.CONTACTED.value,
            OpportunityStage.ARCHIVED.value,
        ],
        OpportunityStage.CONTACTED.value: [
            OpportunityStage.REPLIED.value,
            OpportunityStage.ARCHIVED.value,
            OpportunityStage.LOST.value,
        ],
        OpportunityStage.REPLIED.value: [
            OpportunityStage.MEETING.value,
            OpportunityStage.ARCHIVED.value,
            OpportunityStage.LOST.value,
        ],
        OpportunityStage.MEETING.value: [
            OpportunityStage.PROPOSAL.value,
            OpportunityStage.ARCHIVED.value,
            OpportunityStage.LOST.value,
        ],
        OpportunityStage.PROPOSAL.value: [
            OpportunityStage.NEGOTIATION.value,
            OpportunityStage.ARCHIVED.value,
            OpportunityStage.LOST.value,
        ],
        OpportunityStage.NEGOTIATION.value: [
            OpportunityStage.WON.value,
            OpportunityStage.LOST.value,
            OpportunityStage.ARCHIVED.value,
        ],
        OpportunityStage.WON.value: [
            OpportunityStage.ARCHIVED.value,
        ],
        OpportunityStage.LOST.value: [
            OpportunityStage.ARCHIVED.value,
        ],
        OpportunityStage.ARCHIVED.value: [],
        OpportunityStage.SPAM.value: [],
        OpportunityStage.NOT_ICP.value: [],
    }

    def __init__(self):
        self._transitions: dict[str, list[StageTransition]] = {}
        self._current_stages: dict[str, str] = {}

    def transition(
        self,
        opportunity_id: str,
        to_stage: str,
        action: str = "manual",
        reason: str = "",
        actor: str = "founder",
    ) -> StageTransition | None:
        """Transition opportunity to new stage."""
        from_stage = self._current_stages.get(opportunity_id, OpportunityStage.NEW.value)

        # Validate transition
        valid_next = self.VALID_TRANSITIONS.get(from_stage, [])
        if to_stage not in valid_next:
            return None  # Invalid transition

        transition = StageTransition({
            "opportunity_id": opportunity_id,
            "from_stage": from_stage,
            "to_stage": to_stage,
            "action": action,
            "reason": reason,
            "actor": actor,
            "timestamp": datetime.now(timezone.utc),
        })

        # Record transition
        if opportunity_id not in self._transitions:
            self._transitions[opportunity_id] = []
        self._transitions[opportunity_id].append(transition)

        # Update current stage
        self._current_stages[opportunity_id] = to_stage

        return transition

    def get_transitions(self, opportunity_id: str) -> list[StageTransition]:
        """Get all transitions for opportunity."""
        return self._transitions.get(opportunity_id, [])

    def get_current_stage(self, opportunity_id: str) -> str:
        """Get current stage of opportunity."""
        return self._current_stages.get(opportunity_id, OpportunityStage.NEW.value)

    def get_valid_next_stages(self, opportunity_id: str) -> list[str]:
        """Get valid next stages for opportunity."""
        current = self.get_current_stage(opportunity_id)
        return self.VALID_TRANSITIONS.get(current, [])

    def can_transition(self, opportunity_id: str, to_stage: str) -> bool:
        """Check if transition is valid."""
        valid_next = self.get_valid_next_stages(opportunity_id)
        return to_stage in valid_next

    def get_stage_history(self, opportunity_id: str) -> list[dict[str, Any]]:
        """Get stage history for opportunity."""
        transitions = self.get_transitions(opportunity_id)
        return [t.to_dict() for t in transitions]

    def get_all_current_stages(self) -> dict[str, str]:
        """Get current stages for all opportunities."""
        return dict(self._current_stages)

    def get_opportunities_by_stage(self, stage: str) -> list[str]:
        """Get all opportunities at a specific stage."""
        return [
            opp_id for opp_id, current_stage in self._current_stages.items()
            if current_stage == stage
        ]

    def get_statistics(self) -> dict[str, Any]:
        """Get lifecycle statistics."""
        total_transitions = sum(len(t) for t in self._transitions.values())
        by_stage = {}
        for stage in self._current_stages.values():
            by_stage[stage] = by_stage.get(stage, 0) + 1

        return {
            "total_opportunities": len(self._current_stages),
            "total_transitions": total_transitions,
            "by_stage": by_stage,
        }
