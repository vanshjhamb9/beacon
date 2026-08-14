"""DQE Orchestrator — deterministic quality gate pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from discovery_quality_engine.activity_engine import ActivityEngine, ActivityEvidence
from discovery_quality_engine.buying_signal_engine import BuyingSignalEngine
from discovery_quality_engine.company_age import CompanyAgeFilter
from discovery_quality_engine.company_filter import CompanyFilter
from discovery_quality_engine.competitor_engine import CompetitorConfig, CompetitorEngine
from discovery_quality_engine.duplicate_engine import DuplicateEngine
from discovery_quality_engine.freshness_engine import FreshnessEngine
from discovery_quality_engine.industry_filter import IndustryFilter
from discovery_quality_engine.quality_dashboard import QualityDashboard
from discovery_quality_engine.quality_engine import (
    QualityDecision,
    QualityEvent,
    QualityGate,
    RejectionReason,
)
from discovery_quality_engine.quality_metrics import QualityMetricsCollector
from discovery_quality_engine.region_filter import RegionFilter
from discovery_quality_engine.signal_filter import SignalFilter
from discovery_quality_engine.source_quality import SourceQualityEngine
from discovery_quality_engine.technology_filter import TechnologyFilter
from discovery_quality_engine.website_quality import WebsiteQualityEngine


class DQEResult:
    __slots__ = ("decision", "gates_passed", "gates_failed", "rejection_reasons", "metadata")

    def __init__(
        self,
        *,
        decision: QualityDecision,
        gates_passed: list[str],
        gates_failed: list[str],
        rejection_reasons: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.decision = decision
        self.gates_passed = gates_passed
        self.gates_failed = gates_failed
        self.rejection_reasons = rejection_reasons
        self.metadata = metadata or {}


class DQEOrchestrator:
    def __init__(
        self,
        *,
        freshness_engine: FreshnessEngine | None = None,
        buying_signal_engine: BuyingSignalEngine | None = None,
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
    ) -> None:
        self.freshness = freshness_engine or FreshnessEngine()
        self.buying_signal = buying_signal_engine or BuyingSignalEngine()
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
    ) -> DQEResult:
        gates_passed: list[str] = []
        gates_failed: list[str] = []
        rejection_reasons: list[str] = []
        current = now or datetime.now(UTC)

        company_result = self.company.evaluate(
            company_name=company_name, website=website, domain=domain
        )
        if company_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.company.gate_name())
            rejection_reasons.extend(company_result.reasons)
            return self._finalize(
                company_id=company_id,
                company_name=company_name,
                signal_type=signal_type,
                signal_source=signal_source,
                decision=QualityDecision.REJECT,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
            )
        gates_passed.append(self.company.gate_name())

        signal_result = self.signal.evaluate(
            signal_type=signal_type,
            signal_source=signal_source,
            signal_title=signal_title,
            signal_timestamp=signal_timestamp,
        )
        if signal_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.signal.gate_name())
            rejection_reasons.extend(signal_result.reasons)
            return self._finalize(
                company_id=company_id,
                company_name=company_name,
                signal_type=signal_type,
                signal_source=signal_source,
                decision=QualityDecision.REJECT,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
            )
        gates_passed.append(self.signal.gate_name())

        if signal_timestamp is not None:
            freshness_result = self.freshness.evaluate(
                signal_type=signal_type, signal_timestamp=signal_timestamp, now=current
            )
            if freshness_result.decision == QualityDecision.REJECT:
                gates_failed.append(self.freshness.gate_name())
                rejection_reasons.extend(freshness_result.reasons)
                self.metrics.record_gate_evaluation(self.freshness.gate_name(), passed=False)
                return self._finalize(
                    company_id=company_id,
                    company_name=company_name,
                    signal_type=signal_type,
                    signal_source=signal_source,
                    decision=QualityDecision.REJECT,
                    gates_passed=gates_passed,
                    gates_failed=gates_failed,
                    rejection_reasons=rejection_reasons,
                )
            gates_passed.append(self.freshness.gate_name())
            self.metrics.record_gate_evaluation(self.freshness.gate_name(), passed=True)

        website_result = self.website.evaluate(
            website, has_https=has_https, content_length=content_length, page_text=page_text
        )
        if website_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.website.gate_name())
            rejection_reasons.extend(website_result.reasons)
            return self._finalize(
                company_id=company_id,
                company_name=company_name,
                signal_type=signal_type,
                signal_source=signal_source,
                decision=QualityDecision.REJECT,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
            )
        gates_passed.append(self.website.gate_name())

        source_result = self.source.evaluate(signal_source)
        if source_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.source.gate_name())
            rejection_reasons.extend(source_result.reasons)
            return self._finalize(
                company_id=company_id,
                company_name=company_name,
                signal_type=signal_type,
                signal_source=signal_source,
                decision=QualityDecision.REJECT,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
            )
        gates_passed.append(self.source.gate_name())

        domain_to_check = domain or website
        if domain_to_check:
            dup_domain = self.duplicate.check_domain(domain_to_check)
            if dup_domain.decision == QualityDecision.REJECT:
                gates_failed.append(self.duplicate.gate_name())
                rejection_reasons.extend(dup_domain.reasons)
                return self._finalize(
                    company_id=company_id,
                    company_name=company_name,
                    signal_type=signal_type,
                    signal_source=signal_source,
                    decision=QualityDecision.REJECT,
                    gates_passed=gates_passed,
                    gates_failed=gates_failed,
                    rejection_reasons=rejection_reasons,
                )

        dup_company = self.duplicate.check_company(company_name)
        if dup_company.decision == QualityDecision.REJECT:
            gates_failed.append(self.duplicate.gate_name())
            rejection_reasons.extend(dup_company.reasons)
            return self._finalize(
                company_id=company_id,
                company_name=company_name,
                signal_type=signal_type,
                signal_source=signal_source,
                decision=QualityDecision.REJECT,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
            )

        if signal_type and signal_source:
            dup_opp = self.duplicate.check_opportunity(company_name, signal_type, signal_source)
            if dup_opp.decision == QualityDecision.REJECT:
                gates_failed.append(self.duplicate.gate_name())
                rejection_reasons.extend(dup_opp.reasons)
                return self._finalize(
                    company_id=company_id,
                    company_name=company_name,
                    signal_type=signal_type,
                    signal_source=signal_source,
                    decision=QualityDecision.REJECT,
                    gates_passed=gates_passed,
                    gates_failed=gates_failed,
                    rejection_reasons=rejection_reasons,
                )
        gates_passed.append(self.duplicate.gate_name())

        competitor_result = self.competitor.evaluate(company_name)
        if competitor_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.competitor.gate_name())
            rejection_reasons.extend(competitor_result.reasons)
            return self._finalize(
                company_id=company_id,
                company_name=company_name,
                signal_type=signal_type,
                signal_source=signal_source,
                decision=QualityDecision.REJECT,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
            )
        gates_passed.append(self.competitor.gate_name())

        tech_result = self.technology.evaluate(
            description=description, industry=industry, tags=tags, company_name=company_name
        )
        if tech_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.technology.gate_name())
            rejection_reasons.extend(tech_result.reasons)
            return self._finalize(
                company_id=company_id,
                company_name=company_name,
                signal_type=signal_type,
                signal_source=signal_source,
                decision=QualityDecision.REJECT,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
            )
        gates_passed.append(self.technology.gate_name())

        activity_result = self.activity.evaluate(activity_evidence, now=current)
        if activity_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.activity.gate_name())
            rejection_reasons.extend(activity_result.reasons)
            return self._finalize(
                company_id=company_id,
                company_name=company_name,
                signal_type=signal_type,
                signal_source=signal_source,
                decision=QualityDecision.REJECT,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
            )
        gates_passed.append(self.activity.gate_name())

        industry_result = self.industry.evaluate(industry)
        if industry_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.industry.gate_name())
            rejection_reasons.extend(industry_result.reasons)
            return self._finalize(
                company_id=company_id,
                company_name=company_name,
                signal_type=signal_type,
                signal_source=signal_source,
                decision=QualityDecision.REJECT,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
            )
        gates_passed.append(self.industry.gate_name())

        region_result = self.region.evaluate(country)
        if region_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.region.gate_name())
            rejection_reasons.extend(region_result.reasons)
            return self._finalize(
                company_id=company_id,
                company_name=company_name,
                signal_type=signal_type,
                signal_source=signal_source,
                decision=QualityDecision.REJECT,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
            )
        gates_passed.append(self.region.gate_name())

        age_result = self.company_age.evaluate(company_age_days)
        if age_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.company_age.gate_name())
            rejection_reasons.extend(age_result.reasons)
            return self._finalize(
                company_id=company_id,
                company_name=company_name,
                signal_type=signal_type,
                signal_source=signal_source,
                decision=QualityDecision.REJECT,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
            )
        gates_passed.append(self.company_age.gate_name())

        effective_signal_types = signal_types or ([signal_type] if signal_type else [])
        bs_result = self.buying_signal.evaluate(effective_signal_types)
        if bs_result.decision == QualityDecision.REJECT:
            gates_failed.append(self.buying_signal.gate_name())
            rejection_reasons.extend(bs_result.reasons)
            return self._finalize(
                company_id=company_id,
                company_name=company_name,
                signal_type=signal_type,
                signal_source=signal_source,
                decision=QualityDecision.REJECT,
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                rejection_reasons=rejection_reasons,
            )
        gates_passed.append(self.buying_signal.gate_name())

        return self._finalize(
            company_id=company_id,
            company_name=company_name,
            signal_type=signal_type,
            signal_source=signal_source,
            decision=QualityDecision.ACCEPT,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
            rejection_reasons=[],
        )

    def _finalize(
        self,
        *,
        company_id: UUID,
        company_name: str,
        signal_type: str,
        signal_source: str,
        decision: QualityDecision,
        gates_passed: list[str],
        gates_failed: list[str],
        rejection_reasons: list[str],
    ) -> DQEResult:
        event = QualityEvent(
            company_id=company_id,
            company_name=company_name,
            signal_type=signal_type,
            source=signal_source,
            decision=decision,
            gates_passed=list(gates_passed),
            gates_failed=list(gates_failed),
            rejection_reasons=list(rejection_reasons),
        )
        self.dashboard.record(event)
        self.metrics.record_decision(
            decision=decision.value,
            rejection_reasons=rejection_reasons,
            gates_failed=gates_failed,
        )
        return DQEResult(
            decision=decision,
            gates_passed=list(gates_passed),
            gates_failed=list(gates_failed),
            rejection_reasons=list(rejection_reasons),
            metadata={"event_id": str(event.id)},
        )
