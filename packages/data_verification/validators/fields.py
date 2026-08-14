from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from data_verification.freshness.engine import FreshnessEngine
from data_verification.models.types import (
    FieldObservation,
    FieldVerificationResult,
    FreshnessStatus,
    VerificationStatus,
)
from data_verification.trust.engine import TrustEngine


def _normalize_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "|".join(sorted(str(item).strip().lower() for item in value))
    return str(value).strip().lower()


class FieldVerificationEngine:
    def __init__(
        self,
        *,
        freshness: FreshnessEngine | None = None,
        trust: TrustEngine | None = None,
    ) -> None:
        self.freshness = freshness or FreshnessEngine()
        self.trust = trust or TrustEngine()

    def verify(
        self,
        observations: list[FieldObservation],
        *,
        verified_at: datetime | None = None,
    ) -> list[FieldVerificationResult]:
        when = verified_at or datetime.now(UTC)
        by_field: dict[str, list[FieldObservation]] = defaultdict(list)
        for observation in observations:
            by_field[observation.field_name].append(observation)

        results: list[FieldVerificationResult] = []
        for field_name, values in sorted(by_field.items()):
            grouped: dict[str, list[FieldObservation]] = defaultdict(list)
            for observation in values:
                grouped[_normalize_value(observation.value)].append(observation)

            ranked = sorted(
                grouped.items(),
                key=lambda item: (
                    len(item[1]),
                    max(self.trust.score_source(obs.source) for obs in item[1]),
                    max(obs.confidence for obs in item[1]),
                ),
                reverse=True,
            )

            for index, (_normalized, group) in enumerate(ranked):
                primary = max(
                    group,
                    key=lambda obs: (self.trust.score_source(obs.source), obs.confidence),
                )
                confirming = sorted(
                    {
                        obs.source
                        for obs in group
                        if obs.source != primary.source
                    }
                )
                conflicting = sorted(
                    {
                        obs.source
                        for other_key, other_group in ranked
                        if other_key != _normalized
                        for obs in other_group
                        if obs.source != primary.source
                    }
                )
                freshness_score, freshness_status, _age = self.freshness.evaluate(primary.collected_at, now=when)
                trust_score = self.trust.score_field(
                    source=primary.source,
                    confidence=primary.confidence,
                    confirmed_by=confirming,
                    conflicting_sources=conflicting,
                )
                status = self._status(
                    value=primary.value,
                    freshness_status=freshness_status,
                    confirming=confirming,
                    conflicting=conflicting,
                    trust_score=trust_score,
                )
                explanation = None
                if conflicting:
                    explanation = (
                        f"Canonical value chosen from {primary.source} due to higher trust/confidence; "
                        f"conflicting values retained from {', '.join(conflicting)}."
                    )
                elif confirming:
                    explanation = f"Value confirmed by {', '.join(confirming)}."

                results.append(
                    FieldVerificationResult(
                        field_name=field_name,
                        value=primary.value,
                        source=primary.source,
                        source_url=primary.source_url,
                        connector=primary.connector or primary.source,
                        verified_at=when,
                        confidence=primary.confidence,
                        freshness_score=freshness_score,
                        freshness_status=freshness_status,
                        trust_score=trust_score,
                        verification_status=status,
                        confirmed_by=confirming,
                        conflicting_sources=conflicting,
                        is_canonical=index == 0,
                        conflict_explanation=explanation,
                        category=self._category(field_name),
                    )
                )
        return results

    def _status(
        self,
        *,
        value: Any,
        freshness_status: FreshnessStatus,
        confirming: list[str],
        conflicting: list[str],
        trust_score: float,
    ) -> VerificationStatus:
        if value in (None, "", [], {}):
            return VerificationStatus.MISSING
        if conflicting:
            return VerificationStatus.CONFLICTING
        if freshness_status == FreshnessStatus.EXPIRED or trust_score < 40.0:
            return VerificationStatus.FLAGGED
        if confirming and trust_score >= 70.0:
            return VerificationStatus.VERIFIED
        if trust_score >= 55.0:
            return VerificationStatus.PARTIAL
        return VerificationStatus.UNVERIFIED

    def _category(self, field_name: str) -> str:
        if field_name.startswith("contact."):
            return "contacts"
        if field_name.startswith("person.") or field_name.startswith("leadership."):
            return "leadership"
        if field_name.startswith("tech."):
            return "technology"
        if field_name.startswith("social."):
            return "social"
        if field_name.startswith("hiring.") or field_name.startswith("job."):
            return "hiring"
        if field_name.startswith("revenue.") or field_name in {
            "recommended_service",
            "business_pain",
            "buyer_persona",
            "estimated_budget",
            "priority",
        }:
            return "revenue"
        if field_name.startswith("evidence."):
            return "evidence"
        return "company_profile"
