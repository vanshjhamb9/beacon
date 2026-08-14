"""DQE v2 Quality Score Engine — deterministic weighted scoring (0-100)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from discovery_quality_engine.v2_schemas import (
    DEFAULT_SCORE_WEIGHTS,
    FreshnessStatus,
    QualityEvidence,
    QualityScore,
    ScoreComponent,
    ScoreWeight,
)


class QualityScoreEngine:
    """Calculates deterministic quality score with configurable weights."""

    def __init__(
        self,
        weights: list[ScoreWeight] | None = None,
    ) -> None:
        self._weights = weights or DEFAULT_SCORE_WEIGHTS
        self._validate_weights()

    def _validate_weights(self) -> None:
        total = sum(w.weight for w in self._weights)
        if total != 100:
            raise ValueError(f"Weights must sum to 100, got {total}")
        names = [w.name for w in self._weights]
        if len(names) != len(set(names)):
            raise ValueError("Weight names must be unique")

    @property
    def weights(self) -> list[ScoreWeight]:
        return list(self._weights)

    def calculate(
        self,
        *,
        evidence: QualityEvidence,
        freshness_raw_score: float = 0.0,
        buying_signal_raw_score: float = 0.0,
        source_trust_raw_score: float = 0.0,
        website_quality_raw_score: float = 0.0,
        company_validation_raw_score: float = 0.0,
        icp_match_raw_score: float = 0.0,
        region_raw_score: float = 0.0,
        industry_raw_score: float = 0.0,
        custom_scores: dict[str, float] | None = None,
        now: datetime | None = None,
    ) -> QualityScore:
        current = now or datetime.now(UTC)
        raw_scores = {
            "freshness": freshness_raw_score,
            "buying_signal": buying_signal_raw_score,
            "source_trust": source_trust_raw_score,
            "website_quality": website_quality_raw_score,
            "company_validation": company_validation_raw_score,
            "icp_match": icp_match_raw_score,
            "region": region_raw_score,
            "industry": industry_raw_score,
        }
        if custom_scores:
            raw_scores.update(custom_scores)

        components: list[ScoreComponent] = []
        for weight in self._weights:
            raw = raw_scores.get(weight.name, 0.0)
            raw_clamped = max(0.0, min(100.0, raw))
            weighted = raw_clamped * weight.weight / 100.0
            evidence_list = self._collect_evidence(weight.name, evidence)
            components.append(
                ScoreComponent(
                    name=weight.name,
                    raw_score=raw_clamped,
                    weighted_score=round(weighted, 2),
                    weight=weight.weight,
                    evidence=evidence_list,
                )
            )

        total = sum(c.weighted_score for c in components)
        total_int = max(0, min(100, round(total)))

        return QualityScore(
            total_score=total_int,
            components=components,
            calculated_at=current,
            metadata={"weights_version": "v2.0"},
        )

    def _collect_evidence(self, component_name: str, evidence: QualityEvidence) -> list[str]:
        ev: list[str] = []
        if component_name == "freshness":
            if evidence.signal_freshness_days is not None:
                ev.append(f"Signal age: {evidence.signal_freshness_days} days")
            if evidence.signal_freshness_status:
                ev.append(f"Freshness status: {evidence.signal_freshness_status.value}")
        elif component_name == "buying_signal":
            if evidence.buying_signals_detected:
                ev.append(f"Signals detected: {', '.join(evidence.buying_signals_detected)}")
            if evidence.buying_signal_verdict:
                ev.append(f"Verdict: {evidence.buying_signal_verdict.value}")
        elif component_name == "source_trust":
            if evidence.source_trust_level:
                ev.append(f"Source trust: {evidence.source_trust_level}")
        elif component_name == "website_quality":
            ev.append(f"Website score: {evidence.website_score}")
        elif component_name == "company_validation":
            if evidence.company_age_days is not None:
                ev.append(f"Company age: {evidence.company_age_days} days")
            if evidence.duplicate_flag:
                ev.append("Duplicate detected")
        elif component_name == "icp_match":
            ev.append(f"ICP match: {evidence.icp_match_score}")
        elif component_name == "region":
            ev.append(f"Region match: {evidence.region_match}")
        elif component_name == "industry":
            ev.append(f"Industry match: {evidence.industry_match}")
        return ev

    def calculate_freshness_score(
        self,
        *,
        status: FreshnessStatus,
        signal_age_days: int,
        accepted_threshold_days: int = 90,
        borderline_threshold_days: int = 180,
    ) -> float:
        """Calculate freshness raw score based on v2 status."""
        if status == FreshnessStatus.ACCEPTED:
            if signal_age_days <= accepted_threshold_days // 2:
                return 100.0
            elif signal_age_days <= accepted_threshold_days:
                ratio = 1.0 - (signal_age_days - accepted_threshold_days // 2) / (accepted_threshold_days // 2)
                return 50.0 + 50.0 * max(0.0, ratio)
            return 50.0
        elif status == FreshnessStatus.BORDERLINE:
            if signal_age_days <= borderline_threshold_days:
                ratio = 1.0 - (signal_age_days - accepted_threshold_days) / (borderline_threshold_days - accepted_threshold_days)
                return 25.0 + 25.0 * max(0.0, ratio)
            return 25.0
        else:
            return 0.0

    def calculate_buying_signal_score(
        self,
        *,
        valid_count: int,
        not_valid_count: int,
        borderline_count: int,
    ) -> float:
        """Calculate buying signal raw score based on v2 verdicts."""
        total = valid_count + not_valid_count + borderline_count
        if total == 0:
            return 0.0
        valid_ratio = valid_count / total
        borderline_ratio = borderline_count / total
        score = (valid_ratio * 100.0) + (borderline_ratio * 50.0)
        return min(100.0, max(0.0, score))
