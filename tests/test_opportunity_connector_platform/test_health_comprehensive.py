"""Comprehensive tests for connector health engine — all edge cases."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from opportunity_connector_platform.connector_health import ConnectorHealthEngine, HealthInput


class TestHealthInputEdgeCases:
    def test_all_defaults(self):
        h = HealthInput()
        assert h.latency_ms == 0.0
        assert h.failures == 0
        assert h.retries == 0
        assert h.authenticated is True
        assert h.rate_limit_remaining is None
        assert h.queue_size == 0
        assert h.freshness_minutes == 0
        assert h.consecutive_failures == 0
        assert h.last_success is None
        assert h.last_failure is None

    def test_all_custom(self):
        now = datetime.now(UTC)
        h = HealthInput(
            latency_ms=500.0, failures=3, retries=1,
            authenticated=True, rate_limit_remaining=100,
            queue_size=50, freshness_minutes=30,
            consecutive_failures=2, last_success=now, last_failure=now,
        )
        assert h.latency_ms == 500.0
        assert h.failures == 3
        assert h.retries == 1
        assert h.authenticated is True
        assert h.rate_limit_remaining == 100
        assert h.queue_size == 50
        assert h.freshness_minutes == 30
        assert h.consecutive_failures == 2
        assert h.last_success == now
        assert h.last_failure == now


class TestHealthEngineComprehensive:
    def test_critical_unauthenticated(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(authenticated=False))
        assert r["status"] == "critical"

    def test_critical_failures_10(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(failures=10))
        assert r["status"] == "critical"

    def test_critical_failures_20(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(failures=20))
        assert r["status"] == "critical"

    def test_critical_consecutive_failures_5(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(consecutive_failures=5))
        assert r["status"] == "critical"

    def test_critical_consecutive_failures_10(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(consecutive_failures=10))
        assert r["status"] == "critical"

    def test_critical_unauth_overrides_healthy(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(
            latency_ms=10, failures=0, authenticated=False,
        ))
        assert r["status"] == "critical"

    def test_offline_zero_latency_241_freshness(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(latency_ms=0, freshness_minutes=241))
        assert r["status"] == "offline"

    def test_offline_zero_latency_300_freshness(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(latency_ms=0, freshness_minutes=300))
        assert r["status"] == "offline"

    def test_warning_rate_limit_zero(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(rate_limit_remaining=0))
        assert r["status"] == "warning"

    def test_warning_queue_1001(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(queue_size=1001))
        assert r["status"] == "warning"

    def test_warning_queue_2000(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(queue_size=2000))
        assert r["status"] == "warning"

    def test_warning_freshness_121(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(freshness_minutes=121))
        assert r["status"] == "warning"

    def test_warning_freshness_200(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(freshness_minutes=200))
        assert r["status"] == "warning"

    def test_warning_latency_30001(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(latency_ms=30001))
        assert r["status"] == "warning"

    def test_warning_latency_50000(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(latency_ms=50000))
        assert r["status"] == "warning"

    def test_healthy_latency_1(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(latency_ms=1, freshness_minutes=10))
        assert r["status"] == "healthy"

    def test_healthy_latency_29999(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(latency_ms=29999, freshness_minutes=10))
        assert r["status"] == "healthy"

    def test_healthy_failures_9(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(failures=9))
        assert r["status"] == "healthy"

    def test_healthy_consecutive_4(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(consecutive_failures=4))
        assert r["status"] == "healthy"

    def test_healthy_rate_limit_1(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(rate_limit_remaining=1))
        assert r["status"] == "healthy"

    def test_healthy_queue_1000(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(queue_size=1000))
        assert r["status"] == "healthy"

    def test_healthy_freshness_120(self):
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(freshness_minutes=120))
        assert r["status"] == "healthy"

    def test_result_fields(self):
        now = datetime.now(UTC)
        e = ConnectorHealthEngine()
        r = e.calculate(HealthInput(
            latency_ms=100, failures=2, retries=1,
            authenticated=True, rate_limit_remaining=500,
            queue_size=10, freshness_minutes=5,
            consecutive_failures=1, last_success=now, last_failure=now,
        ))
        assert r["latency_ms"] == 100
        assert r["failures"] == 2
        assert r["retries"] == 1
        assert r["authenticated"] is True
        assert r["rate_limit_remaining"] == 500
        assert r["queue_size"] == 10
        assert r["freshness_minutes"] == 5
        assert r["consecutive_failures"] == 1
        assert r["last_success"] is not None
        assert r["last_failure"] is not None


class TestBulkCalculate:
    def test_multiple(self):
        e = ConnectorHealthEngine()
        inputs = {
            "c1": HealthInput(failures=0),
            "c2": HealthInput(failures=10),
            "c3": HealthInput(authenticated=False),
            "c4": HealthInput(rate_limit_remaining=0),
            "c5": HealthInput(queue_size=1001),
            "c6": HealthInput(freshness_minutes=200),
            "c7": HealthInput(latency_ms=50000),
            "c8": HealthInput(latency_ms=0, freshness_minutes=300),
        }
        results = e.bulk_calculate(inputs)
        assert results["c1"]["status"] == "healthy"
        assert results["c2"]["status"] == "critical"
        assert results["c3"]["status"] == "critical"
        assert results["c4"]["status"] == "warning"
        assert results["c5"]["status"] == "warning"
        assert results["c6"]["status"] == "warning"
        assert results["c7"]["status"] == "warning"
        assert results["c8"]["status"] == "offline"

    def test_empty(self):
        e = ConnectorHealthEngine()
        assert e.bulk_calculate({}) == {}


class TestWorstStatus:
    def test_empty(self):
        e = ConnectorHealthEngine()
        assert e.worst_status([]) == "healthy"

    def test_all_healthy(self):
        e = ConnectorHealthEngine()
        assert e.worst_status(["healthy", "healthy", "healthy"]) == "healthy"

    def test_one_warning(self):
        e = ConnectorHealthEngine()
        assert e.worst_status(["healthy", "warning"]) == "warning"

    def test_one_critical(self):
        e = ConnectorHealthEngine()
        assert e.worst_status(["healthy", "warning", "critical"]) == "critical"

    def test_one_offline(self):
        e = ConnectorHealthEngine()
        assert e.worst_status(["healthy", "offline"]) == "offline"

    def test_priority_order(self):
        e = ConnectorHealthEngine()
        assert e.worst_status(["healthy", "offline", "warning", "critical"]) == "critical"
        assert e.worst_status(["healthy", "offline", "warning"]) == "warning"
        assert e.worst_status(["healthy", "warning"]) == "warning"
