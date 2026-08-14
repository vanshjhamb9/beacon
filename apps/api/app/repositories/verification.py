from collections import Counter
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrichment import EnrichmentReport, EnrichmentSource
from app.models.intelligence import CompanyTimeline
from app.models.verification import (
    ConnectorStatisticRow,
    CoverageMetric,
    FieldStatistic,
    FieldVerification,
    FreshnessMetric,
    ProfileCompleteness,
    TrustScore,
    VerificationHistory,
    VerificationReport,
)
from data_verification.models.types import (
    AutomaticAction,
    ConnectorStatistic,
    DashboardMetrics,
    VerificationInput,
    VerificationResult,
)


class VerificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def pending_verification_inputs(self, *, limit: int) -> Sequence[VerificationInput]:
        stale_or_missing = ~exists().where(
            VerificationReport.enrichment_report_id == EnrichmentReport.id,
            VerificationReport.created_at >= EnrichmentReport.created_at,
        )
        result = await self.session.execute(
            select(EnrichmentReport.id)
            .where(stale_or_missing)
            .order_by(EnrichmentReport.created_at.desc())
            .limit(limit)
        )
        inputs: list[VerificationInput] = []
        for report_id in result.scalars().all():
            item = await self.verification_input(report_id)
            if item is not None:
                inputs.append(item)
        return inputs

    async def verification_input(
        self,
        enrichment_report_id: UUID,
        *,
        force_refresh: bool = False,
    ) -> VerificationInput | None:
        report = await self.session.get(EnrichmentReport, enrichment_report_id)
        if report is None:
            return None
        source_rows = list(await self._sources(report.id))
        timeline_count = await self._timeline_count(report.company_id)
        return VerificationInput(
            company_id=report.company_id,
            opportunity_id=report.opportunity_id,
            enrichment_report_id=report.id,
            company_name=report.company_name,
            enriched_at=report.created_at,
            lead_profile=dict(report.lead_profile or {}),
            source_rows=source_rows,
            timeline_event_count=timeline_count,
            enrichment_latency_ms=report.processing_latency_ms,
            force_refresh=force_refresh,
        )

    async def store_verification(self, result: VerificationResult) -> UUID:
        report = VerificationReport(
            company_id=result.company_id,
            opportunity_id=result.opportunity_id,
            enrichment_report_id=result.enrichment_report_id,
            company_name=result.company_name,
            overall_data_quality=result.overall_data_quality,
            overall_readiness=result.overall_readiness,
            coverage_percent=result.coverage_percent,
            verification_percent=result.verification_percent,
            freshness_score=result.freshness_score,
            freshness_status=result.freshness_status.value,
            trust_score=result.trust_score,
            decision=result.decision.value,
            automatic_actions=[action.value for action in result.automatic_actions],
            reason_codes=list(result.reason_codes),
            missing_fields=list(result.missing_fields),
            readiness_checklist=result.readiness_checklist.model_dump(mode="json"),
            explanation=result.explanation,
            result_payload=result.model_dump(mode="json"),
            processing_latency_ms=result.processing_latency_ms,
        )
        self.session.add(report)
        await self.session.flush()

        completeness = result.completeness
        self.session.add(
            ProfileCompleteness(
                company_id=result.company_id,
                verification_report_id=report.id,
                enrichment_report_id=result.enrichment_report_id,
                overall_completeness=completeness.overall_completeness,
                company_profile_completeness=completeness.company_profile_completeness,
                contact_completeness=completeness.contact_completeness,
                leadership_completeness=completeness.leadership_completeness,
                technology_completeness=completeness.technology_completeness,
                revenue_completeness=completeness.revenue_completeness,
                hiring_completeness=completeness.hiring_completeness,
                social_profile_completeness=completeness.social_profile_completeness,
                evidence_completeness=completeness.evidence_completeness,
                timeline_completeness=completeness.timeline_completeness,
            )
        )

        for coverage in result.coverage:
            self.session.add(
                CoverageMetric(
                    company_id=result.company_id,
                    verification_report_id=report.id,
                    category=coverage.category,
                    present_fields=coverage.present_fields,
                    expected_fields=coverage.expected_fields,
                    score=coverage.score,
                    missing_fields=list(coverage.missing_fields),
                )
            )

        self.session.add(
            FreshnessMetric(
                company_id=result.company_id,
                verification_report_id=report.id,
                field_name=None,
                freshness_score=result.freshness_score,
                freshness_status=result.freshness_status.value,
                scope="profile",
            )
        )
        self.session.add(
            TrustScore(
                company_id=result.company_id,
                verification_report_id=report.id,
                scope="profile",
                field_name=None,
                source=None,
                trust_score=result.trust_score,
                details={"decision": result.decision.value},
            )
        )

        for field in result.field_verifications:
            self.session.add(
                FieldVerification(
                    company_id=result.company_id,
                    verification_report_id=report.id,
                    field_name=field.field_name,
                    category=field.category,
                    value=field.value,
                    source=field.source,
                    source_url=field.source_url,
                    connector=field.connector,
                    verified_at=field.verified_at,
                    confidence=field.confidence,
                    freshness_score=field.freshness_score,
                    freshness_status=field.freshness_status.value,
                    trust_score=field.trust_score,
                    verification_status=field.verification_status.value,
                    confirmed_by=list(field.confirmed_by),
                    conflicting_sources=list(field.conflicting_sources),
                    is_canonical=field.is_canonical,
                    conflict_explanation=field.conflict_explanation,
                )
            )
            if field.is_canonical:
                self.session.add(
                    FreshnessMetric(
                        company_id=result.company_id,
                        verification_report_id=report.id,
                        field_name=field.field_name,
                        freshness_score=field.freshness_score,
                        freshness_status=field.freshness_status.value,
                        scope="field",
                    )
                )
                self.session.add(
                    TrustScore(
                        company_id=result.company_id,
                        verification_report_id=report.id,
                        scope="field",
                        field_name=field.field_name,
                        source=field.source,
                        trust_score=field.trust_score,
                        details={
                            "confirmed_by": field.confirmed_by,
                            "conflicting_sources": field.conflicting_sources,
                            "is_canonical": field.is_canonical,
                        },
                    )
                )
                self.session.add(
                    FieldStatistic(
                        company_id=result.company_id,
                        verification_report_id=report.id,
                        field_name=field.field_name,
                        present=field.value not in (None, "", [], {}),
                        confidence=field.confidence,
                        freshness_score=field.freshness_score,
                        trust_score=field.trust_score,
                        verification_status=field.verification_status.value,
                        source_count=1 + len(field.confirmed_by) + len(field.conflicting_sources),
                    )
                )

        for connector in result.connector_statistics:
            self.session.add(
                ConnectorStatisticRow(
                    company_id=result.company_id,
                    verification_report_id=report.id,
                    connector=connector.connector,
                    success_rate=connector.success_rate,
                    average_latency_ms=connector.average_latency_ms,
                    failure_rate=connector.failure_rate,
                    coverage=connector.coverage,
                    fields_returned=connector.fields_returned,
                    average_confidence=connector.average_confidence,
                    companies_enriched=connector.companies_enriched,
                )
            )

        self.session.add(
            VerificationHistory(
                company_id=result.company_id,
                verification_report_id=report.id,
                enrichment_report_id=result.enrichment_report_id,
                action="verification_created",
                actor="data_verification",
                details={
                    "decision": result.decision.value,
                    "overall_readiness": result.overall_readiness,
                    "automatic_actions": [action.value for action in result.automatic_actions],
                },
            )
        )
        for action in result.automatic_actions:
            if action == AutomaticAction.NONE:
                continue
            self.session.add(
                VerificationHistory(
                    company_id=result.company_id,
                    verification_report_id=report.id,
                    enrichment_report_id=result.enrichment_report_id,
                    action=action.value,
                    actor="data_verification",
                    details={"reason_codes": result.reason_codes},
                )
            )

        await self.session.flush()
        return report.id

    async def latest_report_for_company(self, company_id: UUID) -> VerificationReport | None:
        result = await self.session.execute(
            select(VerificationReport)
            .where(VerificationReport.company_id == company_id)
            .order_by(VerificationReport.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def latest_report_by_id(self, verification_report_id: UUID) -> VerificationReport | None:
        return await self.session.get(VerificationReport, verification_report_id)

    async def company_payload(self, company_id: UUID) -> dict[str, Any] | None:
        report = await self.latest_report_for_company(company_id)
        if report is None:
            return None
        return self._payload(report)

    async def profile_payload(self, verification_report_id: UUID) -> dict[str, Any] | None:
        report = await self.latest_report_by_id(verification_report_id)
        if report is None:
            return None
        return self._payload(report)

    async def dashboard_metrics(self) -> DashboardMetrics:
        result = await self.session.execute(
            select(VerificationReport).order_by(VerificationReport.created_at.desc()).limit(500)
        )
        reports = list(result.scalars().all())
        seen: set[UUID] = set()
        latest: list[VerificationReport] = []
        for report in reports:
            if report.company_id in seen:
                continue
            seen.add(report.company_id)
            latest.append(report)

        if not latest:
            return DashboardMetrics(
                overall_data_quality=0.0,
                coverage_percent=0.0,
                verification_percent=0.0,
                freshness_percent=0.0,
                average_profile_completeness=0.0,
                connector_leaderboard=[],
                missing_field_distribution={},
                top_missing_fields=[],
                profiles_needing_refresh=0,
                flagged_for_review=0,
                total_verified_profiles=0,
            )

        completeness_rows = await self.session.execute(
            select(ProfileCompleteness).where(
                ProfileCompleteness.verification_report_id.in_([report.id for report in latest])
            )
        )
        completeness_by_report = {
            row.verification_report_id: row.overall_completeness for row in completeness_rows.scalars().all()
        }

        connector_rows = await self.session.execute(
            select(ConnectorStatisticRow).where(
                ConnectorStatisticRow.verification_report_id.in_([report.id for report in latest])
            )
        )
        connector_agg: dict[str, list[ConnectorStatisticRow]] = {}
        for row in connector_rows.scalars().all():
            connector_agg.setdefault(row.connector, []).append(row)

        leaderboard: list[ConnectorStatistic] = []
        for connector, rows in connector_agg.items():
            count = len(rows)
            leaderboard.append(
                ConnectorStatistic(
                    connector=connector,
                    success_rate=round(sum(item.success_rate for item in rows) / count, 2),
                    average_latency_ms=round(sum(item.average_latency_ms for item in rows) / count, 2),
                    failure_rate=round(sum(item.failure_rate for item in rows) / count, 2),
                    coverage=round(sum(item.coverage for item in rows) / count, 2),
                    fields_returned=sum(item.fields_returned for item in rows),
                    average_confidence=round(sum(item.average_confidence for item in rows) / count, 2),
                    companies_enriched=sum(item.companies_enriched for item in rows),
                )
            )
        leaderboard.sort(key=lambda item: (item.success_rate, item.average_confidence), reverse=True)

        missing_counter: Counter[str] = Counter()
        for report in latest:
            for field in report.missing_fields or []:
                missing_counter[str(field)] += 1

        profiles_needing_refresh = sum(
            1
            for report in latest
            if report.decision in {"needs_refresh", "incomplete"}
            or "schedule_enrichment_refresh" in (report.automatic_actions or [])
            or "queue_reenrichment" in (report.automatic_actions or [])
        )
        flagged = sum(1 for report in latest if report.decision == "needs_review")

        n = len(latest)
        return DashboardMetrics(
            overall_data_quality=round(sum(report.overall_data_quality for report in latest) / n, 2),
            coverage_percent=round(sum(report.coverage_percent for report in latest) / n, 2),
            verification_percent=round(sum(report.verification_percent for report in latest) / n, 2),
            freshness_percent=round(sum(report.freshness_score for report in latest) / n, 2),
            average_profile_completeness=round(
                sum(completeness_by_report.get(report.id, report.coverage_percent) for report in latest) / n,
                2,
            ),
            connector_leaderboard=leaderboard[:20],
            missing_field_distribution=dict(missing_counter.most_common(50)),
            top_missing_fields=[name for name, _count in missing_counter.most_common(10)],
            profiles_needing_refresh=profiles_needing_refresh,
            flagged_for_review=flagged,
            total_verified_profiles=n,
        )

    async def connector_leaderboard(self) -> list[ConnectorStatistic]:
        metrics = await self.dashboard_metrics()
        return list(metrics.connector_leaderboard)

    async def companies_needing_enrichment_refresh(self, *, limit: int = 50) -> Sequence[UUID]:
        result = await self.session.execute(
            select(VerificationReport)
            .order_by(VerificationReport.created_at.desc())
            .limit(500)
        )
        seen: set[UUID] = set()
        company_ids: list[UUID] = []
        for report in result.scalars().all():
            if report.company_id in seen:
                continue
            seen.add(report.company_id)
            actions = set(report.automatic_actions or [])
            if actions.intersection(
                {
                    AutomaticAction.SCHEDULE_ENRICHMENT_REFRESH.value,
                    AutomaticAction.QUEUE_REENRICHMENT.value,
                }
            ):
                company_ids.append(report.company_id)
            if len(company_ids) >= limit:
                break
        return company_ids

    def _payload(self, report: VerificationReport) -> dict[str, Any]:
        payload = dict(report.result_payload or {})
        payload.update(
            {
                "verification_report_id": str(report.id),
                "created_at": report.created_at.isoformat(),
                "overall_readiness": report.overall_readiness,
                "overall_data_quality": report.overall_data_quality,
                "decision": report.decision,
            }
        )
        return payload

    async def _sources(self, enrichment_report_id: UUID) -> Sequence[dict[str, Any]]:
        result = await self.session.execute(
            select(EnrichmentSource).where(EnrichmentSource.enrichment_report_id == enrichment_report_id)
        )
        return [
            {
                "source": row.source,
                "source_url": row.source_url,
                "fields": list(row.fields or []),
                "confidence": row.confidence,
                "licensed": row.licensed,
            }
            for row in result.scalars().all()
        ]

    async def _timeline_count(self, company_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count(CompanyTimeline.id)).where(CompanyTimeline.company_id == company_id)
        )
        return int(result.scalar_one() or 0)
