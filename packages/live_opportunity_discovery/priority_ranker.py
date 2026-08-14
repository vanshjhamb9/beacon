"""Weighted live opportunity priority ranking."""

from __future__ import annotations

from dataclasses import dataclass


RANKING_WEIGHTS: dict[str, float] = {
    "buying_intent": 0.20,
    "freshness": 0.16,
    "company_size": 0.10,
    "funding": 0.10,
    "evidence_count": 0.10,
    "source_quality": 0.10,
    "decision_maker": 0.08,
    "revenue_potential": 0.08,
    "competition": 0.04,
    "service_match": 0.04,
}


@dataclass(frozen=True, slots=True)
class PriorityInput:
    buying_intent: float
    freshness: float
    company_size: float = 50.0
    funding: float = 0.0
    evidence_count: float = 0.0
    source_quality: float = 50.0
    decision_maker: float = 0.0
    revenue_potential: float = 50.0
    competition: float = 50.0
    service_match: float = 0.0


@dataclass(frozen=True, slots=True)
class PriorityScore:
    score: float
    priority: str
    breakdown: dict[str, float]
    reasons: tuple[str, ...]


class PriorityRanker:
    def score(self, factors: PriorityInput) -> PriorityScore:
        raw = {
            "buying_intent": factors.buying_intent,
            "freshness": factors.freshness,
            "company_size": min(factors.company_size, 100.0),
            "funding": min(factors.funding, 100.0),
            "evidence_count": min(factors.evidence_count * 18.0, 100.0),
            "source_quality": factors.source_quality,
            "decision_maker": factors.decision_maker,
            "revenue_potential": factors.revenue_potential,
            "competition": max(100.0 - factors.competition, 0.0),
            "service_match": factors.service_match,
        }
        breakdown = {key: round(raw[key] * RANKING_WEIGHTS[key], 2) for key in RANKING_WEIGHTS}
        final = round(sum(breakdown.values()), 2)
        if final >= 85:
            priority = "P0"
        elif final >= 70:
            priority = "P1"
        elif final >= 55:
            priority = "P2"
        else:
            priority = "P3"
        reasons = tuple(
            f"{key.replace('_', ' ').title()} contributed {points} weighted points."
            for key, points in breakdown.items()
        )
        return PriorityScore(score=final, priority=priority, breakdown=breakdown, reasons=reasons)

    def rank(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return sorted(
            rows,
            key=lambda row: (
                float(row.get("buying_score") or row.get("priority_score") or 0),
                float(row.get("freshness_score") or 0),
                int(row.get("evidence_count") or 0),
            ),
            reverse=True,
        )
