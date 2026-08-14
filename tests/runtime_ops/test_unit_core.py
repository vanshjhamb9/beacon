"""Runtime ops unit tests — Redis, migrations, pipeline, gate, reports."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from runtime_ops.celery_probe import CeleryRuntimeProbe
from runtime_ops.migrations.catalog import HEAD_REVISION, REQUIRED_TABLES
from runtime_ops.migrations.validator import MigrationValidator
from runtime_ops.models.types import (
    AlertSeverity,
    CeleryRuntimeStatus,
    HealthTone,
    MigrationValidationResult,
    RedisValidationResult,
    RuntimeOpsSnapshot,
)
from runtime_ops.pipeline.auditor import STAGE_SPECS, PipelineStageAuditor
from runtime_ops.production.gate import ProductionGate, build_alerts
from runtime_ops.redis.validator import RedisStreamsValidator
from runtime_ops.reports.builder import RuntimeOpsReportBuilder


class FakeRedisOK:
    def ping(self):
        return True

    def info(self, section):
        return {"redis_version": "7.4.9"}

    def delete(self, key):
        return 1

    def xadd(self, key, fields):
        return "1-0"

    def xgroup_create(self, *args, **kwargs):
        return True

    def xreadgroup(self, *args, **kwargs):
        return [["stream", [("1-0", {"probe": "1"})]]]

    def publish(self, channel, message):
        return 0


class FakeRedisOld:
    def ping(self):
        return True

    def info(self, section):
        return {"redis_version": "3.0.504"}

    def delete(self, key):
        return 1

    def xadd(self, key, fields):
        raise Exception("unknown command 'XADD'")

    def xgroup_create(self, *args, **kwargs):
        raise Exception("unknown command")

    def xreadgroup(self, *args, **kwargs):
        raise Exception("unknown command")

    def publish(self, channel, message):
        return 0


@pytest.mark.parametrize("version", ["7.0.0", "7.2.5", "7.4.9", "8.0.0"])
def test_redis_validator_accepts_modern_versions(version):
    client = FakeRedisOK()
    client.info = lambda section: {"redis_version": version}
    result = RedisStreamsValidator().validate_sync(client)
    assert result.ok is True
    assert result.streams_ok is True
    assert result.consumer_groups_ok is True
    assert result.pubsub_ok is True


def test_redis_validator_rejects_redis3():
    result = RedisStreamsValidator().validate_sync(FakeRedisOld())
    assert result.ok is False
    assert any("unsupported_redis_version" in e or "xadd_failed" in e for e in result.errors)


def test_redis_validator_ping_failure():
    class Boom:
        def ping(self):
            raise ConnectionError("refused")

    result = RedisStreamsValidator().validate_sync(Boom())
    assert result.ok is False
    assert result.errors


@pytest.mark.parametrize(
    "current,missing_ok",
    [
        (HEAD_REVISION, True),
        ("20260720_0016", False),
        (None, False),
        ("20260723_0017", False),
    ],
)
def test_migration_validator_head(current, missing_ok):
    tables = list(REQUIRED_TABLES)
    result = MigrationValidator().evaluate(current_revision=current, existing_tables=tables)
    assert result.ok is missing_ok
    assert result.head_revision == HEAD_REVISION


def test_migration_validator_missing_tables():
    result = MigrationValidator().evaluate(
        current_revision=HEAD_REVISION,
        existing_tables=["companies", "raw_events"],
    )
    assert result.ok is False
    assert "revenue_hunter_dossiers" in result.missing_tables


@pytest.mark.parametrize("table", list(REQUIRED_TABLES))
def test_required_table_catalog_contains(table):
    assert isinstance(table, str)
    assert table


def test_pipeline_auditor_stages_count():
    counts = {
        "companies": 207,
        "raw_events": 355,
        "opportunities": 213,
        "enrichment_reports": 7,
        "verification_reports": 7,
        "decision_reports": 7,
        "aip_profiles": 0,
        "target_accounts": 40,
        "hunter_dossiers": 0,
        "sales_intelligence_snapshots": 0,
        "campaigns": 0,
        "communication_messages": 1,
        "founder_tasks": 0,
        "roip_metrics": 0,
    }
    stages = PipelineStageAuditor().audit(counts)
    assert len(stages) == len(STAGE_SPECS)
    collection = next(s for s in stages if s.stage == "collection")
    assert collection.input_count == 207
    enrich = next(s for s in stages if s.stage == "enrichment")
    assert enrich.success_percent < 50
    assert enrich.status in {HealthTone.WARNING, HealthTone.FAIL}


@pytest.mark.parametrize("stage_name,task", list(STAGE_SPECS))
def test_stage_specs_named(stage_name, task):
    assert stage_name
    assert "." in task


def test_celery_probe_offline():
    status = CeleryRuntimeProbe().probe(broker_ok=True, queue_depth=0, inspect_payload={})
    assert status.worker_online is False


def test_celery_probe_online():
    status = CeleryRuntimeProbe().probe(
        broker_ok=True,
        queue_depth=3,
        inspect_payload={
            "ping": {"w1": {"ok": "pong"}},
            "active": {"w1": [{"id": "1"}]},
            "scheduled": {"w1": []},
            "registered": {"w1": ["a", "b", "c"]},
            "stats": {"w1": {"rusage": {"maxrss": 204800}}},
        },
        beat_schedule_count=69,
        heartbeat_key_ttl_ok=True,
    )
    assert status.worker_online is True
    assert status.beat_online is True
    assert status.active_tasks == 1
    assert status.registered_task_count == 3


def test_production_gate_blocks_on_redis():
    gate = ProductionGate().evaluate(
        redis=RedisValidationResult(ok=False, errors=["xadd_failed"]),
        migrations=MigrationValidationResult(ok=True, head_revision=HEAD_REVISION, current_revision=HEAD_REVISION),
        celery=CeleryRuntimeStatus(worker_online=True, beat_online=True, broker_ok=True),
        database_ok=True,
    )
    assert gate.allow_production is False
    assert "redis_streams_unsupported_or_unavailable" in gate.blockers


def test_production_gate_blocks_worker_offline():
    gate = ProductionGate().evaluate(
        redis=RedisValidationResult(ok=True, streams_ok=True, consumer_groups_ok=True, pubsub_ok=True, version="7.4.9", major=7),
        migrations=MigrationValidationResult(ok=True, head_revision=HEAD_REVISION, current_revision=HEAD_REVISION),
        celery=CeleryRuntimeStatus(worker_online=False, beat_online=True, broker_ok=True),
        database_ok=True,
    )
    assert gate.allow_production is False
    assert "worker_offline" in gate.blockers


def test_production_gate_blocks_beat_offline():
    gate = ProductionGate().evaluate(
        redis=RedisValidationResult(ok=True, streams_ok=True, consumer_groups_ok=True, pubsub_ok=True, version="7.4.9", major=7),
        migrations=MigrationValidationResult(ok=True, head_revision=HEAD_REVISION, current_revision=HEAD_REVISION),
        celery=CeleryRuntimeStatus(worker_online=True, beat_online=False, broker_ok=True),
        database_ok=True,
    )
    assert "beat_offline" in gate.blockers


def test_production_gate_blocks_pending_migrations():
    gate = ProductionGate().evaluate(
        redis=RedisValidationResult(ok=True, streams_ok=True, consumer_groups_ok=True, pubsub_ok=True, version="7.4.9", major=7),
        migrations=MigrationValidationResult(
            ok=False,
            head_revision=HEAD_REVISION,
            current_revision="20260720_0016",
            pending_revisions=["20260723_0017"],
        ),
        celery=CeleryRuntimeStatus(worker_online=True, beat_online=True, broker_ok=True),
        database_ok=True,
    )
    assert "pending_or_incomplete_migrations" in gate.blockers


def test_production_gate_pass():
    gate = ProductionGate().evaluate(
        redis=RedisValidationResult(ok=True, streams_ok=True, consumer_groups_ok=True, pubsub_ok=True, version="7.4.9", major=7),
        migrations=MigrationValidationResult(ok=True, head_revision=HEAD_REVISION, current_revision=HEAD_REVISION),
        celery=CeleryRuntimeStatus(worker_online=True, beat_online=True, broker_ok=True),
        database_ok=True,
    )
    assert gate.allow_production is True
    assert gate.score >= 95


def test_build_alerts_codes():
    alerts = build_alerts(
        redis=RedisValidationResult(ok=False, errors=["x"]),
        migrations=MigrationValidationResult(ok=False, head_revision=HEAD_REVISION),
        celery=CeleryRuntimeStatus(worker_online=False, beat_online=False, broker_ok=True, queue_depth=600),
        enrichment_coverage_pct=3.0,
        collector_failures=["indie_hackers"],
    )
    codes = {a.code for a in alerts}
    assert "worker_offline" in codes
    assert "beat_offline" in codes
    assert "redis_streams_unsupported" in codes
    assert "pending_migration" in codes
    assert "collector_failure" in codes
    assert "low_coverage" in codes
    assert "queue_stalled" in codes
    assert all(isinstance(a.severity, AlertSeverity) for a in alerts)


def _sample_snapshot(**overrides):
    base = RuntimeOpsSnapshot(
        generated_at=datetime.now(UTC),
        redis=RedisValidationResult(ok=True, version="7.4.9", major=7, streams_ok=True, consumer_groups_ok=True, pubsub_ok=True, latency_ms=1.2),
        migrations=MigrationValidationResult(ok=True, current_revision=HEAD_REVISION, head_revision=HEAD_REVISION),
        celery=CeleryRuntimeStatus(worker_online=True, beat_online=True, broker_ok=True, queue_depth=0, scheduled_tasks=69),
        production_gate=ProductionGate().evaluate(
            redis=RedisValidationResult(ok=True, version="7.4.9", major=7, streams_ok=True, consumer_groups_ok=True, pubsub_ok=True),
            migrations=MigrationValidationResult(ok=True, current_revision=HEAD_REVISION, head_revision=HEAD_REVISION),
            celery=CeleryRuntimeStatus(worker_online=True, beat_online=True, broker_ok=True),
            database_ok=True,
        ),
        readiness_score=100.0,
        enrichment={"coverage_pct": 80.0, "opportunities": 10, "enrichment_reports": 8},
        freshness={"last_collection": datetime.now(UTC).isoformat()},
        collectors=[{"source": "reddit", "health_status": "HEALTHY"}],
        pipeline=PipelineStageAuditor().audit({"companies": 10, "raw_events": 10, "opportunities": 10, "enrichment_reports": 10, "verification_reports": 10, "decision_reports": 10, "aip_profiles": 10, "target_accounts": 10, "hunter_dossiers": 10, "sales_intelligence_snapshots": 10, "campaigns": 10, "communication_messages": 10, "founder_tasks": 10, "roip_metrics": 10}),
    )
    return base.model_copy(update=overrides)


@pytest.mark.parametrize(
    "report_key",
    [
        "platform_health",
        "infrastructure",
        "collectors",
        "pipeline",
        "migrations",
        "coverage",
        "freshness",
        "performance",
        "production_readiness",
    ],
)
def test_report_builder_keys(report_key):
    reports = RuntimeOpsReportBuilder().build_all(_sample_snapshot())
    assert report_key in reports
    assert "Status:" in reports[report_key]
    assert "Evidence" in reports[report_key]
    assert "Recommendations" in reports[report_key]


@pytest.mark.parametrize("n", list(range(40)))
def test_pipeline_success_math(n):
    entering = n + 1
    leaving = n // 2
    stages = PipelineStageAuditor().audit(
        {
            "companies": entering,
            "raw_events": leaving,
            "opportunities": leaving,
            "enrichment_reports": leaving,
            "verification_reports": leaving,
            "decision_reports": leaving,
            "aip_profiles": leaving,
            "target_accounts": leaving,
            "hunter_dossiers": leaving,
            "sales_intelligence_snapshots": leaving,
            "campaigns": leaving,
            "communication_messages": leaving,
            "founder_tasks": leaving,
            "roip_metrics": leaving,
        }
    )
    collection = stages[0]
    expected = round((leaving / entering) * 100.0, 2)
    assert collection.success_percent == expected
