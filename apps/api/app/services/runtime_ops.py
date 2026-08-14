from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.acquisition import CollectorRun
from app.models.enrichment import EnrichmentReport
from app.models.intelligence import Company
from app.models.opportunity import Opportunity
from app.models.source_health import SourceHealth
from app.models.verification import VerificationReport
from runtime_ops.celery_probe import CeleryRuntimeProbe
from runtime_ops.migrations.validator import MigrationValidator
from runtime_ops.models.types import ComponentStatus, HealthTone, RuntimeOpsSnapshot
from runtime_ops.pipeline.auditor import PipelineStageAuditor
from runtime_ops.production.gate import ProductionGate, build_alerts
from runtime_ops.redis.validator import RedisStreamsValidator
from runtime_ops.reports.builder import RuntimeOpsReportBuilder


class RuntimeOpsService:
    """Compose infrastructure + pipeline operational snapshot for System Operations."""

    def __init__(self, session: AsyncSession, redis: Redis, settings: Settings) -> None:
        self.session = session
        self.redis = redis
        self.settings = settings
        self.redis_validator = RedisStreamsValidator()
        self.migration_validator = MigrationValidator()
        self.celery_probe = CeleryRuntimeProbe()
        self.pipeline_auditor = PipelineStageAuditor()
        self.gate = ProductionGate()
        self.report_builder = RuntimeOpsReportBuilder()

    async def snapshot(self, *, inspect_payload: dict[str, Any] | None = None) -> RuntimeOpsSnapshot:
        redis_result = await self.redis_validator.validate_async(self.redis)

        current_revision = await self.session.scalar(text("SELECT version_num FROM alembic_version LIMIT 1"))
        table_rows = (
            await self.session.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
        ).all()
        migrations = self.migration_validator.evaluate_from_rows(
            current_revision=str(current_revision) if current_revision else None,
            table_rows=table_rows,
        )

        broker_ok = False
        queue_depth = 0
        try:
            await self.redis.ping()
            broker_ok = True
            queue_depth = int(await self.redis.llen("celery") or 0)
        except Exception:  # noqa: BLE001
            broker_ok = False

        beat_heartbeat = False
        try:
            beat_heartbeat = bool(await self.redis.exists("beacon:celery:beat:heartbeat"))
        except Exception:  # noqa: BLE001
            beat_heartbeat = False

        last_collector = await self.session.scalar(select(func.max(CollectorRun.created_at)))
        beat_schedule_count = 0
        try:
            from worker.celery_app import celery_app

            beat_schedule_count = len(celery_app.conf.beat_schedule or {})
        except Exception:  # noqa: BLE001
            beat_schedule_count = 0

        celery = self.celery_probe.probe(
            broker_ok=broker_ok,
            queue_depth=queue_depth,
            inspect_payload=inspect_payload or {},
            beat_schedule_count=beat_schedule_count,
            last_collector_run_at=last_collector,
            heartbeat_key_ttl_ok=beat_heartbeat,
        )
        if beat_schedule_count:
            celery.scheduled_tasks = max(celery.scheduled_tasks, beat_schedule_count)
            celery.evidence.append(f"beat_schedule_count:{beat_schedule_count}")

        counts = await self._pipeline_counts()
        pipeline = self.pipeline_auditor.audit(counts, last_runs={"collection": last_collector})

        collectors = await self._collectors()
        enrichment = await self._enrichment_coverage()
        freshness = await self._freshness()

        database_ok = True
        try:
            await self.session.execute(text("SELECT 1"))
        except Exception:  # noqa: BLE001
            database_ok = False

        production_gate = self.gate.evaluate(
            redis=redis_result,
            migrations=migrations,
            celery=celery,
            database_ok=database_ok,
            secrets_ok=True,
            oauth_ok=True,
            pipeline=pipeline,
        )

        failing_collectors = [
            c["source"]
            for c in collectors
            if str(c.get("health_status", "")).lower() in {"down", "degraded"}
        ]
        alerts = build_alerts(
            redis=redis_result,
            migrations=migrations,
            celery=celery,
            enrichment_coverage_pct=float(enrichment.get("coverage_pct") or 0),
            collector_failures=failing_collectors,
        )

        infrastructure = [
            ComponentStatus(
                name="redis",
                status=HealthTone.PASS if redis_result.ok else HealthTone.FAIL,
                detail=redis_result.version,
                metrics={"latency_ms": redis_result.latency_ms, "streams_ok": redis_result.streams_ok},
                evidence=redis_result.evidence,
            ),
            ComponentStatus(
                name="postgres",
                status=HealthTone.PASS if database_ok and migrations.ok else HealthTone.FAIL,
                detail=migrations.current_revision,
                metrics={"pending": len(migrations.pending_revisions)},
                evidence=migrations.evidence,
            ),
            ComponentStatus(
                name="celery_worker",
                status=HealthTone.PASS if celery.worker_online else HealthTone.FAIL,
                metrics={"active_tasks": celery.active_tasks, "queue_depth": celery.queue_depth},
                evidence=celery.evidence,
            ),
            ComponentStatus(
                name="celery_beat",
                status=HealthTone.PASS if celery.beat_online else HealthTone.FAIL,
                metrics={"scheduled_tasks": celery.scheduled_tasks},
                evidence=celery.evidence,
            ),
            ComponentStatus(
                name="api",
                status=HealthTone.PASS,
                detail="reachable",
                evidence=["process:api"],
            ),
        ]

        readiness = production_gate.score
        return RuntimeOpsSnapshot(
            generated_at=datetime.now(UTC),
            infrastructure=infrastructure,
            redis=redis_result,
            migrations=migrations,
            celery=celery,
            pipeline=pipeline,
            collectors=collectors,
            enrichment=enrichment,
            freshness=freshness,
            alerts=alerts,
            production_gate=production_gate,
            readiness_score=readiness,
        )

    async def reports(self) -> dict[str, str]:
        snap = await self.snapshot()
        return self.report_builder.build_all(snap)

    async def _pipeline_counts(self) -> dict[str, Any]:
        async def count(sql: str) -> int:
            return int(await self.session.scalar(text(sql)) or 0)

        return {
            "companies": await count("SELECT COUNT(*) FROM companies WHERE deleted_at IS NULL"),
            "raw_events": await count("SELECT COUNT(*) FROM raw_events WHERE deleted_at IS NULL"),
            "opportunities": await count("SELECT COUNT(*) FROM opportunities WHERE deleted_at IS NULL"),
            "enrichment_reports": await count(
                "SELECT COUNT(*) FROM enrichment_reports WHERE deleted_at IS NULL"
            ),
            "verification_reports": await count(
                "SELECT COUNT(*) FROM verification_reports WHERE deleted_at IS NULL"
            ),
            "decision_reports": await count(
                "SELECT COUNT(*) FROM decision_discovery_reports WHERE deleted_at IS NULL"
            ),
            "aip_profiles": await count(
                "SELECT COUNT(*) FROM aip_account_profiles WHERE deleted_at IS NULL"
            ),
            "target_accounts": await count(
                "SELECT COUNT(*) FROM target_accounts WHERE deleted_at IS NULL"
            ),
            "hunter_dossiers": await count(
                "SELECT COUNT(*) FROM revenue_hunter_dossiers WHERE deleted_at IS NULL"
            ),
            "sales_intelligence_snapshots": await count(
                "SELECT COUNT(*) FROM sales_intelligence_snapshots WHERE deleted_at IS NULL"
            ),
            "campaigns": await count("SELECT COUNT(*) FROM campaigns WHERE deleted_at IS NULL"),
            "communication_messages": await count(
                "SELECT COUNT(*) FROM communication_messages WHERE deleted_at IS NULL"
            ),
            "founder_tasks": await count(
                "SELECT COUNT(*) FROM founder_revenue_tasks WHERE deleted_at IS NULL"
            ),
            "roip_metrics": await count(
                "SELECT COUNT(*) FROM roip_email_metrics WHERE deleted_at IS NULL"
            ),
        }

    async def _collectors(self) -> list[dict[str, Any]]:
        rows = (await self.session.scalars(select(SourceHealth))).all()
        out: list[dict[str, Any]] = []
        for row in rows:
            out.append(
                {
                    "source": row.source,
                    "health_status": str(getattr(row.status, "value", row.status)),
                    "consecutive_failures": row.consecutive_failures,
                    "last_success_at": row.last_success_at.isoformat() if row.last_success_at else None,
                    "last_failure_at": row.last_failure_at.isoformat() if row.last_failure_at else None,
                    "last_error": row.last_error,
                    "average_latency_ms": row.average_latency_ms,
                }
            )
        return out

    async def _enrichment_coverage(self) -> dict[str, Any]:
        companies = int(
            await self.session.scalar(select(func.count()).select_from(Company).where(Company.deleted_at.is_(None)))
            or 0
        )
        opportunities = int(
            await self.session.scalar(
                select(func.count()).select_from(Opportunity).where(Opportunity.deleted_at.is_(None))
            )
            or 0
        )
        enriched = int(
            await self.session.scalar(
                select(func.count()).select_from(EnrichmentReport).where(EnrichmentReport.deleted_at.is_(None))
            )
            or 0
        )
        verified = int(
            await self.session.scalar(
                select(func.count()).select_from(VerificationReport).where(VerificationReport.deleted_at.is_(None))
            )
            or 0
        )
        coverage = 0.0 if opportunities <= 0 else round((enriched / opportunities) * 100.0, 2)
        return {
            "companies": companies,
            "opportunities": opportunities,
            "enrichment_reports": enriched,
            "verification_reports": verified,
            "coverage_pct": coverage,
            "target_pct": 100.0,
        }

    async def _freshness(self) -> dict[str, Any]:
        async def max_ts(table: str) -> str | None:
            value = await self.session.scalar(text(f"SELECT MAX(created_at) FROM {table}"))
            return value.isoformat() if value is not None else None

        return {
            "last_collection": await max_ts("collector_runs"),
            "last_enrichment": await max_ts("enrichment_reports"),
            "last_verification": await max_ts("verification_reports"),
            "last_revenue_hunter": await max_ts("revenue_hunter_dossiers"),
            "last_founder_refresh": await max_ts("founder_daily_briefs"),
        }
