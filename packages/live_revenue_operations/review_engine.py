"""Review Engine — human review workspace for opportunities.

Every opportunity gets:
    Evidence Timeline
    Buying Signal
    Connector
    DQE Report
    LOVP Report
    Source URLs
    Signal Age
    Quality Score
    Founder Notes
    Current Stage
    Review History

Everything fully explainable.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class ReviewSession:
    """Single review session for an opportunity."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.reviewer: str = data.get("reviewer", "founder")
        self.decision: str | None = data.get("decision")
        self.notes: str = data.get("notes", "")
        self.started_at: datetime = data.get("started_at", datetime.now(timezone.utc))
        self.completed_at: datetime | None = data.get("completed_at")
        self.duration_seconds: float | None = data.get("duration_seconds")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "reviewer": self.reviewer,
            "decision": self.decision,
            "notes": self.notes,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
        }


class ReviewEngine:
    """Human review workspace engine."""

    def __init__(self):
        self._sessions: dict[str, ReviewSession] = {}
        self._reviews_by_opportunity: dict[str, list[str]] = {}
        self._active_sessions: dict[str, ReviewSession] = {}

    def start_review(
        self,
        opportunity_id: str,
        reviewer: str = "founder",
    ) -> ReviewSession:
        """Start a review session."""
        session = ReviewSession({
            "opportunity_id": opportunity_id,
            "reviewer": reviewer,
            "started_at": datetime.now(timezone.utc),
        })

        self._sessions[session.id] = session
        self._active_sessions[opportunity_id] = session

        if opportunity_id not in self._reviews_by_opportunity:
            self._reviews_by_opportunity[opportunity_id] = []
        self._reviews_by_opportunity[opportunity_id].append(session.id)

        return session

    def complete_review(
        self,
        session_id: str,
        decision: str,
        notes: str = "",
    ) -> ReviewSession | None:
        """Complete a review session."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        session.decision = decision
        session.notes = notes
        session.completed_at = datetime.now(timezone.utc)

        # Calculate duration
        if session.started_at and session.completed_at:
            delta = session.completed_at - session.started_at
            session.duration_seconds = delta.total_seconds()

        # Remove from active
        if session.opportunity_id in self._active_sessions:
            del self._active_sessions[session.opportunity_id]

        return session

    def get_session(self, session_id: str) -> ReviewSession | None:
        """Get review session by ID."""
        return self._sessions.get(session_id)

    def get_active_session(self, opportunity_id: str) -> ReviewSession | None:
        """Get active review session for opportunity."""
        return self._active_sessions.get(opportunity_id)

    def get_sessions_for_opportunity(self, opportunity_id: str) -> list[ReviewSession]:
        """Get all review sessions for opportunity."""
        session_ids = self._reviews_by_opportunity.get(opportunity_id, [])
        return [self._sessions[sid] for sid in session_ids if sid in self._sessions]

    def get_all_sessions(self) -> list[ReviewSession]:
        """Get all review sessions."""
        return list(self._sessions.values())

    def get_statistics(self) -> dict[str, Any]:
        """Get review statistics."""
        total = len(self._sessions)
        completed = sum(1 for s in self._sessions.values() if s.decision)
        active = len(self._active_sessions)

        decisions = {}
        for session in self._sessions.values():
            if session.decision:
                decisions[session.decision] = decisions.get(session.decision, 0) + 1

        avg_duration = 0
        durations = [s.duration_seconds for s in self._sessions.values() if s.duration_seconds]
        if durations:
            avg_duration = sum(durations) / len(durations)

        return {
            "total_sessions": total,
            "completed": completed,
            "active": active,
            "decisions": decisions,
            "avg_duration_seconds": round(avg_duration, 2),
        }
