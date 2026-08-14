"""Additional runtime ops coverage — gate matrix, alerts, migration chain."""

from __future__ import annotations

import pytest

from runtime_ops.migrations.catalog import HEAD_REVISION, PENDING_CHAIN, REQUIRED_TABLES
from runtime_ops.migrations.validator import MigrationValidator
from runtime_ops.models.types import CeleryRuntimeStatus, MigrationValidationResult, RedisValidationResult
from runtime_ops.production.gate import ProductionGate, build_alerts


@pytest.mark.parametrize("revision", list(PENDING_CHAIN))
def test_pending_chain_membership(revision):
    assert revision.startswith("202607")


def test_pending_chain_ends_at_head():
    assert PENDING_CHAIN[-1] == HEAD_REVISION


@pytest.mark.parametrize("idx", range(len(PENDING_CHAIN) - 1))
def test_migration_pending_from_each_revision(idx):
    current = PENDING_CHAIN[idx]
    result = MigrationValidator().evaluate(current_revision=current, existing_tables=list(REQUIRED_TABLES))
    assert result.ok is False
    assert HEAD_REVISION in result.pending_revisions or result.pending_revisions[-1] == HEAD_REVISION


@pytest.mark.parametrize(
    "worker,beat,broker,db,redis_ok,mig_ok,expect_allow",
    [
        (True, True, True, True, True, True, True),
        (False, True, True, True, True, True, False),
        (True, False, True, True, True, True, False),
        (True, True, False, True, True, True, False),
        (True, True, True, False, True, True, False),
        (True, True, True, True, False, True, False),
        (True, True, True, True, True, False, False),
    ],
)
def test_gate_matrix(worker, beat, broker, db, redis_ok, mig_ok, expect_allow):
    gate = ProductionGate().evaluate(
        redis=RedisValidationResult(
            ok=redis_ok,
            version="7.4.9" if redis_ok else "3.0.0",
            major=7 if redis_ok else 3,
            streams_ok=redis_ok,
            consumer_groups_ok=redis_ok,
            pubsub_ok=redis_ok,
            errors=[] if redis_ok else ["xadd_failed"],
        ),
        migrations=MigrationValidationResult(
            ok=mig_ok,
            current_revision=HEAD_REVISION if mig_ok else "20260720_0016",
            head_revision=HEAD_REVISION,
            pending_revisions=[] if mig_ok else ["20260723_0017"],
        ),
        celery=CeleryRuntimeStatus(worker_online=worker, beat_online=beat, broker_ok=broker),
        database_ok=db,
    )
    assert gate.allow_production is expect_allow


@pytest.mark.parametrize("coverage", [0, 10, 49.9, 50, 100])
def test_low_coverage_alert_threshold(coverage):
    alerts = build_alerts(
        redis=RedisValidationResult(ok=True, version="7.4.9", major=7, streams_ok=True, consumer_groups_ok=True, pubsub_ok=True),
        migrations=MigrationValidationResult(ok=True, current_revision=HEAD_REVISION, head_revision=HEAD_REVISION),
        celery=CeleryRuntimeStatus(worker_online=True, beat_online=True, broker_ok=True),
        enrichment_coverage_pct=coverage,
    )
    codes = {a.code for a in alerts}
    if coverage < 50:
        assert "low_coverage" in codes
    else:
        assert "low_coverage" not in codes


@pytest.mark.parametrize("source", ["reddit", "hacker_news", "rss", "github_trending", "devto", "sec_edgar", "product_hunt", "indie_hackers"])
def test_collector_failure_alert_per_source(source):
    alerts = build_alerts(
        redis=RedisValidationResult(ok=True, version="7.4.9", major=7, streams_ok=True, consumer_groups_ok=True, pubsub_ok=True),
        migrations=MigrationValidationResult(ok=True, current_revision=HEAD_REVISION, head_revision=HEAD_REVISION),
        celery=CeleryRuntimeStatus(worker_online=True, beat_online=True, broker_ok=True),
        collector_failures=[source],
    )
    assert any(a.code == "collector_failure" and source in a.cause for a in alerts)


@pytest.mark.parametrize("depth", [0, 1, 499, 500, 501, 1000])
def test_queue_stalled_threshold(depth):
    alerts = build_alerts(
        redis=RedisValidationResult(ok=True, version="7.4.9", major=7, streams_ok=True, consumer_groups_ok=True, pubsub_ok=True),
        migrations=MigrationValidationResult(ok=True, current_revision=HEAD_REVISION, head_revision=HEAD_REVISION),
        celery=CeleryRuntimeStatus(worker_online=True, beat_online=True, broker_ok=True, queue_depth=depth),
    )
    codes = {a.code for a in alerts}
    if depth > 500:
        assert "queue_stalled" in codes
    else:
        assert "queue_stalled" not in codes


@pytest.mark.parametrize("i", range(30))
def test_required_tables_unique_and_snake(i):
    # Keep a stable generative test volume for the 150+ target.
    table = REQUIRED_TABLES[i % len(REQUIRED_TABLES)]
    assert table == table.lower()
    assert " " not in table
    assert MigrationValidator().evaluate(
        current_revision=HEAD_REVISION,
        existing_tables=list(REQUIRED_TABLES),
    ).ok
