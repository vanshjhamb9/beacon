import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.models.quality import QualityFeedback, QualityMetric, QualityReport, QualityRule
from app.models.raw_event import RawEvent, RawEventStatus
from app.repositories.quality import QualityRepository
from quality_engine import QualityDecision, QualityEvent, QualityPipeline, default_rule_catalog

logger = logging.getLogger(__name__)


class QualityService:
    def __init__(self, repository: QualityRepository, pipeline: QualityPipeline | None = None) -> None:
        self.repository = repository
        self.pipeline = pipeline

    async def process_raw_event(self, raw_event: RawEvent) -> QualityReport:
        source_profile = await self.repository.source_profile(raw_event.source)
        pipeline = self.pipeline or QualityPipeline(rules=await self.repository.active_rule_catalog())
        report = pipeline.process(
            QualityEvent(
                id=raw_event.id,
                source=raw_event.source,
                url=raw_event.url,
                title=raw_event.title,
                content=raw_event.content,
                published_at=raw_event.published_at,
                collected_at=raw_event.created_at,
                metadata=raw_event.event_metadata,
                event_hash=raw_event.event_hash,
            ),
            source_profile=source_profile,
            recent_hashes=await self.repository.recent_content_hashes(raw_event.source),
            recent_fingerprints=await self.repository.recent_fingerprints(raw_event.source),
            processed_urls=await self.repository.processed_urls(raw_event.source),
        )
        model = await self.repository.store_report(report)
        if report.decision == QualityDecision.REJECT:
            raw_event.status = RawEventStatus.REJECTED
        logger.info(
            "Quality processed raw event",
            extra={
                "extra": {
                    "raw_event_id": str(raw_event.id),
                    "quality_report_id": str(model.id),
                    "decision": report.decision.value,
                    "quality": report.overall_quality_score,
                }
            },
        )
        return model

    async def ensure_rules_seeded(self) -> None:
        existing_rules = await self.repository.quality_rules()
        if existing_rules:
            return
        await self.repository.sync_rules(default_rule_catalog())

    async def list_reports(
        self,
        *,
        decision: str | None,
        limit: int,
        offset: int,
    ) -> list[QualityReport]:
        return list(await self.repository.list_reports(decision=decision, limit=limit, offset=offset))

    async def report_detail(self, report_id: UUID) -> tuple[QualityReport | None, list[QualityMetric]]:
        report = await self.repository.get_report(report_id)
        if report is None:
            return None, []
        return report, list(await self.repository.metrics_for_report(report.id))

    async def latest_event_report(self, event_id: UUID) -> tuple[QualityReport | None, list[QualityMetric]]:
        report = await self.repository.latest_report_for_event(event_id)
        if report is None:
            return None, []
        return report, list(await self.repository.metrics_for_report(report.id))

    async def statistics(self) -> dict[str, object]:
        since = datetime.now(UTC) - timedelta(days=1)
        stats = await self.repository.statistics(since=since)
        return {
            **stats,
            "window": "24h",
            "source_rankings": await self.repository.source_rankings(since=since),
        }

    async def dashboard(self) -> dict[str, object]:
        since = datetime.now(UTC) - timedelta(days=1)
        stats = await self.repository.statistics(since=since)
        rankings = await self.repository.source_rankings(since=since)
        lowest_quality = sorted(rankings, key=lambda item: float(item["average_quality"]))[:10]
        top_spam = sorted(rankings, key=lambda item: float(item["spam_percent"]), reverse=True)[:10]
        return {
            "signals_today": stats["signals"],
            "accepted": stats["accepted"],
            "rejected": stats["rejected"],
            "spam_percent": stats["spam_percent"],
            "duplicate_percent": stats["duplicate_percent"],
            "average_quality": stats["average_quality"],
            "collector_ranking": rankings,
            "source_ranking": rankings,
            "rule_performance": await self.rule_performance(),
            "pipeline_latency_ms": stats["average_processing_time_ms"],
            "top_spam_sources": top_spam,
            "lowest_quality_sources": lowest_quality,
            "trend_graphs": {"quality_24h": rankings},
        }

    async def sources(self) -> list[dict[str, object]]:
        since = datetime.now(UTC) - timedelta(days=30)
        return await self.repository.source_rankings(since=since)

    async def rule_performance(self) -> list[dict[str, object]]:
        rules = await self.repository.quality_rules()
        return [
            {
                "rule_key": rule.rule_key,
                "version": rule.version,
                "category": rule.category,
                "enabled": rule.enabled,
                "threshold": rule.threshold,
                "priority": rule.priority,
            }
            for rule in rules
        ]

    async def rules(self) -> list[QualityRule]:
        return list(await self.repository.quality_rules())

    async def review(
        self,
        *,
        quality_report_id: UUID,
        reviewer: str,
        review_outcome: str,
        corrected_decision: str | None,
        corrected_reason_codes: list[str],
        notes: str | None,
    ) -> QualityFeedback:
        report = await self.repository.get_report(quality_report_id)
        if report is None:
            raise LookupError("Quality report was not found.")
        return await self.repository.add_feedback(
            quality_report=report,
            reviewer=reviewer,
            review_outcome=review_outcome,
            corrected_decision=corrected_decision,
            corrected_reason_codes=corrected_reason_codes,
            notes=notes,
        )

