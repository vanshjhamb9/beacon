from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from data_verification.coverage.engine import CoverageEngine
from data_verification.freshness.engine import FreshnessEngine
from data_verification.metrics.timing import VerificationTimer
from data_verification.models.types import (
    AutomaticAction,
    ConnectorStatistic,
    FreshnessStatus,
    ReadinessDecision,
    VerificationInput,
    VerificationResult,
    VerificationStatus,
)
from data_verification.pipelines.observation_builder import ObservationBuilder
from data_verification.trust.engine import TrustEngine
from data_verification.validators.fields import FieldVerificationEngine


class VerificationPipeline:
    def __init__(
        self,
        *,
        coverage: CoverageEngine | None = None,
        freshness: FreshnessEngine | None = None,
        trust: TrustEngine | None = None,
        fields: FieldVerificationEngine | None = None,
        observations: ObservationBuilder | None = None,
        timer: VerificationTimer | None = None,
        completeness_threshold: float = 70.0,
        freshness_expired_action: bool = True,
        trust_review_threshold: float = 55.0,
    ) -> None:
        self.coverage = coverage or CoverageEngine()
        self.freshness = freshness or FreshnessEngine()
        self.trust = trust or TrustEngine()
        self.fields = fields or FieldVerificationEngine(freshness=self.freshness, trust=self.trust)
        self.observations = observations or ObservationBuilder()
        self.timer = timer or VerificationTimer()
        self.completeness_threshold = completeness_threshold
        self.freshness_expired_action = freshness_expired_action
        self.trust_review_threshold = trust_review_threshold

    def process(self, item: VerificationInput) -> VerificationResult:
        def _run() -> VerificationResult:
            now = datetime.now(UTC)
            completeness, coverage, checklist, missing = self.coverage.evaluate(
                item.lead_profile,
                timeline_event_count=item.timeline_event_count,
            )
            observations = self.observations.build(
                item.lead_profile,
                enriched_at=item.enriched_at,
                source_rows=item.source_rows,
            )
            field_results = self.fields.verify(observations, verified_at=now)
            profile_freshness, freshness_status, _age = self.freshness.evaluate(item.enriched_at, now=now)
            trust_score = self.trust.score_profile(observations)

            verified_count = sum(
                1
                for field in field_results
                if field.is_canonical
                and field.verification_status
                in {VerificationStatus.VERIFIED, VerificationStatus.PARTIAL}
            )
            canonical_count = sum(1 for field in field_results if field.is_canonical) or 1
            verification_percent = round((verified_count / canonical_count) * 100.0, 2)
            coverage_percent = completeness.overall_completeness

            overall_quality = round(
                completeness.overall_completeness * 0.40
                + verification_percent * 0.25
                + profile_freshness * 0.20
                + trust_score * 0.15,
                2,
            )
            overall_readiness = round(
                completeness.overall_completeness * 0.45
                + profile_freshness * 0.20
                + trust_score * 0.20
                + verification_percent * 0.15,
                2,
            )

            actions: list[AutomaticAction] = []
            reason_codes: list[str] = []
            if completeness.overall_completeness < self.completeness_threshold:
                actions.append(AutomaticAction.SCHEDULE_ENRICHMENT_REFRESH)
                reason_codes.append("completeness_below_threshold")
            if self.freshness_expired_action and freshness_status == FreshnessStatus.EXPIRED:
                actions.append(AutomaticAction.QUEUE_REENRICHMENT)
                reason_codes.append("freshness_expired")
            elif freshness_status == FreshnessStatus.STALE:
                actions.append(AutomaticAction.SCHEDULE_ENRICHMENT_REFRESH)
                reason_codes.append("freshness_stale")
            if trust_score < self.trust_review_threshold:
                actions.append(AutomaticAction.FLAG_FOR_REVIEW)
                reason_codes.append("trust_below_threshold")
            if any(field.verification_status == VerificationStatus.CONFLICTING and field.is_canonical for field in field_results):
                actions.append(AutomaticAction.FLAG_FOR_REVIEW)
                reason_codes.append("field_conflicts_present")
            if not actions:
                actions.append(AutomaticAction.NONE)

            unique_actions = list(dict.fromkeys(actions))
            decision = self._decision(overall_readiness, unique_actions, completeness.overall_completeness)
            connector_stats = self._connector_statistics(
                field_results=field_results,
                enrichment_latency_ms=item.enrichment_latency_ms,
            )

            return VerificationResult(
                company_id=item.company_id,
                opportunity_id=item.opportunity_id,
                enrichment_report_id=item.enrichment_report_id,
                company_name=item.company_name,
                completeness=completeness,
                coverage=coverage,
                field_verifications=field_results,
                freshness_score=profile_freshness,
                freshness_status=freshness_status,
                trust_score=trust_score,
                verification_percent=verification_percent,
                coverage_percent=coverage_percent,
                overall_data_quality=overall_quality,
                overall_readiness=overall_readiness,
                readiness_checklist=checklist,
                decision=decision,
                automatic_actions=unique_actions,
                reason_codes=sorted(set(reason_codes)),
                missing_fields=missing,
                connector_statistics=connector_stats,
                explanation={
                    "completeness_threshold": self.completeness_threshold,
                    "trust_review_threshold": self.trust_review_threshold,
                    "timeline_event_count": item.timeline_event_count,
                    "canonical_fields": canonical_count,
                    "verified_fields": verified_count,
                },
            )

        result, latency_ms = self.timer.measure(_run)
        return result.model_copy(update={"processing_latency_ms": latency_ms})

    def _decision(
        self,
        readiness: float,
        actions: list[AutomaticAction],
        completeness: float,
    ) -> ReadinessDecision:
        if AutomaticAction.FLAG_FOR_REVIEW in actions:
            return ReadinessDecision.NEEDS_REVIEW
        if AutomaticAction.QUEUE_REENRICHMENT in actions:
            return ReadinessDecision.NEEDS_REFRESH
        if AutomaticAction.SCHEDULE_ENRICHMENT_REFRESH in actions or completeness < self.completeness_threshold:
            return ReadinessDecision.NEEDS_REFRESH if readiness < 80 else ReadinessDecision.INCOMPLETE
        if readiness >= 80:
            return ReadinessDecision.READY
        return ReadinessDecision.INCOMPLETE

    def _connector_statistics(
        self,
        *,
        field_results: list,
        enrichment_latency_ms: float,
    ) -> list[ConnectorStatistic]:
        by_connector: dict[str, list] = defaultdict(list)
        for field in field_results:
            if not field.is_canonical:
                continue
            by_connector[field.connector].append(field)

        stats: list[ConnectorStatistic] = []
        for connector, fields in sorted(by_connector.items()):
            failures = sum(
                1
                for field in fields
                if field.verification_status in {VerificationStatus.MISSING, VerificationStatus.FLAGGED}
            )
            total = len(fields) or 1
            avg_confidence = sum(field.confidence for field in fields) / total
            success_rate = round(((total - failures) / total) * 100.0, 2)
            stats.append(
                ConnectorStatistic(
                    connector=connector,
                    success_rate=success_rate,
                    average_latency_ms=enrichment_latency_ms,
                    failure_rate=round(100.0 - success_rate, 2),
                    coverage=round(min(100.0, (len(fields) / max(1, len(field_results))) * 100.0), 2),
                    fields_returned=len(fields),
                    average_confidence=round(avg_confidence, 2),
                    companies_enriched=1,
                )
            )
        return stats
