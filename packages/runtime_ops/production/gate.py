from __future__ import annotations

from datetime import UTC, datetime

from runtime_ops.models.types import (
    AlertSeverity,
    CeleryRuntimeStatus,
    MigrationValidationResult,
    OperationalAlert,
    PipelineStageStatus,
    ProductionGateDecision,
    RedisValidationResult,
)


class ProductionGate:
    """Refuse production mode when critical runtime prerequisites fail."""

    def evaluate(
        self,
        *,
        redis: RedisValidationResult,
        migrations: MigrationValidationResult,
        celery: CeleryRuntimeStatus,
        database_ok: bool,
        secrets_ok: bool = True,
        oauth_ok: bool = True,
        pipeline: list[PipelineStageStatus] | None = None,
        min_score: float = 95.0,
    ) -> ProductionGateDecision:
        blockers: list[str] = []
        warnings: list[str] = []
        evidence: list[str] = []

        if not database_ok:
            blockers.append("database_unavailable")
        if not redis.ok:
            blockers.append("redis_streams_unsupported_or_unavailable")
            evidence.extend(redis.errors)
        if not migrations.ok:
            blockers.append("pending_or_incomplete_migrations")
            if migrations.pending_revisions:
                evidence.append("pending:" + ",".join(migrations.pending_revisions[:8]))
            if migrations.missing_tables:
                evidence.append("missing_tables:" + ",".join(migrations.missing_tables[:8]))
        if not celery.broker_ok:
            blockers.append("broker_unavailable")
        if not celery.worker_online:
            blockers.append("worker_offline")
        if not celery.beat_online:
            blockers.append("beat_offline")
        if not secrets_ok:
            blockers.append("missing_secrets")
        if not oauth_ok:
            warnings.append("oauth_invalid_or_unconfigured")

        pipeline = pipeline or []
        failing_stages = [s.stage for s in pipeline if s.status.value == "fail"]
        if failing_stages:
            warnings.append("pipeline_stage_failures:" + ",".join(failing_stages[:6]))

        # Score: start 100, deduct for blockers/warnings.
        score = 100.0
        score -= 20.0 * len(blockers)
        score -= 5.0 * len(warnings)
        score = max(0.0, min(100.0, score))

        allow = not blockers and score >= min_score
        evidence.extend(
            [
                f"redis_ok:{redis.ok}",
                f"migrations_ok:{migrations.ok}",
                f"worker_online:{celery.worker_online}",
                f"beat_online:{celery.beat_online}",
                f"score:{score}",
            ]
        )
        return ProductionGateDecision(
            allow_production=allow,
            score=round(score, 2),
            blockers=blockers,
            warnings=warnings,
            evidence=evidence,
            checked_at=datetime.now(UTC),
        )


def build_alerts(
    *,
    redis: RedisValidationResult,
    migrations: MigrationValidationResult,
    celery: CeleryRuntimeStatus,
    enrichment_coverage_pct: float | None = None,
    collector_failures: list[str] | None = None,
) -> list[OperationalAlert]:
    alerts: list[OperationalAlert] = []
    if not celery.worker_online:
        alerts.append(
            OperationalAlert(
                code="worker_offline",
                severity=AlertSeverity.CRITICAL,
                cause="Celery worker process is not responding to inspect.ping",
                evidence=celery.evidence,
                recommended_fix="Start worker: scripts\\start-worker.bat",
            )
        )
    if not celery.beat_online:
        alerts.append(
            OperationalAlert(
                code="beat_offline",
                severity=AlertSeverity.CRITICAL,
                cause="Celery Beat is offline or collector schedule is stale",
                evidence=celery.evidence,
                recommended_fix="Start beat+worker: scripts\\start-worker.bat (includes --beat)",
            )
        )
    if not redis.ok:
        alerts.append(
            OperationalAlert(
                code="redis_streams_unsupported",
                severity=AlertSeverity.CRITICAL,
                cause="Redis Streams validation failed",
                evidence=redis.errors + redis.evidence,
                recommended_fix="Run Redis 7.x (scripts\\start-redis.bat) and confirm XADD works",
            )
        )
    if not migrations.ok:
        alerts.append(
            OperationalAlert(
                code="pending_migration",
                severity=AlertSeverity.CRITICAL,
                cause="Alembic not at required head or required tables missing",
                evidence=migrations.evidence,
                recommended_fix=f"cd apps\\api && python -m alembic upgrade head (target {migrations.head_revision})",
            )
        )
    for source in collector_failures or []:
        alerts.append(
            OperationalAlert(
                code="collector_failure",
                severity=AlertSeverity.HIGH,
                cause=f"Collector {source} is failing or down",
                evidence=[f"source:{source}"],
                recommended_fix="Inspect source_health + collector_runs; re-run connector manually",
            )
        )
    if enrichment_coverage_pct is not None and enrichment_coverage_pct < 50.0:
        alerts.append(
            OperationalAlert(
                code="low_coverage",
                severity=AlertSeverity.MEDIUM,
                cause=f"Enrichment coverage {enrichment_coverage_pct:.1f}% below target",
                evidence=[f"enrichment_coverage_pct:{enrichment_coverage_pct}"],
                recommended_fix="Ensure enrichment worker task is scheduled and opportunities qualify for enrichment",
            )
        )
    if celery.queue_depth > 500:
        alerts.append(
            OperationalAlert(
                code="queue_stalled",
                severity=AlertSeverity.HIGH,
                cause=f"Celery queue depth {celery.queue_depth} indicates backlog",
                evidence=[f"queue_depth:{celery.queue_depth}"],
                recommended_fix="Scale workers or inspect failing tasks",
            )
        )
    return alerts
