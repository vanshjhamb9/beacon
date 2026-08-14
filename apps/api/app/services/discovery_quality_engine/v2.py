"""Discovery Quality Engine v2 service layer — scoring, grading, and reports."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from discovery_quality_engine.buying_signal_engine_v2 import BuyingSignalEngineV2
from discovery_quality_engine.freshness_engine_v2 import FreshnessEngineV2
from discovery_quality_engine.quality_dashboard import QualityDashboard
from discovery_quality_engine.quality_grade_engine import QualityGradeEngine
from discovery_quality_engine.quality_metrics import QualityMetricsCollector
from discovery_quality_engine.quality_report_engine import QualityReportEngine
from discovery_quality_engine.quality_score_engine import QualityScoreEngine
from discovery_quality_engine.v2_schemas import (
    QualityEvidence,
    QualityGrade,
    QualityReport,
)


class DiscoveryQualityServiceV2:
    def __init__(self) -> None:
        self._dashboard = QualityDashboard()
        self._metrics = QualityMetricsCollector()
        self._freshness_v2 = FreshnessEngineV2()
        self._buying_signal_v2 = BuyingSignalEngineV2()
        self._score_engine = QualityScoreEngine()
        self._grade_engine = QualityGradeEngine()
        self._report_engine = QualityReportEngine(
            score_engine=self._score_engine,
            grade_engine=self._grade_engine,
        )
        self._reports: dict[str, QualityReport] = {}

    async def evaluate_v2(
        self,
        *,
        company_id: str,
        company_name: str,
        website: str | None = None,
        industry: str | None = None,
        country: str | None = None,
        signal_type: str = "",
        signal_source: str = "",
        signal_title: str = "",
        signal_timestamp: str | None = None,
        signal_types: str | None = None,
        domain: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)

        freshness_status = None
        signal_age_days = None
        if signal_timestamp:
            ts = datetime.fromisoformat(signal_timestamp.replace("Z", "+00:00"))
            freshness_eval = self._freshness_v2.evaluate(signal_timestamp=ts, now=now)
            freshness_status = freshness_eval.status
            signal_age_days = freshness_eval.signal_age_days

        effective_signal_types = []
        if signal_types:
            effective_signal_types = [s.strip() for s in signal_types.split(",")]
        elif signal_type:
            effective_signal_types = [signal_type]

        bs_eval = self._buying_signal_v2.evaluate(signal_types=effective_signal_types)

        evidence = QualityEvidence(
            signal_freshness_days=signal_age_days,
            signal_freshness_status=freshness_status,
            buying_signals_detected=bs_eval.valid_signals + bs_eval.not_valid_signals,
            buying_signal_verdict=bs_eval.verdict,
            source_trust_level=signal_source,
            website_score=100.0 if website else 0.0,
            company_age_days=None,
            icp_match_score=50.0,
            region_match=country is not None,
            industry_match=industry is not None,
        )

        freshness_raw = self._score_engine.calculate_freshness_score(
            status=freshness_status or freshness_status,
            signal_age_days=signal_age_days or 0,
        )
        buying_signal_raw = self._score_engine.calculate_buying_signal_score(
            valid_count=len(bs_eval.valid_signals),
            not_valid_count=len(bs_eval.not_valid_signals),
            borderline_count=len(bs_eval.borderline_signals),
        )

        report = self._report_engine.generate(
            company_id=UUID(company_id),
            company_name=company_name,
            evidence=evidence,
            gates_passed=[],
            gates_failed=[],
            rejection_reasons=[],
            freshness_raw_score=freshness_raw,
            buying_signal_raw_score=buying_signal_raw,
            source_trust_raw_score=100.0 if signal_source else 0.0,
            website_quality_raw_score=100.0 if website else 0.0,
            company_validation_raw_score=100.0,
            icp_match_raw_score=50.0,
            region_raw_score=100.0 if country else 0.0,
            industry_raw_score=100.0 if industry else 0.0,
            now=now,
        )

        self._reports[company_id] = report

        return {
            "company_id": company_id,
            "company_name": company_name,
            "quality_score": report.quality_score.total_score if report.quality_score else 0,
            "quality_grade": report.quality_grade.value,
            "decision": report.decision,
            "evidence": {
                "freshness_status": freshness_status.value if freshness_status else None,
                "signal_age_days": signal_age_days,
                "buying_signal_verdict": bs_eval.verdict.value,
                "valid_signals": bs_eval.valid_signals,
                "not_valid_signals": bs_eval.not_valid_signals,
                "borderline_signals": bs_eval.borderline_signals,
            },
            "created_at": now.isoformat(),
        }

    async def get_quality_score(self, company_id: str) -> dict[str, Any]:
        report = self._reports.get(company_id)
        if not report or not report.quality_score:
            return {"error": "Score not found", "company_id": company_id}
        score = report.quality_score
        return {
            "company_id": company_id,
            "total_score": score.total_score,
            "components": [
                {
                    "name": c.name,
                    "raw_score": c.raw_score,
                    "weighted_score": c.weighted_score,
                    "weight": c.weight,
                    "evidence": c.evidence,
                }
                for c in score.components
            ],
            "calculated_at": score.calculated_at.isoformat(),
        }

    async def get_quality_grade(self, company_id: str) -> dict[str, Any]:
        report = self._reports.get(company_id)
        if not report:
            return {"error": "Grade not found", "company_id": company_id}
        return {
            "company_id": company_id,
            "quality_grade": report.quality_grade.value,
            "decision": report.decision,
            "quality_score": report.quality_score.total_score if report.quality_score else None,
        }

    async def get_quality_report(self, company_id: str) -> dict[str, Any]:
        report = self._reports.get(company_id)
        if not report:
            return {"error": "Report not found", "company_id": company_id}
        return self._serialize_report(report)

    async def list_quality_reports(
        self,
        *,
        grade: str | None = None,
        decision: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        reports = list(self._reports.values())
        if grade:
            reports = [r for r in reports if r.quality_grade.value == grade]
        if decision:
            reports = [r for r in reports if r.decision == decision]
        reports = sorted(reports, key=lambda r: r.created_at, reverse=True)[:limit]
        return {
            "items": [self._serialize_report(r) for r in reports],
            "count": len(reports),
        }

    async def scores_summary(self) -> dict[str, Any]:
        reports = [r for r in self._reports.values() if r.quality_score]
        if not reports:
            return {"total": 0, "average_score": 0, "min_score": 0, "max_score": 0}
        scores = [r.quality_score.total_score for r in reports if r.quality_score]
        return {
            "total": len(scores),
            "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
        }

    async def grades_summary(self) -> dict[str, Any]:
        grade_counts: dict[str, int] = {}
        for report in self._reports.values():
            grade = report.quality_grade.value
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        return {"grades": grade_counts, "total": len(self._reports)}

    async def freshness_stats_v2(self) -> dict[str, Any]:
        status_counts: dict[str, int] = {}
        for report in self._reports.values():
            if report.evidence.signal_freshness_status:
                status = report.evidence.signal_freshness_status.value
                status_counts[status] = status_counts.get(status, 0) + 1
        return {"status_counts": status_counts, "total": len(self._reports)}

    async def buying_signals_stats_v2(self) -> dict[str, Any]:
        verdict_counts: dict[str, int] = {}
        for report in self._reports.values():
            if report.evidence.buying_signal_verdict:
                verdict = report.evidence.buying_signal_verdict.value
                verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        return {"verdict_counts": verdict_counts, "total": len(self._reports)}

    async def get_audit_trail(self, company_id: str) -> dict[str, Any]:
        report = self._reports.get(company_id)
        if not report:
            return {"error": "Audit trail not found", "company_id": company_id}
        return {
            "company_id": company_id,
            "audit_trail": [
                {
                    "gate": entry.gate,
                    "decision": entry.decision,
                    "timestamp": entry.timestamp.isoformat(),
                    "reasons": entry.reasons,
                    "evidence": entry.evidence,
                }
                for entry in report.audit_trail
            ],
        }

    def _serialize_report(self, report: QualityReport) -> dict[str, Any]:
        return {
            "id": str(report.id),
            "company_id": str(report.company_id),
            "company_name": report.company_name,
            "quality_score": report.quality_score.total_score if report.quality_score else None,
            "quality_grade": report.quality_grade.value,
            "decision": report.decision,
            "reasons": report.reasons,
            "gates_passed": report.gates_passed,
            "gates_failed": report.gates_failed,
            "rejection_reasons": report.rejection_reasons,
            "created_at": report.created_at.isoformat(),
        }
