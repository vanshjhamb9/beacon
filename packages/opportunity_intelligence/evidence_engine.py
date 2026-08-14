"""Evidence validation and scoring for opportunities."""

from __future__ import annotations

from collections.abc import Iterable

from opportunity_intelligence.constants import MINIMUM_EVIDENCE
from opportunity_intelligence.schemas import EvidenceInput


class EvidenceEngine:
    def deduplicate(self, evidence: Iterable[EvidenceInput]) -> tuple[EvidenceInput, ...]:
        seen: set[tuple[str, str, str]] = set()
        unique: list[EvidenceInput] = []
        for item in evidence:
            key = (
                item.provider.strip().lower(),
                str(item.url or "").strip().lower(),
                item.title.strip().lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return tuple(unique)

    def validate(self, evidence: Iterable[EvidenceInput], *, minimum: int = MINIMUM_EVIDENCE) -> tuple[EvidenceInput, ...]:
        unique = self.deduplicate(evidence)
        if len(unique) < minimum:
            raise ValueError(f"Opportunity rejected: at least {minimum} evidence records are required.")
        return unique

    def score(self, evidence: Iterable[EvidenceInput]) -> float:
        rows = tuple(evidence)
        if not rows:
            return 0.0
        average_confidence = sum(item.confidence for item in rows) / len(rows)
        average_trust = sum(item.trust for item in rows) / len(rows)
        diversity_bonus = min(len({item.provider.lower() for item in rows}) * 4.0, 16.0)
        return min((average_confidence * 0.45) + (average_trust * 0.45) + diversity_bonus, 100.0)

    def trust(self, evidence: Iterable[EvidenceInput]) -> float:
        rows = tuple(evidence)
        if not rows:
            return 0.0
        return min(sum(item.trust for item in rows) / len(rows), 100.0)
