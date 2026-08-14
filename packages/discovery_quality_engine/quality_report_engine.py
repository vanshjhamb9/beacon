"""DQE v2 Quality Report Engine — generates complete QualityReport per company."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from discovery_quality_engine.quality_grade_engine import QualityGradeEngine
from discovery_quality_engine.quality_score_engine import QualityScoreEngine
from discovery_quality_engine.v2_schemas import (
    AuditEntry,
    QualityEvidence,
    QualityGrade,
    QualityReport,
    QualityScore,
    ScoreWeight,
)


class QualityReportEngine:
    """Generates complete QualityReport with score, grade, evidence, and audit trail."""

    def __init__(
        self,
        score_engine: QualityScoreEngine | None = None,
        grade_engine: QualityGradeEngine | None = None,
    ) -> None:
        self._score_engine = score_engine or QualityScoreEngine()
        self._grade_engine = grade_engine or QualityGradeEngine()

    @property
    def score_engine(self) -> QualityScoreEngine:
        return self._score_engine

    @property
    def grade_engine(self) -> QualityGradeEngine:
        return self._grade_engine

    def generate(
        self,
        *,
        company_id: UUID,
        company_name: str,
        evidence: QualityEvidence,
        gates_passed: list[str],
        gates_failed: list[str],
        rejection_reasons: list[str],
        freshness_raw_score: float = 0.0,
        buying_signal_raw_score: float = 0.0,
        source_trust_raw_score: float = 0.0,
        website_quality_raw_score: float = 0.0,
        company_validation_raw_score: float = 0.0,
        icp_match_raw_score: float = 0.0,
        region_raw_score: float = 0.0,
        industry_raw_score: float = 0.0,
        custom_scores: dict[str, float] | None = None,
        audit_entries: list[AuditEntry] | None = None,
        now: datetime | None = None,
    ) -> QualityReport:
        current = now or datetime.now(UTC)

        quality_score = self._score_engine.calculate(
            evidence=evidence,
            freshness_raw_score=freshness_raw_score,
            buying_signal_raw_score=buying_signal_raw_score,
            source_trust_raw_score=source_trust_raw_score,
            website_quality_raw_score=website_quality_raw_score,
            company_validation_raw_score=company_validation_raw_score,
            icp_match_raw_score=icp_match_raw_score,
            region_raw_score=region_raw_score,
            industry_raw_score=industry_raw_score,
            custom_scores=custom_scores,
            now=current,
        )

        quality_grade, decision = self._grade_engine.get_decision(quality_score)

        reasons = list(rejection_reasons)
        if decision == "REJECT" and not reasons:
            reasons.append(f"Quality score {quality_score.total_score} below threshold")

        all_audit = list(audit_entries or [])
        if not all_audit:
            all_audit = self._build_default_audit(
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                decision=decision,
                now=current,
            )

        return QualityReport(
            company_id=company_id,
            company_name=company_name,
            quality_score=quality_score,
            quality_grade=quality_grade,
            decision=decision,
            reasons=reasons,
            evidence=evidence,
            audit_trail=all_audit,
            gates_passed=list(gates_passed),
            gates_failed=list(gates_failed),
            rejection_reasons=list(rejection_reasons),
            created_at=current,
        )

    def _build_default_audit(
        self,
        *,
        gates_passed: list[str],
        gates_failed: list[str],
        decision: str,
        now: datetime,
    ) -> list[AuditEntry]:
        entries: list[AuditEntry] = []
        for gate in gates_passed:
            entries.append(
                AuditEntry(
                    gate=gate,
                    decision="PASS",
                    timestamp=now,
                )
            )
        for gate in gates_failed:
            entries.append(
                AuditEntry(
                    gate=gate,
                    decision="FAIL",
                    timestamp=now,
                )
            )
        entries.append(
            AuditEntry(
                gate="FINAL_DECISION",
                decision=decision,
                timestamp=now,
            )
        )
        return entries

    def generate_rejection_report(
        self,
        *,
        company_id: UUID,
        company_name: str,
        rejection_reasons: list[str],
        gates_failed: list[str],
        now: datetime | None = None,
    ) -> QualityReport:
        """Generate a report for immediately rejected companies (no scoring)."""
        current = now or datetime.now(UTC)
        evidence = QualityEvidence()
        return QualityReport(
            company_id=company_id,
            company_name=company_name,
            quality_score=None,
            quality_grade=QualityGrade.REJECT,
            decision="REJECT",
            reasons=list(rejection_reasons),
            evidence=evidence,
            audit_trail=[
                AuditEntry(
                    gate="IMMEDIATE_REJECTION",
                    decision="REJECT",
                    timestamp=current,
                    reasons=list(rejection_reasons),
                )
            ],
            gates_passed=[],
            gates_failed=list(gates_failed),
            rejection_reasons=list(rejection_reasons),
            created_at=current,
        )
