from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quality import (
    QualityAudit,
    QualityFeedback,
    QualityMetric,
    QualityReport,
    QualityRule,
)
from app.models.raw_event import RawEvent
from app.models.source_health import SourceHealth
from quality_engine.models import QualityReportResult, SourceQualityProfile
from quality_engine.rules.definitions import QualityRuleDefinition, RuleCatalog, RuleCategory
from quality_engine.rules.defaults import default_rule_catalog


class QualityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def source_profile(self, source: str) -> SourceQualityProfile:
        since = datetime.now(UTC) - timedelta(days=30)
        result = await self.session.execute(
            select(
                func.count(QualityReport.id),
                func.sum(case((QualityReport.decision == "accept", 1), else_=0)),
                func.sum(case((QualityReport.decision == "reject", 1), else_=0)),
                func.avg(QualityReport.spam_score),
                func.avg(QualityReport.duplicate_probability),
                func.avg(QualityReport.overall_quality_score),
                func.avg(QualityReport.entity_confidence_score),
                func.avg(QualityReport.processing_time_ms),
            ).where(QualityReport.source == source, QualityReport.created_at >= since)
        )
        row = result.one()
        health_result = await self.session.execute(
            select(SourceHealth.status).where(SourceHealth.source == source).limit(1)
        )
        health = health_result.scalar_one_or_none()
        collected = int(row[0] or 0)
        accepted = int(row[1] or 0)
        rejected = int(row[2] or 0)
        return SourceQualityProfile(
            source=source,
            signals_collected=collected,
            signals_accepted=accepted,
            signals_rejected=rejected,
            spam_rate=round(float(row[3] or 0.0) / 100.0, 4),
            duplicate_rate=round(float(row[4] or 0.0) / 100.0, 4),
            average_quality=round(float(row[5] or 75.0), 4),
            average_confidence=round(float(row[6] or 75.0), 4),
            average_processing_time_ms=round(float(row[7] or 0.0), 4),
            collector_health=health.value if health is not None else "unknown",
        )

    async def recent_content_hashes(self, source: str, *, limit: int = 500) -> set[str]:
        result = await self.session.execute(
            select(QualityMetric.details)
            .join(QualityReport, QualityReport.id == QualityMetric.quality_report_id)
            .where(QualityReport.source == source, QualityMetric.stage == "normalization")
            .order_by(QualityMetric.created_at.desc())
            .limit(limit)
        )
        return {
            str(details["content_hash"])
            for details in result.scalars().all()
            if isinstance(details, dict) and details.get("content_hash")
        }

    async def recent_fingerprints(self, source: str, *, limit: int = 500) -> list[str]:
        result = await self.session.execute(
            select(QualityMetric.details)
            .join(QualityReport, QualityReport.id == QualityMetric.quality_report_id)
            .where(QualityReport.source == source, QualityMetric.stage == "normalization")
            .order_by(QualityMetric.created_at.desc())
            .limit(limit)
        )
        return [
            str(details["fingerprint"])
            for details in result.scalars().all()
            if isinstance(details, dict) and details.get("fingerprint")
        ]

    async def processed_urls(self, source: str, *, limit: int = 500) -> set[str]:
        result = await self.session.execute(
            select(RawEvent.url)
            .join(QualityReport, QualityReport.raw_event_id == RawEvent.id)
            .where(QualityReport.source == source)
            .order_by(QualityReport.created_at.desc())
            .limit(limit)
        )
        return {str(url) for url in result.scalars().all()}

    async def store_report(self, report: QualityReportResult) -> QualityReport:
        if report.event_id is None:
            raise ValueError("Quality reports persisted to the database require an event_id.")

        model = QualityReport(
            raw_event_id=report.event_id,
            source=report.source,
            decision=report.decision.value,
            grade=report.grade.value,
            schema_score=report.schema_score,
            spam_score=report.spam_score,
            trust_score=report.trust_score,
            freshness_score=report.freshness_score,
            completeness_score=report.completeness_score,
            entity_confidence_score=report.entity_confidence_score,
            duplicate_probability=report.duplicate_probability,
            overall_quality_score=report.overall_quality_score,
            processing_time_ms=report.processing_time_ms,
            queue_time_ms=report.queue_time_ms,
            reason_codes=report.reason_codes,
            explanation=report.explanation,
        )
        self.session.add(model)
        await self.session.flush()

        for stage in report.stage_results:
            self.session.add(
                QualityMetric(
                    quality_report_id=model.id,
                    raw_event_id=report.event_id,
                    stage=stage.stage.value,
                    metric_name=f"{stage.stage.value}.score",
                    metric_value=stage.score,
                    passed=stage.passed,
                    duration_ms=stage.duration_ms,
                    reason_codes=stage.reason_codes,
                    details=stage.details,
                )
            )

        self.session.add(
            QualityAudit(
                raw_event_id=report.event_id,
                quality_report_id=model.id,
                action="quality_processed",
                actor="quality_engine",
                details={"decision": report.decision.value, "grade": report.grade.value},
            )
        )
        await self.session.flush()
        await self.session.refresh(model)
        return model

    async def sync_rules(self, catalog: RuleCatalog) -> None:
        for rule in catalog.all():
            self.session.add(
                QualityRule(
                    rule_key=rule.key,
                    name=rule.name,
                    category=rule.category.value,
                    version=rule.version,
                    enabled=rule.enabled,
                    priority=rule.priority,
                    threshold=rule.threshold,
                    weight=rule.weight,
                    parameters=rule.parameters,
                )
            )
        await self.session.flush()

    async def latest_report_for_event(self, event_id: UUID) -> QualityReport | None:
        result = await self.session.execute(
            select(QualityReport)
            .where(QualityReport.raw_event_id == event_id)
            .order_by(QualityReport.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_reports(
        self,
        *,
        decision: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[QualityReport]:
        query = select(QualityReport).order_by(QualityReport.created_at.desc())
        if decision:
            query = query.where(QualityReport.decision == decision)
        result = await self.session.execute(query.limit(limit).offset(offset))
        return result.scalars().all()

    async def get_report(self, report_id: UUID) -> QualityReport | None:
        return await self.session.get(QualityReport, report_id)

    async def metrics_for_report(self, report_id: UUID) -> Sequence[QualityMetric]:
        result = await self.session.execute(
            select(QualityMetric)
            .where(QualityMetric.quality_report_id == report_id)
            .order_by(QualityMetric.created_at)
        )
        return result.scalars().all()

    async def quality_rules(self) -> Sequence[QualityRule]:
        result = await self.session.execute(
            select(QualityRule).order_by(QualityRule.rule_key, desc(QualityRule.version))
        )
        return result.scalars().all()

    async def active_rule_catalog(self) -> RuleCatalog:
        rules = await self.quality_rules()
        if not rules:
            return default_rule_catalog()

        latest_by_key: dict[str, QualityRule] = {}
        for rule in rules:
            existing = latest_by_key.get(rule.rule_key)
            if existing is None or rule.version > existing.version:
                latest_by_key[rule.rule_key] = rule

        return RuleCatalog(
            [
                QualityRuleDefinition(
                    key=rule.rule_key,
                    name=rule.name,
                    category=RuleCategory(rule.category),
                    version=rule.version,
                    enabled=rule.enabled,
                    priority=rule.priority,
                    threshold=rule.threshold,
                    weight=rule.weight,
                    parameters=rule.parameters,
                )
                for rule in latest_by_key.values()
            ]
        )

    async def add_feedback(
        self,
        *,
        quality_report: QualityReport,
        reviewer: str,
        review_outcome: str,
        corrected_decision: str | None,
        corrected_reason_codes: list[str],
        notes: str | None,
    ) -> QualityFeedback:
        feedback = QualityFeedback(
            quality_report_id=quality_report.id,
            raw_event_id=quality_report.raw_event_id,
            reviewer=reviewer,
            review_outcome=review_outcome,
            corrected_decision=corrected_decision,
            corrected_reason_codes=corrected_reason_codes,
            notes=notes,
        )
        self.session.add(feedback)
        self.session.add(
            QualityAudit(
                raw_event_id=quality_report.raw_event_id,
                quality_report_id=quality_report.id,
                action="quality_reviewed",
                actor=reviewer,
                details={
                    "review_outcome": review_outcome,
                    "corrected_decision": corrected_decision,
                    "corrected_reason_codes": corrected_reason_codes,
                },
            )
        )
        await self.session.flush()
        await self.session.refresh(feedback)
        return feedback

    async def statistics(self, *, since: datetime) -> dict[str, float | int]:
        result = await self.session.execute(
            select(
                func.count(QualityReport.id),
                func.sum(case((QualityReport.decision == "accept", 1), else_=0)),
                func.sum(case((QualityReport.decision == "reject", 1), else_=0)),
                func.avg(QualityReport.spam_score),
                func.avg(QualityReport.duplicate_probability),
                func.avg(QualityReport.overall_quality_score),
                func.avg(QualityReport.processing_time_ms),
            ).where(QualityReport.created_at >= since)
        )
        row = result.one()
        return {
            "signals": int(row[0] or 0),
            "accepted": int(row[1] or 0),
            "rejected": int(row[2] or 0),
            "spam_percent": round(float(row[3] or 0.0), 4),
            "duplicate_percent": round(float(row[4] or 0.0), 4),
            "average_quality": round(float(row[5] or 0.0), 4),
            "average_processing_time_ms": round(float(row[6] or 0.0), 4),
        }

    async def source_rankings(self, *, since: datetime) -> list[dict[str, object]]:
        result = await self.session.execute(
            select(
                QualityReport.source,
                func.count(QualityReport.id),
                func.avg(QualityReport.overall_quality_score),
                func.avg(QualityReport.spam_score),
                func.avg(QualityReport.duplicate_probability),
            )
            .where(QualityReport.created_at >= since)
            .group_by(QualityReport.source)
            .order_by(func.avg(QualityReport.overall_quality_score).desc())
        )
        return [
            {
                "source": source,
                "signals": int(count),
                "average_quality": round(float(quality or 0.0), 4),
                "spam_percent": round(float(spam or 0.0), 4),
                "duplicate_percent": round(float(duplicate or 0.0), 4),
            }
            for source, count, quality, spam, duplicate in result.all()
        ]
