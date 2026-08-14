"""Lead Quality Scorer — integrates DQE v2 with lead intelligence for improved lead quality."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from discovery_quality_engine.buying_signal_engine_v2 import BuyingSignalEngineV2
from discovery_quality_engine.freshness_engine_v2 import FreshnessEngineV2, FreshnessStatus
from discovery_quality_engine.quality_grade_engine import QualityGradeEngine
from discovery_quality_engine.quality_score_engine import QualityScoreEngine
from discovery_quality_engine.v2_schemas import (
    FreshnessStatus,
    QualityEvidence,
    QualityGrade,
    QualityScore,
    ScoreWeight,
)


class LeadQualityScorer:
    """Scores lead quality by combining DQE v2 with lead-specific signals."""

    def __init__(self) -> None:
        self._freshness_engine = FreshnessEngineV2()
        self._buying_signal_engine = BuyingSignalEngineV2()
        self._score_engine = QualityScoreEngine()
        self._grade_engine = QualityGradeEngine()

    def score_lead(
        self,
        *,
        company_id: str,
        company_name: str,
        website: str | None = None,
        industry: str | None = None,
        country: str | None = None,
        signal_type: str = "",
        signal_source: str = "",
        signal_timestamp: datetime | None = None,
        signal_types: list[str] | None = None,
        has_email: bool = False,
        has_decision_maker: bool = False,
        has_website: bool = False,
        confidence: float = 0.0,
        trust: float = 0.0,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)

        freshness_status = FreshnessStatus.ACCEPTED
        signal_age_days = 0
        if signal_timestamp:
            freshness_eval = self._freshness_engine.evaluate(
                signal_timestamp=signal_timestamp, now=current
            )
            freshness_status = freshness_eval.status
            signal_age_days = freshness_eval.signal_age_days

        effective_signal_types = signal_types or ([signal_type] if signal_type else [])
        bs_eval = self._buying_signal_engine.evaluate(signal_types=effective_signal_types)

        evidence = QualityEvidence(
            signal_freshness_days=signal_age_days,
            signal_freshness_status=freshness_status,
            buying_signals_detected=bs_eval.valid_signals + bs_eval.not_valid_signals,
            buying_signal_verdict=bs_eval.verdict,
            source_trust_level=signal_source,
            website_score=100.0 if has_website else 0.0,
            company_age_days=None,
            icp_match_score=50.0,
            region_match=country is not None,
            industry_match=industry is not None,
        )

        freshness_raw = self._score_engine.calculate_freshness_score(
            status=freshness_status,
            signal_age_days=signal_age_days,
        )

        buying_signal_raw = self._score_engine.calculate_buying_signal_score(
            valid_count=len(bs_eval.valid_signals),
            not_valid_count=len(bs_eval.not_valid_signals),
            borderline_count=len(bs_eval.borderline_signals),
        )

        source_trust_raw = 100.0 if signal_source else 0.0
        website_quality_raw = 100.0 if has_website else 0.0
        company_validation_raw = 100.0
        if has_email:
            company_validation_raw += 10
        if has_decision_maker:
            company_validation_raw += 10
        company_validation_raw = min(100.0, company_validation_raw)

        icp_match_raw = 50.0
        if industry:
            icp_match_raw += 25.0
        if country:
            icp_match_raw += 25.0
        icp_match_raw = min(100.0, icp_match_raw)

        region_raw = 100.0 if country else 0.0
        industry_raw = 100.0 if industry else 0.0

        quality_score = self._score_engine.calculate(
            evidence=evidence,
            freshness_raw_score=freshness_raw,
            buying_signal_raw_score=buying_signal_raw,
            source_trust_raw_score=source_trust_raw,
            website_quality_raw_score=website_quality_raw,
            company_validation_raw_score=company_validation_raw,
            icp_match_raw_score=icp_match_raw,
            region_raw_score=region_raw,
            industry_raw_score=industry_raw,
        )

        quality_grade, decision = self._grade_engine.get_decision(quality_score)

        lead_quality_multiplier = 1.0
        if has_email:
            lead_quality_multiplier *= 1.1
        if has_decision_maker:
            lead_quality_multiplier *= 1.1
        if confidence > 80:
            lead_quality_multiplier *= 1.05
        if trust > 80:
            lead_quality_multiplier *= 1.05

        adjusted_score = min(100, round(quality_score.total_score * lead_quality_multiplier))

        return {
            "company_id": company_id,
            "company_name": company_name,
            "quality_score": adjusted_score,
            "quality_grade": quality_grade.value,
            "decision": decision,
            "freshness_status": freshness_status.value,
            "signal_age_days": signal_age_days,
            "buying_signal_verdict": bs_eval.verdict.value,
            "valid_signals": bs_eval.valid_signals,
            "not_valid_signals": bs_eval.not_valid_signals,
            "borderline_signals": bs_eval.borderline_signals,
            "has_email": has_email,
            "has_decision_maker": has_decision_maker,
            "has_website": has_website,
            "confidence": confidence,
            "trust": trust,
            "components": [
                {
                    "name": c.name,
                    "raw_score": c.raw_score,
                    "weighted_score": c.weighted_score,
                    "weight": c.weight,
                }
                for c in quality_score.components
            ],
            "calculated_at": current.isoformat(),
        }

    def prioritize_leads(
        self,
        leads: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Sort leads by quality score descending."""
        return sorted(leads, key=lambda x: x.get("quality_score", 0), reverse=True)

    def filter_by_grade(
        self,
        leads: list[dict[str, Any]],
        min_grade: str = "B",
    ) -> list[dict[str, Any]]:
        """Filter leads by minimum quality grade."""
        grade_order = {"A+": 0, "A": 1, "B": 2, "C": 3, "Reject": 4}
        min_order = grade_order.get(min_grade, 4)
        return [
            lead
            for lead in leads
            if grade_order.get(lead.get("quality_grade", "Reject"), 4) <= min_order
        ]

    def get_quality_summary(
        self,
        leads: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Get summary statistics for a batch of leads."""
        if not leads:
            return {
                "total": 0,
                "average_score": 0,
                "grade_distribution": {},
                "acceptance_rate": 0,
            }

        scores = [lead.get("quality_score", 0) for lead in leads]
        grades = [lead.get("quality_grade", "Reject") for lead in leads]

        grade_counts: dict[str, int] = {}
        for grade in grades:
            grade_counts[grade] = grade_counts.get(grade, 0) + 1

        accepted = sum(1 for lead in leads if lead.get("decision") == "ACCEPT")

        return {
            "total": len(leads),
            "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "grade_distribution": grade_counts,
            "acceptance_rate": round(accepted / len(leads) * 100, 2) if leads else 0,
        }
