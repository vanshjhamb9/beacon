from __future__ import annotations

import time
from typing import Any

from runtime_ops.models.types import RedisValidationResult

MIN_MAJOR = 7
PROBE_STREAM = "beacon:runtime_ops:probe"
PROBE_GROUP = "runtime_ops_probe_cg"


class RedisStreamsValidator:
    """Fail-fast Redis Streams capability checks (compose-only)."""

    def __init__(self, *, min_major: int = MIN_MAJOR) -> None:
        self.min_major = min_major

    def validate_sync(self, client: Any) -> RedisValidationResult:
        errors: list[str] = []
        evidence: list[str] = []
        version: str | None = None
        major: int | None = None
        streams_ok = False
        groups_ok = False
        pubsub_ok = False
        latency_ms: float | None = None

        started = time.perf_counter()
        try:
            pong = client.ping()
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            evidence.append(f"ping:{pong}")
        except Exception as exc:  # noqa: BLE001 — operational probe
            errors.append(f"ping_failed:{exc}")
            return RedisValidationResult(ok=False, errors=errors, evidence=evidence)

        try:
            info = client.info("server")
            version = str(info.get("redis_version") or "")
            major = int(version.split(".")[0]) if version else None
            evidence.append(f"redis_version:{version}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"info_failed:{exc}")

        if major is None or major < self.min_major:
            errors.append(
                f"unsupported_redis_version:{version or 'unknown'}; require>={self.min_major}.x"
            )

        try:
            client.delete(PROBE_STREAM)
            stream_id = client.xadd(PROBE_STREAM, {"probe": "1", "ts": str(time.time())})
            evidence.append(f"xadd:{stream_id}")
            streams_ok = True
        except Exception as exc:  # noqa: BLE001
            errors.append(f"xadd_failed:{exc}")

        if streams_ok:
            try:
                try:
                    client.xgroup_create(PROBE_STREAM, PROBE_GROUP, id="0", mkstream=True)
                except Exception as create_exc:  # noqa: BLE001
                    if "BUSYGROUP" not in str(create_exc):
                        raise
                messages = client.xreadgroup(
                    PROBE_GROUP,
                    "runtime-ops-probe",
                    {PROBE_STREAM: ">"},
                    count=1,
                )
                groups_ok = True
                evidence.append(f"xreadgroup_messages:{len(messages or [])}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"consumer_group_failed:{exc}")

        try:
            receivers = int(client.publish("beacon:runtime_ops:ping", "probe") or 0)
            pubsub_ok = True
            evidence.append(f"pubsub_receivers:{receivers}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"pubsub_failed:{exc}")

        ok = (
            not errors
            and streams_ok
            and groups_ok
            and pubsub_ok
            and major is not None
            and major >= self.min_major
        )
        return RedisValidationResult(
            ok=ok,
            version=version,
            major=major,
            streams_ok=streams_ok,
            consumer_groups_ok=groups_ok,
            pubsub_ok=pubsub_ok,
            latency_ms=latency_ms,
            errors=errors,
            evidence=evidence,
        )

    async def validate_async(self, client: Any) -> RedisValidationResult:
        errors: list[str] = []
        evidence: list[str] = []
        version: str | None = None
        major: int | None = None
        streams_ok = False
        groups_ok = False
        pubsub_ok = False
        latency_ms: float | None = None

        started = time.perf_counter()
        try:
            pong = await client.ping()
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            evidence.append(f"ping:{pong}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"ping_failed:{exc}")
            return RedisValidationResult(ok=False, errors=errors, evidence=evidence)

        try:
            info = await client.info("server")
            version = str(info.get("redis_version") or "")
            major = int(version.split(".")[0]) if version else None
            evidence.append(f"redis_version:{version}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"info_failed:{exc}")

        if major is None or major < self.min_major:
            errors.append(
                f"unsupported_redis_version:{version or 'unknown'}; require>={self.min_major}.x"
            )

        try:
            await client.delete(PROBE_STREAM)
            stream_id = await client.xadd(PROBE_STREAM, {"probe": "1", "ts": str(time.time())})
            evidence.append(f"xadd:{stream_id}")
            streams_ok = True
        except Exception as exc:  # noqa: BLE001
            errors.append(f"xadd_failed:{exc}")

        if streams_ok:
            try:
                try:
                    await client.xgroup_create(PROBE_STREAM, PROBE_GROUP, id="0", mkstream=True)
                except Exception as create_exc:  # noqa: BLE001
                    if "BUSYGROUP" not in str(create_exc):
                        raise
                messages = await client.xreadgroup(
                    PROBE_GROUP,
                    "runtime-ops-probe",
                    {PROBE_STREAM: ">"},
                    count=1,
                )
                groups_ok = True
                evidence.append(f"xreadgroup_messages:{len(messages or [])}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"consumer_group_failed:{exc}")

        try:
            receivers = int(await client.publish("beacon:runtime_ops:ping", "probe") or 0)
            pubsub_ok = True
            evidence.append(f"pubsub_receivers:{receivers}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"pubsub_failed:{exc}")

        ok = (
            not errors
            and streams_ok
            and groups_ok
            and pubsub_ok
            and major is not None
            and major >= self.min_major
        )
        return RedisValidationResult(
            ok=ok,
            version=version,
            major=major,
            streams_ok=streams_ok,
            consumer_groups_ok=groups_ok,
            pubsub_ok=pubsub_ok,
            latency_ms=latency_ms,
            errors=errors,
            evidence=evidence,
        )
