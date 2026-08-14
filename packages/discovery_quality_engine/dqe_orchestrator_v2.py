"""DQE v2 Orchestrator — deterministic quality gate pipeline with scoring and grading."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from discovery_quality_engine.activity_engine import ActivityEngine, ActivityEvidence
from discovery_quality_engine.buying_signal_engine import BuyingSignalEngine
from discovery_quality_engine.buying_signal_engine_v2 import BuyingSignalEngineV2
from discovery_quality_engine.company_age import CompanyAgeFilter
from discovery_quality_engine.company_filter import CompanyFilter
from discovery_quality_engine.competitor_engine import CompetitorEngine
from discovery_quality_engine.duplicate_engine import DuplicateEngine
from discovery_quality_engine.freshness_engine import FreshnessEngine
from discovery_quality_engine.freshness_engine_v2 import FreshnessEngineV2
from discovery_quality_engine.industry_filter import IndustryFilter
from discovery_quality_engine.quality_dashboard import QualityDashboard
from discovery_quality_engine.quality_engine import (
    QualityDecision,
    QualityEvent,
    RejectionReason,
)
from discovery_quality_engine.quality_grade_engine import QualityGradeEngine
from discovery_quality_engine.quality_metrics import QualityMetricsCollector
from discovery_quality_engine.quality_report_engine import QualityReportEngine
from discovery_quality_engine.quality_score_engine import QualityScoreEngine
from discovery_quality_engine.region_filter import RegionFilter
from discovery_quality_engine.signal_filter import SignalFilter
from discovery_quality_engine.source_quality import SourceQualityEngine
from discovery_quality_engine.technology_filter import TechnologyFilter
from discovery_quality_engine.v2_schemas import (
    AuditEntry,
    FreshnessStatus,
    QualityEvidence,
    QualityGrade,
    QualityReport,
    ScoreWeight,
)
from discovery_quality_engine.website_quality import WebsiteQualityEngine


class DQEResultV2:
    __slots__ = (
        "decision",
        "grade",
        "report",
        "gates_passed",
        "gates_failed",
        "rejection_reasons",
        "metadata",
    )

    def __init__(
        self,
        *,
        decision: str,
        grade: QualityGrade,
        report: QualityReport,
        gates_passed: list[str],
        gates_failed: list[str],
        rejection_reasons: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.decision = decision
        self.grade = grade
        self.report = report
        self.gates_passed = gates_passed
        self.gates_failed = gates_failed
        self.rejection_reasons = rejection_reasons
        self.metadata = metadata or {}


class DQEOrchestratorV2:
    def __init__(
        self,
        *,
        freshness_engine: FreshnessEngine | None = None,
        freshness_engine_v2: FreshnessEngineV2 | None = None,
        buying_signal_engine: BuyingSignalEngine | None = None,
        buying_signal_engine_v2: BuyingSignalEngineV2 | None = None,
        company_filter: CompanyFilter | None = None,
        signal_filter: SignalFilter | None = None,
        website_quality: WebsiteQualityEngine | None = None,
        source_quality: SourceQualityEngine | None = None,
        duplicate_engine: DuplicateEngine | None = None,
        competitor_engine: CompetitorEngine | None = None,
        activity_engine: ActivityEngine | None = None,
        industry_filter: IndustryFilter | None = None,
        region_filter: RegionFilter | None = None,
        technology_filter: TechnologyFilter | None = None,
        company_age: CompanyAgeFilter | None = None,
        dashboard: QualityDashboard | None = None,
        metrics: QualityMetricsCollector | None = None,
        score_engine: QualityScoreEngine | None = None,
        grade_engine: QualityGradeEngine | None = None,
        report_engine: QualityReportEngine | None = None,
        score_weights: list[ScoreWeight] | None = None,
    ) -> None:
        self.freshness = freshness_engine or FreshnessEngine()
        self.freshness_v2 = freshness_engine_v2 or FreshnessEngineV2()
        self.buying_signal = buying_signal_engine or BuyingSignalEngine()
        self.buying_signal_v2 = buying_signal_engine_v2 or BuyingSignalEngineV2()
        self.company = company_filter or CompanyFilter()
        self.signal = signal_filter or SignalFilter()
        self.website = website_quality or WebsiteQualityEngine()
        self.source = source_quality or SourceQualityEngine()
        self.duplicate = duplicate_engine or DuplicateEngine()
        self.competitor = competitor_engine or CompetitorEngine()
        self.activity = activity_engine or ActivityEngine()
        self.industry = industry_filter or IndustryFilter()
        self.region = region_filter or RegionFilter()
        self.technology = technology_filter or TechnologyFilter()
        self.company_age = company_age or CompanyAgeFilter()
        self.dashboard = dashboard or QualityDashboard()
        self.metrics = metrics or QualityMetricsCollector()
        self.score_engine = score_engine or QualityScoreEngine(weights=score_weights)
        self.grade_engine = grade_engine or QualityGradeEngine()
        self.report_engine = report_engine or QualityReportEngine(
            score_engine=self.score_engine,
            grade_engine=self.grade_engine,
        )

    def evaluate(
        self,
        *,
        company_id: UUID,
        company_name: str,
        website: str | None = None,
        industry: str | None = None,
        country: str | None = None,
        signal_type: str = "",
        signal_source: str = "",
        signal_title: str = "",
        signal_timestamp: datetime | None = None,
        signal_types: list[str] | None = None,
        domain: str | None = None,
        has_https: bool | None = None,
        content_length: int | None = None,
        page_text: str | None = None,
        company_age_days: int | None = None,
        activity_evidence: list[ActivityEvidence] | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        now: datetime | None = None,
    ) -> DQEResultV2:
        gates_passed: list[str] = []
        gates_failed: list[str] = []
        rejection_reasons: list[str] = []
        audit_entries: list[AuditEntry] = []
        current = now or datetime.now(UTC)

        company_result = self.company.evaluate(
            company_name=company_name, website=website, domain=domain
        )
        audit_entries.append(
            AuditEntry(
                gate=self.company.gate_name(),
                decision="PASS" if company_result.decision != QualityDecision.REJECT else "FAIL",
                timestamp=current,
                reasons=company_result.reasons,
            )
        )
        if company_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.company.gate_name())
            rejection_reasons.extend(company_result.reasons)
            return self._finalize_rejection(
                company_id=company_id,
                company_name=company_name,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
                audit_entries=audit_entries,
                now=current,
            )
        gates_passed.append(self.company.gate_name())

        signal_result = self.signal.evaluate(
            signal_type=signal_type,
            signal_source=signal_source,
            signal_title=signal_title,
            signal_timestamp=signal_timestamp,
        )
        audit_entries.append(
            AuditEntry(
                gate=self.signal.gate_name(),
                decision="PASS" if signal_result.decision != QualityDecision.REJECT else "FAIL",
                timestamp=current,
                reasons=signal_result.reasons,
            )
        )
        if signal_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.signal.gate_name())
            rejection_reasons.extend(signal_result.reasons)
            return self._finalize_rejection(
                company_id=company_id,
                company_name=company_name,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
                audit_entries=audit_entries,
                now=current,
            )
        gates_passed.append(self.signal.gate_name())

        freshness_status = FreshnessStatus.ACCEPTED
        if signal_timestamp is not None:
            freshness_v2_result = self.freshness_v2.evaluate(
                signal_timestamp=signal_timestamp, now=current
            )
            freshness_status = freshness_v2_result.status
            audit_entries.append(
                AuditEntry(
                    gate="freshness_v2",
                    decision="PASS" if freshness_status != FreshnessStatus.EXPIRED else "FAIL",
                    timestamp=current,
                    reasons=freshness_v2_result.reasons,
                    evidence=freshness_v2_result.evidence,
                )
            )
            if freshness_status == FreshnessStatus.EXPIRED:
                gates_failed.append("freshness_v2")
                rejection_reasons.extend(freshness_v2_result.reasons)
                return self._finalize_rejection(
                    company_id=company_id,
                    company_name=company_name,
                    gates_passed=gates_passed,
                    gates_failed=gates_failed,
                    rejection_reasons=rejection_reasons,
                    audit_entries=audit_entries,
                    now=current,
                )
            gates_passed.append("freshness_v2")

        website_result = self.website.evaluate(
            website, has_https=has_https, content_length=content_length, page_text=page_text
        )
        audit_entries.append(
            AuditEntry(
                gate=self.website.gate_name(),
                decision="PASS" if website_result.decision != QualityDecision.REJECT else "FAIL",
                timestamp=current,
                reasons=website_result.reasons,
            )
        )
        if website_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.website.gate_name())
            rejection_reasons.extend(website_result.reasons)
            return self._finalize_rejection(
                company_id=company_id,
                company_name=company_name,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
                audit_entries=audit_entries,
                now=current,
            )
        gates_passed.append(self.website.gate_name())

        source_result = self.source.evaluate(signal_source)
        audit_entries.append(
            AuditEntry(
                gate=self.source.gate_name(),
                decision="PASS" if source_result.decision != QualityDecision.REJECT else "FAIL",
                timestamp=current,
                reasons=source_result.reasons,
            )
        )
        if source_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.source.gate_name())
            rejection_reasons.extend(source_result.reasons)
            return self._finalize_rejection(
                company_id=company_id,
                company_name=company_name,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
                audit_entries=audit_entries,
                now=current,
            )
        gates_passed.append(self.source.gate_name())

        domain_to_check = domain or website
        if domain_to_check:
            dup_domain = self.duplicate.check_domain(domain_to_check)
            if dup_domain.decision == QualityDecision.REJECT:
                gates_failed.append(self.duplicate.gate_name())
                rejection_reasons.extend(dup_domain.reasons)
                audit_entries.append(
                    AuditEntry(
                        gate=self.duplicate.gate_name(),
                        decision="FAIL",
                        timestamp=current,
                        reasons=dup_domain.reasons,
                    )
                )
                return self._finalize_rejection(
                    company_id=company_id,
                    company_name=company_name,
                    gates_passed=gates_passed,
                    gates_failed=gates_failed,
                    rejection_reasons=rejection_reasons,
                    audit_entries=audit_entries,
                    now=current,
                )

        dup_company = self.duplicate.check_company(company_name)
        if dup_company.decision == QualityDecision.REJECT:
            gates_failed.append(self.duplicate.gate_name())
            rejection_reasons.extend(dup_company.reasons)
            audit_entries.append(
                AuditEntry(
                    gate=self.duplicate.gate_name(),
                    decision="FAIL",
                    timestamp=current,
                    reasons=dup_company.reasons,
                )
            )
            return self._finalize_rejection(
                company_id=company_id,
                company_name=company_name,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
                audit_entries=audit_entries,
                now=current,
            )

        if signal_type and signal_source:
            dup_opp = self.duplicate.check_opportunity(company_name, signal_type, signal_source)
            if dup_opp.decision == QualityDecision.REJECT:
                gates_failed.append(self.duplicate.gate_name())
                rejection_reasons.extend(dup_opp.reasons)
                audit_entries.append(
                    AuditEntry(
                        gate=self.duplicate.gate_name(),
                        decision="FAIL",
                        timestamp=current,
                        reasons=dup_opp.reasons,
                    )
                )
                return self._finalize_rejection(
                    company_id=company_id,
                    company_name=company_name,
                    gates_passed=gates_passed,
                    gates_failed=gates_failed,
                    rejection_reasons=rejection_reasons,
                    audit_entries=audit_entries,
                    now=current,
                )
        gates_passed.append(self.duplicate.gate_name())
        audit_entries.append(
            AuditEntry(
                gate=self.duplicate.gate_name(),
                decision="PASS",
                timestamp=current,
            )
        )

        competitor_result = self.competitor.evaluate(company_name)
        audit_entries.append(
            AuditEntry(
                gate=self.competitor.gate_name(),
                decision="PASS" if competitor_result.decision != QualityDecision.REJECT else "FAIL",
                timestamp=current,
                reasons=competitor_result.reasons,
            )
        )
        if competitor_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.competitor.gate_name())
            rejection_reasons.extend(competitor_result.reasons)
            return self._finalize_rejection(
                company_id=company_id,
                company_name=company_name,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
                audit_entries=audit_entries,
                now=current,
            )
        gates_passed.append(self.competitor.gate_name())

        tech_result = self.technology.evaluate(
            description=description, industry=industry, tags=tags, company_name=company_name
        )
        audit_entries.append(
            AuditEntry(
                gate=self.technology.gate_name(),
                decision="PASS" if tech_result.decision != QualityDecision.REJECT else "FAIL",
                timestamp=current,
                reasons=tech_result.reasons,
            )
        )
        if tech_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.technology.gate_name())
            rejection_reasons.extend(tech_result.reasons)
            return self._finalize_rejection(
                company_id=company_id,
                company_name=company_name,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
                audit_entries=audit_entries,
                now=current,
            )
        gates_passed.append(self.technology.gate_name())

        activity_result = self.activity.evaluate(activity_evidence, now=current)
        audit_entries.append(
            AuditEntry(
                gate=self.activity.gate_name(),
                decision="PASS" if activity_result.decision != QualityDecision.REJECT else "FAIL",
                timestamp=current,
                reasons=activity_result.reasons,
            )
        )
        if activity_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.activity.gate_name())
            rejection_reasons.extend(activity_result.reasons)
            return self._finalize_rejection(
                company_id=company_id,
                company_name=company_name,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
                audit_entries=audit_entries,
                now=current,
            )
        gates_passed.append(self.activity.gate_name())

        industry_result = self.industry.evaluate(industry)
        audit_entries.append(
            AuditEntry(
                gate=self.industry.gate_name(),
                decision="PASS" if industry_result.decision != QualityDecision.REJECT else "FAIL",
                timestamp=current,
                reasons=industry_result.reasons,
            )
        )
        if industry_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.industry.gate_name())
            rejection_reasons.extend(industry_result.reasons)
            return self._finalize_rejection(
                company_id=company_id,
                company_name=company_name,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
                audit_entries=audit_entries,
                now=current,
            )
        gates_passed.append(self.industry.gate_name())

        region_result = self.region.evaluate(country)
        audit_entries.append(
            AuditEntry(
                gate=self.region.gate_name(),
                decision="PASS" if region_result.decision != QualityDecision.REJECT else "FAIL",
                timestamp=current,
                reasons=region_result.reasons,
            )
        )
        if region_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.region.gate_name())
            rejection_reasons.extend(region_result.reasons)
            return self._finalize_rejection(
                company_id=company_id,
                company_name=company_name,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
                audit_entries=audit_entries,
                now=current,
            )
        gates_passed.append(self.region.gate_name())

        age_result = self.company_age.evaluate(company_age_days)
        audit_entries.append(
            AuditEntry(
                gate=self.company_age.gate_name(),
                decision="PASS" if age_result.decision != QualityDecision.REJECT else "FAIL",
                timestamp=current,
                reasons=age_result.reasons,
            )
        )
        if age_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.company_age.gate_name())
            rejection_reasons.extend(age_result.reasons)
            return self._finalize_rejection(
                company_id=company_id,
                company_name=company_name,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
                audit_entries=audit_entries,
                now=current,
            )
        gates_passed.append(self.company_age.gate_name())

        effective_signal_types = signal_types or ([signal_type] if signal_type else [])
        bs_v2_result = self.buying_signal_v2.evaluate(signal_types=effective_signal_types)
        audit_entries.append(
            AuditEntry(
                gate="buying_signal_v2",
                decision="PASS" if bs_v2_result.verdict.value != "not_valid" else "FAIL",
                timestamp=current,
                reasons=bs_v2_result.reasons,
                evidence=bs_v2_result.evidence,
            )
        )
        if bs_v2_result.verdict.value == "not_valid":
            gates_failed.append("buying_signal_v2")
            rejection_reasons.extend(bs_v2_result.reasons)
            return self._finalize_rejection(
                company_id=company_id,
                company_name=company_name,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
                audit_entries=audit_entries,
                now=current,
            )
        gates_passed.append("buying_signal_v2")

        evidence = self._build_evidence(
            freshness_status=freshness_status,
            signal_timestamp=signal_timestamp,
            now=current,
            bs_v2_result=bs_v2_result,
            source_result=source_result,
            source=signal_source,
            website_result=website_result,
            company_age_days=company_age_days,
            industry=industry,
            country=country,
            company_name=company_name,
        )

        freshness_raw_score = self.score_engine.calculate_freshness_score(
            status=freshness_status,
            signal_age_days=(current - signal_timestamp).days if signal_timestamp else 0,
        )
        buying_signal_raw_score = self.score_engine.calculate_buying_signal_score(
            valid_count=len(bs_v2_result.valid_signals),
            not_valid_count=len(bs_v2_result.not_valid_signals),
            borderline_count=len(bs_v2_result.borderline_signals),
        )
        source_trust_raw_score = self._calculate_source_trust_score(source_result)
        website_quality_raw_score = self._calculate_website_score(website_result)
        company_validation_raw_score = self._calculate_company_validation_score(
            company_age_days=company_age_days,
            dup_domain=dup_domain.decision if domain_to_check else None,
            dup_company=dup_company.decision,
        )
        icp_match_raw_score = self._calculate_icp_match_score(industry, country)
        region_raw_score = 100.0 if region_result.decision != QualityDecision.REJECT else 0.0
        industry_raw_score = 100.0 if industry_result.decision != QualityDecision.REJECT else 0.0

        return self._finalize_acceptance(
            company_id=company_id,
            company_name=company_name,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
            rejection_reasons=rejection_reasons,
            audit_entries=audit_entries,
            freshness_raw_score=freshness_raw_score,
            buying_signal_raw_score=buying_signal_raw_score,
            source_trust_raw_score=source_trust_raw_score,
            website_quality_raw_score=website_quality_raw_score,
            company_validation_raw_score=company_validation_raw_score,
            icp_match_raw_score=icp_match_raw_score,
            region_raw_score=region_raw_score,
            industry_raw_score=industry_raw_score,
            now=current,
        )

    def _build_evidence(
        self,
        *,
        freshness_status: FreshnessStatus,
        signal_timestamp: datetime | None,
        now: datetime,
        bs_v2_result: Any,
        source_result: Any,
        source: str,
        website_result: Any,
        company_age_days: int | None,
        industry: str | None,
        country: str | None,
        company_name: str,
    ) -> QualityEvidence:
        signal_age_days = None
        if signal_timestamp:
            if signal_timestamp.tzinfo is None:
                signal_timestamp = signal_timestamp.replace(tzinfo=UTC)
            signal_age_days = (now - signal_timestamp).days

        return QualityEvidence(
            signal_freshness_days=signal_age_days,
            signal_freshness_status=freshness_status,
            buying_signals_detected=bs_v2_result.valid_signals + bs_v2_result.not_valid_signals,
            buying_signal_verdict=bs_v2_result.verdict,
            source_trust_level=source,
            website_score=0.0,
            company_age_days=company_age_days,
            icp_match_score=50.0,
            region_match=country is not None,
            industry_match=industry is not None,
            competitor_flag=False,
            duplicate_flag=False,
        )

    def _calculate_source_trust_score(self, source_result: Any) -> float:
        if source_result.decision != QualityDecision.REJECT:
            return 100.0
        return 0.0

    def _calculate_website_score(self, website_result: Any) -> float:
        if website_result.decision != QualityDecision.REJECT:
            return 100.0
        return 0.0

    def _calculate_company_validation_score(
        self,
        *,
        company_age_days: int | None,
        dup_domain: Any,
        dup_company: Any,
    ) -> float:
        score = 100.0
        if dup_domain == QualityDecision.REJECT:
            score -= 50.0
        if dup_company == QualityDecision.REJECT:
            score -= 50.0
        if company_age_days is not None and company_age_days < 90:
            score -= 25.0
        return max(0.0, score)

    def _calculate_icp_match_score(self, industry: str | None, country: str | None) -> float:
        score = 50.0
        if industry:
            score += 25.0
        if country:
            score += 25.0
        return min(100.0, score)

    def _finalize_acceptance(
        self,
        *,
        company_id: UUID,
        company_name: str,
        evidence: QualityEvidence,
        gates_passed: list[str],
        gates_failed: list[str],
        rejection_reasons: list[str],
        audit_entries: list[AuditEntry],
        freshness_raw_score: float,
        buying_signal_raw_score: float,
        source_trust_raw_score: float,
        website_quality_raw_score: float,
        company_validation_raw_score: float,
        icp_match_raw_score: float,
        region_raw_score: float,
        industry_raw_score: float,
        now: datetime,
    ) -> DQEResultV2:
        report = self.report_engine.generate(
            company_id=company_id,
            company_name=company_name,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
            rejection_reasons=rejection_reasons,
            freshness_raw_score=freshness_raw_score,
            buying_signal_raw_score=buying_signal_raw_score,
            source_trust_raw_score=source_trust_raw_score,
            website_quality_raw_score=website_quality_raw_score,
            company_validation_raw_score=company_validation_raw_score,
            icp_match_raw_score=icp_match_raw_score,
            region_raw_score=region_raw_score,
            industry_raw_score=industry_raw_score,
            audit_entries=audit_entries,
            now=now,
        )

        event = QualityEvent(
            company_id=company_id,
            company_name=company_name,
            signal_type="",
            source="",
            decision=QualityDecision.ACCEPT,
            gates_passed=list(gates_passed),
            gates_failed=list(gates_failed),
            rejection_reasons=list(rejection_reasons),
        )
        self.dashboard.record(event)
        self.metrics.record_decision(
            decision="ACCEPT",
            rejection_reasons=rejection_reasons,
            gates_failed=gates_failed,
        )

        return DQEResultV2(
            decision=report.decision,
            grade=report.quality_grade,
            report=report,
            gates_passed=list(gates_passed),
            gates_failed=list(gates_failed),
            rejection_reasons=list(rejection_reasons),
            metadata={"event_id": str(event.id)},
        )

    def _finalize_rejection(
        self,
        *,
        company_id: UUID,
        company_name: str,
        gates_passed: list[str],
        gates_failed: list[str],
        rejection_reasons: list[str],
        audit_entries: list[AuditEntry],
        now: datetime,
    ) -> DQEResultV2:
        report = self.report_engine.generate_rejection_report(
            company_id=company_id,
            company_name=company_name,
            rejection_reasons=rejection_reasons,
            gates_failed=gates_failed,
            now=now,
        )

        event = QualityEvent(
            company_id=company_id,
            company_name=company_name,
            signal_type="",
            source="",
            decision=QualityDecision.REJECT,
            gates_passed=list(gates_passed),
            gates_failed=list(gates_failed),
            rejection_reasons=list(rejection_reasons),
        )
        self.dashboard.record(event)
        self.metrics.record_decision(
            decision="REJECT",
            rejection_reasons=rejection_reasons,
            gates_failed=gates_failed,
        )

        return DQEResultV2(
            decision="REJECT",
            grade=QualityGrade.REJECT,
            report=report,
            gates_passed=list(gates_passed),
            gates_failed=list(gates_failed),
            rejection_reasons=list(rejection_reasons),
            metadata={"event_id": str(event.id)},
        )
