from __future__ import annotations

from decision_discovery.models.types import (
    ContactChannel,
    DecisionMakerCandidate,
    DepartmentEntry,
    DiscoveryConfidence,
    LeadershipEntry,
)


class DiscoveryConfidenceEngine:
    def score(
        self,
        *,
        makers: list[DecisionMakerCandidate],
        leadership: list[LeadershipEntry],
        departments: list[DepartmentEntry],
        channels: list[ContactChannel],
        buyer_match_confidence: float,
    ) -> DiscoveryConfidence:
        leadership_confidence = 0.0
        if leadership:
            leadership_confidence = min(
                100.0,
                sum(item.confidence for item in leadership) / len(leadership),
            )

        department_confidence = 0.0
        if departments:
            department_confidence = min(
                100.0,
                sum(item.signal_strength for item in departments) / len(departments),
            )

        contact_confidence = 0.0
        if channels:
            contact_confidence = min(
                100.0,
                sum(item.confidence for item in channels) / len(channels),
            )
            if any("@" in item.value for item in channels):
                contact_confidence = min(100.0, contact_confidence + 8.0)

        named_makers = [item for item in makers if item.name]
        maker_boost = min(15.0, len(named_makers) * 5.0)
        overall = round(
            (
                leadership_confidence * 0.25
                + department_confidence * 0.15
                + contact_confidence * 0.25
                + buyer_match_confidence * 0.25
                + maker_boost * 0.10
            ),
            4,
        )
        return DiscoveryConfidence(
            leadership_confidence=round(leadership_confidence, 4),
            department_confidence=round(department_confidence, 4),
            contact_confidence=round(contact_confidence, 4),
            buyer_match_confidence=round(buyer_match_confidence, 4),
            overall_discovery_score=min(100.0, overall),
        )
