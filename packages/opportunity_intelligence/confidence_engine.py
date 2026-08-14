"""Reliability scoring independent from opportunity score."""

from __future__ import annotations

from collections.abc import Iterable

from opportunity_intelligence.schemas import EvidenceInput


class ConfidenceEngine:
    def calculate(self, evidence: Iterable[EvidenceInput]) -> float:
        rows = tuple(evidence)
        if not rows:
            return 0.0
        provider_count = len({row.provider.lower() for row in rows})
        base = min(35.0 + (provider_count * 11.0) + (len(rows) * 6.0), 92.0)
        quality = (sum(row.confidence for row in rows) / len(rows)) * 0.06
        trust = (sum(row.trust for row in rows) / len(rows)) * 0.04
        return min(round(base + quality + trust, 2), 100.0)
