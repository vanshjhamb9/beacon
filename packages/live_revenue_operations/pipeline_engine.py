"""Pipeline Engine — Kanban board management for opportunities.

Kanban board stages:
    NEW → REVIEW → APPROVED → CONTACTED → REPLIED → MEETING
    → PROPOSAL → NEGOTIATION → WON → LOST

Drag-and-drop updates status.
Every move creates append-only history.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from . import OpportunityStage


class PipelineCard:
    """Single pipeline card (opportunity on Kanban board)."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.company_name: str = data.get("company_name", "unknown")
        self.website: str = data.get("website", "unknown")
        self.buying_signal: str = data.get("buying_signal", "unknown")
        self.connector: str = data.get("connector", "unknown")
        self.quality_score: int = data.get("quality_score", 0)
        self.stage: str = data.get("stage", OpportunityStage.NEW.value)
        self.position: int = data.get("position", 0)
        self.assigned_to: str = data.get("assigned_to", "unassigned")
        self.tags: list[str] = data.get("tags", [])
        self.created_at: datetime = data.get("created_at", datetime.now(timezone.utc))
        self.updated_at: datetime = data.get("updated_at", datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "company_name": self.company_name,
            "website": self.website,
            "buying_signal": self.buying_signal,
            "connector": self.connector,
            "quality_score": self.quality_score,
            "stage": self.stage,
            "position": self.position,
            "assigned_to": self.assigned_to,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class PipelineEngine:
    """Pipeline Kanban board engine."""

    def __init__(self):
        self._cards: dict[str, PipelineCard] = {}
        self._stage_columns: dict[str, list[str]] = {
            stage.value: [] for stage in OpportunityStage
        }
        self._move_history: list[dict[str, Any]] = []

    def add_card(
        self,
        opportunity_id: str,
        company_name: str,
        website: str,
        buying_signal: str,
        connector: str,
        quality_score: int,
        stage: str = OpportunityStage.NEW.value,
    ) -> PipelineCard:
        """Add new card to pipeline."""
        card = PipelineCard({
            "opportunity_id": opportunity_id,
            "company_name": company_name,
            "website": website,
            "buying_signal": buying_signal,
            "connector": connector,
            "quality_score": quality_score,
            "stage": stage,
            "position": len(self._stage_columns.get(stage, [])),
        })

        self._cards[card.id] = card
        if stage not in self._stage_columns:
            self._stage_columns[stage] = []
        self._stage_columns[stage].append(card.id)

        return card

    def move_card(
        self,
        card_id: str,
        to_stage: str,
        position: int | None = None,
    ) -> PipelineCard | None:
        """Move card to new stage (drag-and-drop)."""
        card = self._cards.get(card_id)
        if not card:
            return None

        old_stage = card.stage

        # Remove from old stage
        if old_stage in self._stage_columns:
            self._stage_columns[old_stage] = [
                cid for cid in self._stage_columns[old_stage] if cid != card_id
            ]

        # Add to new stage
        if to_stage not in self._stage_columns:
            self._stage_columns[to_stage] = []

        if position is not None and position <= len(self._stage_columns[to_stage]):
            self._stage_columns[to_stage].insert(position, card_id)
        else:
            self._stage_columns[to_stage].append(card_id)

        # Update card
        card.stage = to_stage
        card.position = position if position is not None else len(self._stage_columns[to_stage]) - 1
        card.updated_at = datetime.now(timezone.utc)

        # Record move
        self._move_history.append({
            "card_id": card_id,
            "opportunity_id": card.opportunity_id,
            "from_stage": old_stage,
            "to_stage": to_stage,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return card

    def get_card(self, card_id: str) -> PipelineCard | None:
        """Get pipeline card by ID."""
        return self._cards.get(card_id)

    def get_card_by_opportunity(self, opportunity_id: str) -> PipelineCard | None:
        """Get pipeline card by opportunity ID."""
        for card in self._cards.values():
            if card.opportunity_id == opportunity_id:
                return card
        return None

    def get_stage_column(self, stage: str) -> list[PipelineCard]:
        """Get all cards in a stage column."""
        card_ids = self._stage_columns.get(stage, [])
        return [self._cards[cid] for cid in card_ids if cid in self._cards]

    def get_all_stages(self) -> dict[str, list[dict[str, Any]]]:
        """Get all stages with their cards."""
        result = {}
        for stage, card_ids in self._stage_columns.items():
            result[stage] = [
                self._cards[cid].to_dict()
                for cid in card_ids
                if cid in self._cards
            ]
        return result

    def reorder_card(self, card_id: str, new_position: int) -> PipelineCard | None:
        """Reorder card within same stage."""
        card = self._cards.get(card_id)
        if not card:
            return None

        stage = card.stage
        card_ids = self._stage_columns.get(stage, [])

        # Remove card from current position
        card_ids = [cid for cid in card_ids if cid != card_id]

        # Insert at new position
        if new_position <= len(card_ids):
            card_ids.insert(new_position, card_id)
        else:
            card_ids.append(card_id)

        self._stage_columns[stage] = card_ids

        # Update positions
        for i, cid in enumerate(card_ids):
            if cid in self._cards:
                self._cards[cid].position = i

        card.updated_at = datetime.now(timezone.utc)
        return card

    def get_move_history(self, card_id: str | None = None) -> list[dict[str, Any]]:
        """Get move history for card or all cards."""
        if card_id:
            return [m for m in self._move_history if m.get("card_id") == card_id]
        return list(self._move_history)

    def get_statistics(self) -> dict[str, Any]:
        """Get pipeline statistics."""
        total_cards = len(self._cards)
        by_stage = {stage: len(cards) for stage, cards in self._stage_columns.items()}
        by_connector = {}
        for card in self._cards.values():
            by_connector[card.connector] = by_connector.get(card.connector, 0) + 1

        return {
            "total_cards": total_cards,
            "by_stage": by_stage,
            "by_connector": by_connector,
            "total_moves": len(self._move_history),
        }
