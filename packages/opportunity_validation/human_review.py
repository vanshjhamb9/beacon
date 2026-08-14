"""Human review engine — adds reviewer decisions to validation pipeline.

Adds reviewer decision: Approve, Reject, Archive, Spam, Duplicate, Competitor, Future Opportunity, Watchlist.

Reviewer feedback becomes analytics only.
Never modifies deterministic rules.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .v1_schemas import ReviewDecision


class HumanReviewEngine:
    """Adds human review decisions to validation pipeline."""

    def __init__(self):
        self._reviews: dict[str, dict[str, Any]] = {}
        self._review_stats: dict[str, Any] = {
            "total_reviews": 0,
            "by_decision": {},
            "by_reviewer": {},
        }

    def add_review(
        self,
        opportunity_id: str,
        decision: str,
        reviewer: str,
        reasons: list[str],
        feedback: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add human review to opportunity."""
        review = {
            "review_id": str(uuid4()),
            "opportunity_id": opportunity_id,
            "decision": decision,
            "reviewer": reviewer,
            "reasons": reasons,
            "feedback": feedback or "",
            "metadata": metadata or {},
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }

        self._reviews[opportunity_id] = review

        # Update stats
        self._review_stats["total_reviews"] += 1
        decision_count = self._review_stats["by_decision"].get(decision, 0)
        self._review_stats["by_decision"][decision] = decision_count + 1

        reviewer_count = self._review_stats["by_reviewer"].get(reviewer, 0)
        self._review_stats["by_reviewer"][reviewer] = reviewer_count + 1

        return review

    def get_review(self, opportunity_id: str) -> dict[str, Any] | None:
        """Get review for opportunity."""
        return self._reviews.get(opportunity_id)

    def get_reviews_by_decision(self, decision: str) -> list[dict[str, Any]]:
        """Get all reviews with specific decision."""
        return [
            review for review in self._reviews.values()
            if review.get("decision") == decision
        ]

    def get_reviews_by_reviewer(self, reviewer: str) -> list[dict[str, Any]]:
        """Get all reviews by specific reviewer."""
        return [
            review for review in self._reviews.values()
            if review.get("reviewer") == reviewer
        ]

    def get_statistics(self) -> dict[str, Any]:
        """Get review statistics."""
        return dict(self._review_stats)

    def approve(
        self,
        opportunity_id: str,
        reviewer: str,
        reasons: list[str],
        feedback: str | None = None,
    ) -> dict[str, Any]:
        """Approve opportunity."""
        return self.add_review(
            opportunity_id=opportunity_id,
            decision=ReviewDecision.APPROVE.value,
            reviewer=reviewer,
            reasons=reasons,
            feedback=feedback,
        )

    def reject(
        self,
        opportunity_id: str,
        reviewer: str,
        reasons: list[str],
        feedback: str | None = None,
    ) -> dict[str, Any]:
        """Reject opportunity."""
        return self.add_review(
            opportunity_id=opportunity_id,
            decision=ReviewDecision.REJECT.value,
            reviewer=reviewer,
            reasons=reasons,
            feedback=feedback,
        )

    def archive(
        self,
        opportunity_id: str,
        reviewer: str,
        reasons: list[str],
        feedback: str | None = None,
    ) -> dict[str, Any]:
        """Archive opportunity."""
        return self.add_review(
            opportunity_id=opportunity_id,
            decision=ReviewDecision.ARCHIVE.value,
            reviewer=reviewer,
            reasons=reasons,
            feedback=feedback,
        )

    def mark_spam(
        self,
        opportunity_id: str,
        reviewer: str,
        reasons: list[str],
        feedback: str | None = None,
    ) -> dict[str, Any]:
        """Mark opportunity as spam."""
        return self.add_review(
            opportunity_id=opportunity_id,
            decision=ReviewDecision.SPAM.value,
            reviewer=reviewer,
            reasons=reasons,
            feedback=feedback,
        )

    def mark_duplicate(
        self,
        opportunity_id: str,
        reviewer: str,
        reasons: list[str],
        feedback: str | None = None,
    ) -> dict[str, Any]:
        """Mark opportunity as duplicate."""
        return self.add_review(
            opportunity_id=opportunity_id,
            decision=ReviewDecision.DUPLICATE.value,
            reviewer=reviewer,
            reasons=reasons,
            feedback=feedback,
        )

    def mark_competitor(
        self,
        opportunity_id: str,
        reviewer: str,
        reasons: list[str],
        feedback: str | None = None,
    ) -> dict[str, Any]:
        """Mark opportunity as competitor."""
        return self.add_review(
            opportunity_id=opportunity_id,
            decision=ReviewDecision.COMPETITOR.value,
            reviewer=reviewer,
            reasons=reasons,
            feedback=feedback,
        )

    def mark_future_opportunity(
        self,
        opportunity_id: str,
        reviewer: str,
        reasons: list[str],
        feedback: str | None = None,
    ) -> dict[str, Any]:
        """Mark opportunity as future opportunity."""
        return self.add_review(
            opportunity_id=opportunity_id,
            decision=ReviewDecision.FUTURE_OPPORTUNITY.value,
            reviewer=reviewer,
            reasons=reasons,
            feedback=feedback,
        )

    def add_to_watchlist(
        self,
        opportunity_id: str,
        reviewer: str,
        reasons: list[str],
        feedback: str | None = None,
    ) -> dict[str, Any]:
        """Add opportunity to watchlist."""
        return self.add_review(
            opportunity_id=opportunity_id,
            decision=ReviewDecision.WATCHLIST.value,
            reviewer=reviewer,
            reasons=reasons,
            feedback=feedback,
        )

    def clear(self):
        """Clear all reviews (for testing)."""
        self._reviews.clear()
        self._review_stats = {
            "total_reviews": 0,
            "by_decision": {},
            "by_reviewer": {},
        }
