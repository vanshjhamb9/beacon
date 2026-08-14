"""Tests for connector metrics."""

from __future__ import annotations

import pytest

from opportunity_connector_platform.connector_metrics import ConnectorMetrics, MetricsInput


class TestConnectorMetrics:
    def test_acceptance_rate(self):
        m = ConnectorMetrics()
        assert m.acceptance_rate(80, 20) == 80.0

    def test_acceptance_rate_zero(self):
        m = ConnectorMetrics()
        assert m.acceptance_rate(0, 0) == 0.0

    def test_rejection_rate(self):
        m = ConnectorMetrics()
        assert m.rejection_rate(80, 20) == 20.0

    def test_failure_rate(self):
        m = ConnectorMetrics()
        assert m.failure_rate(5, 100) == 5.0

    def test_failure_rate_zero_runs(self):
        m = ConnectorMetrics()
        assert m.failure_rate(5, 0) == 0.0

    def test_average_latency(self):
        m = ConnectorMetrics()
        assert m.average_latency([100, 200, 300]) == 200.0

    def test_average_latency_empty(self):
        m = ConnectorMetrics()
        assert m.average_latency([]) == 0.0

    def test_p95_latency(self):
        m = ConnectorMetrics()
        assert m.p95_latency([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == 10.0

    def test_p95_latency_empty(self):
        m = ConnectorMetrics()
        assert m.p95_latency([]) == 0.0

    def test_signal_yield(self):
        m = ConnectorMetrics()
        assert m.signal_yield(50, 100) == 50.0

    def test_revenue_yield(self):
        m = ConnectorMetrics()
        assert m.revenue_yield(10, 100) == 10.0

    def test_meeting_yield(self):
        m = ConnectorMetrics()
        assert m.meeting_yield(5, 100) == 5.0

    def test_conversion_rate(self):
        m = ConnectorMetrics()
        assert m.conversion_rate(2, 100) == 2.0

    def test_revenue_per_signal(self):
        m = ConnectorMetrics()
        assert m.revenue_per_signal(500, 100) == 5.0

    def test_revenue_per_signal_zero_signals(self):
        m = ConnectorMetrics()
        assert m.revenue_per_signal(500, 0) == 0.0

    def test_calculate_all(self):
        m = ConnectorMetrics()
        inp = MetricsInput(
            accepted=80,
            rejected=20,
            failures=5,
            runs=100,
            latencies=(100, 200, 300),
            signals=100,
            revenue_ready=10,
            meetings=5,
            won=2,
            revenue=500,
        )
        result = m.calculate_all(inp)
        assert result["acceptance_rate"] == 80.0
        assert result["rejection_rate"] == 20.0
        assert result["failure_rate"] == 5.0
        assert result["average_latency"] == 200.0
        assert result["signal_yield"] == 80.0
        assert result["revenue_yield"] == 10.0
        assert result["meeting_yield"] == 5.0
        assert result["conversion_rate"] == 2.0
        assert result["revenue_per_signal"] == 5.0

    def test_acceptance_rate_all_rejected(self):
        m = ConnectorMetrics()
        assert m.acceptance_rate(0, 100) == 0.0

    def test_acceptance_rate_all_accepted(self):
        m = ConnectorMetrics()
        assert m.acceptance_rate(100, 0) == 100.0

    def test_failure_rate_all_failures(self):
        m = ConnectorMetrics()
        assert m.failure_rate(100, 100) == 100.0

    def test_average_latency_single(self):
        m = ConnectorMetrics()
        assert m.average_latency([42.5]) == 42.5

    def test_p95_latency_single(self):
        m = ConnectorMetrics()
        assert m.p95_latency([42.5]) == 42.5

    def test_revenue_per_signal_rounding(self):
        m = ConnectorMetrics()
        assert m.revenue_per_signal(1, 3) == 0.33

    def test_calculate_all_empty(self):
        m = ConnectorMetrics()
        result = m.calculate_all(MetricsInput())
        assert result["acceptance_rate"] == 0.0
        assert result["failure_rate"] == 0.0
        assert result["revenue_per_signal"] == 0.0
