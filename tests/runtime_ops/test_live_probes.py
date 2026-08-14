"""Runtime ops integration-ish tests against live Redis/Postgres when available."""

from __future__ import annotations

import os

import pytest
import redis

from runtime_ops.migrations.validator import MigrationValidator
from runtime_ops.redis.validator import RedisStreamsValidator

pytestmark = pytest.mark.skipif(
    os.getenv("BEACON_RUNTIME_OPS_LIVE", "1") != "1",
    reason="Set BEACON_RUNTIME_OPS_LIVE=0 to skip live probes",
)


def test_live_redis_streams_validation():
    client = redis.Redis(host=os.getenv("REDIS_HOST", "127.0.0.1"), port=int(os.getenv("REDIS_PORT", "6379")), decode_responses=True)
    try:
        client.ping()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Redis unavailable: {exc}")
    result = RedisStreamsValidator().validate_sync(client)
    assert result.version is not None
    if result.major and result.major >= 7:
        assert result.ok is True
        assert result.streams_ok is True
        assert result.consumer_groups_ok is True
    else:
        assert result.ok is False


def test_live_postgres_migration_head():
    try:
        import psycopg
    except ImportError:
        pytest.skip("psycopg not installed")

    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    try:
        with psycopg.connect(
            host=host,
            dbname=os.getenv("POSTGRES_DB", "beacon"),
            user=os.getenv("POSTGRES_USER", "beacon"),
            password=os.getenv("POSTGRES_PASSWORD", "beacon_password"),
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version")
                current = cur.fetchone()[0]
                cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
                tables = [r[0] for r in cur.fetchall()]
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Postgres unavailable: {exc}")

    result = MigrationValidator().evaluate(current_revision=current, existing_tables=tables)
    assert current == "20260724_0031"
    assert result.ok is True
    assert not result.missing_tables
