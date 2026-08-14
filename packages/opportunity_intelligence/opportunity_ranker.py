"""Deterministic opportunity ranking."""

from __future__ import annotations

from collections.abc import Iterable

from opportunity_intelligence.models import Opportunity


class OpportunityRanker:
    def rank(self, opportunities: Iterable[Opportunity]) -> list[Opportunity]:
        return sorted(
            opportunities,
            key=lambda item: (
                item.opportunity_score,
                item.confidence,
                item.freshness_score,
                len(item.evidence),
                item.icp_score,
            ),
            reverse=True,
        )
