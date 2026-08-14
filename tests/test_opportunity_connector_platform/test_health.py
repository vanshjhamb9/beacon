"""Tests for connector health engine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from opportunity_connector_platform.connector_health import ConnectorHealthEngine, HealthInput


class TestHealthInput:
    def test_defaults(self):
        h = HealthInput()
        assert h.latency_ms == 0.0
        assert h.failures == 0
        assert h.retries == 0
        assert h.authenticated is True
        assert h.rate_limit_remaining is None
        assert h.queue_size == 0
        assert h.freshness_minutes == 0
        assert h.consecutive_failures == 0

    def test_frozen(self):
        h = HealthInput()
        with pytest.raises(AttributeError):
            h.failures = 5  # type: ignore[misc]


class TestConnectorHealthEngine:
    def test_healthy_default(self):
        engine = ConnectorHealthEngine()
        result = engine.calculate(HealthInput())
        assert result["status"] == "healthy"

    def test_critical_unauthenticated(self):
        engine = ConnectorHealthEngine()
        result = engine.calculate(HealthInput(authenticated=False))
        assert result["status"] == "critical"

    def test_critical_high_failures(self):
        engine = ConnectorHealthEngine()
        result = engine.calculate(HealthInput(failures=10))
        assert result["status"] == "critical"

    def test_critical_consecutive_failures(self):
        engine = ConnectorHealthEngine()
        result = engine.calculate(HealthInput(consecutive_failures=5))
        assert result["status"] == "critical"

    def test_warning_rate_limit_zero(self):
        engine = ConnectorHealthEngine()
        result = engine.calculate(HealthInput(rate_limit_remaining=0))
        assert result["status"] == "warning"

    def test_warning_queue_size(self):
        engine = ConnectorHealthEngine()
        result = engine.calculate(HealthInput(queue_size=1001))
        assert result["status"] == "warning"

    def test_warning_freshness(self):
        engine = ConnectorHealthEngine()
        result = engine.calculate(HealthInput(freshness_minutes=121))
        assert result["status"] == "warning"

    def test_warning_high_latency(self):
        engine = ConnectorHealthEngine()
        result = engine.calculate(HealthInput(latency_ms=30001))
        assert result["status"] == "warning"

    def test_offline(self):
        engine = ConnectorHealthEngine()
        result = engine.calculate(HealthInput(latency_ms=0, freshness_minutes=241))
        assert result["status"] == "offline"

    def test_healthy_low_latency(self):
        engine = ConnectorHealthEngine()
        result = engine.calculate(HealthInput(latency_ms=50, freshness_minutes=10))
        assert result["status"] == "healthy"

    def test_rate_limit_positive_not_warning(self):
        engine = ConnectorHealthEngine()
        result = engine.calculate(HealthInput(rate_limit_remaining=1))
        assert result["status"] == "healthy"

    def test_failures_9_not_critical(self):
        engine = ConnectorHealthEngine()
        result = engine.calculate(HealthInput(failures=9))
        assert result["status"] == "healthy"

    def test_consecutive_failures_4_not_critical(self):
        engine = ConnectorHealthEngine()
        result = engine.calculate(HealthInput(consecutive_failures=4))
        assert result["status"] == "healthy"

    def test_bulk_calculate(self):
        engine = ConnectorHealthEngine()
        inputs = {
            "c1": HealthInput(failures=0),
            "c2": HealthInput(failures=10),
            "c3": HealthInput(authenticated=False),
        }
        results = engine.bulk_calculate(inputs)
        assert results["c1"]["status"] == "healthy"
        assert results["c2"]["status"] == "critical"
        assert results["c3"]["status"] == "critical"

    def test_worst_status_empty(self):
        engine = ConnectorHealthEngine()
        assert engine.worst_status([]) == "healthy"

    def test_worst_status_all_healthy(self):
        engine = ConnectorHealthEngine()
        assert engine.worst_status(["healthy", "healthy"]) == "healthy"

    def test_worst_status_has_warning(self):
        engine = ConnectorHealthEngine()
        assert engine.worst_status(["healthy", "warning"]) == "warning"

    def test_worst_status_has_critical(self):
        engine = ConnectorHealthEngine()
        assert engine.worst_status(["healthy", "warning", "critical"]) == "critical"

    def test_worst_status_has_offline(self):
        engine = ConnectorHealthEngine()
        assert engine.worst_status(["healthy", "offline"]) == "offline"

    def test_result_includes_all_fields(self):
        engine = ConnectorHealthEngine()
        now = datetime.now(UTC)
        result = engine.calculate(HealthInput(
            latency_ms=100,
            failures=2,
            retries=1,
            authenticated=True,
            rate_limit_remaining=500,
            queue_size=10,
            freshness_minutes=5,
            last_success=now,
            last_failure=now,
            consecutive_failures=1,
        ))
        assert result["latency_ms"] == 100
        assert result["failures"] == 2
        assert result["retries"] == 1
        assert result["authenticated"] is True
        assert result["rate_limit_remaining"] == 500
        assert result["queue_size"] == 10
        assert result["freshness_minutes"] == 5
        assert result["last_success"] is not None
        assert result["last_failure"] is not None
        assert result["consecutive_failures"] == 1

    def test_priority_order(self):
        engine = ConnectorHealthEngine()
        assert engine.worst_status(["healthy", "warning", "critical", "offline"]) == "critical"

    def test_queue_exactly_1000(self):
        engine = ConnectorHealthEngine()
        result = engine.calculate(HealthInput(queue_size=1000))
        assert result["status"] == "healthy"

    def test_queue_1001(self):
        engine = ConnectorHealthEngine()
        result = engine.calculate(HealthInput(queue_size=1001))
        assert result["status"] == "warning"
