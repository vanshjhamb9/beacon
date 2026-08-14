"""Comprehensive tests for connector metrics."""

from __future__ import annotations

import pytest

from opportunity_connector_platform.connector_metrics import ConnectorMetrics, MetricsInput


class TestAcceptanceRate:
    def test_half(self):
        m = ConnectorMetrics()
        assert m.acceptance_rate(50, 50) == 50.0

    def test_all_accepted(self):
        m = ConnectorMetrics()
        assert m.acceptance_rate(100, 0) == 100.0

    def test_all_rejected(self):
        m = ConnectorMetrics()
        assert m.acceptance_rate(0, 100) == 0.0

    def test_zero_zero(self):
        m = ConnectorMetrics()
        assert m.acceptance_rate(0, 0) == 0.0

    def test_one_one(self):
        m = ConnectorMetrics()
        assert m.acceptance_rate(1, 1) == 50.0

    def test_large_numbers(self):
        m = ConnectorMetrics()
        assert m.acceptance_rate(999999, 1) == 100.0


class TestRejectionRate:
    def test_half(self):
        m = ConnectorMetrics()
        assert m.rejection_rate(50, 50) == 50.0

    def test_all_rejected(self):
        m = ConnectorMetrics()
        assert m.rejection_rate(0, 100) == 100.0

    def test_all_accepted(self):
        m = ConnectorMetrics()
        assert m.rejection_rate(100, 0) == 0.0

    def test_zero_zero(self):
        m = ConnectorMetrics()
        assert m.rejection_rate(0, 0) == 0.0


class TestFailureRate:
    def test_10_percent(self):
        m = ConnectorMetrics()
        assert m.failure_rate(10, 100) == 10.0

    def test_100_percent(self):
        m = ConnectorMetrics()
        assert m.failure_rate(50, 50) == 100.0

    def test_zero_runs(self):
        m = ConnectorMetrics()
        assert m.failure_rate(5, 0) == 0.0

    def test_zero_failures(self):
        m = ConnectorMetrics()
        assert m.failure_rate(0, 100) == 0.0


class TestAverageLatency:
    def test_three_values(self):
        m = ConnectorMetrics()
        assert m.average_latency([100, 200, 300]) == 200.0

    def test_single_value(self):
        m = ConnectorMetrics()
        assert m.average_latency([42.5]) == 42.5

    def test_empty(self):
        m = ConnectorMetrics()
        assert m.average_latency([]) == 0.0

    def test_tuple(self):
        m = ConnectorMetrics()
        assert m.average_latency((10, 20)) == 15.0

    def test_large_list(self):
        m = ConnectorMetrics()
        values = [1.0] * 1000
        assert m.average_latency(values) == 1.0


class TestP95Latency:
    def test_ten_values(self):
        m = ConnectorMetrics()
        assert m.p95_latency([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == 10.0

    def test_empty(self):
        m = ConnectorMetrics()
        assert m.p95_latency([]) == 0.0

    def test_single(self):
        m = ConnectorMetrics()
        assert m.p95_latency([50]) == 50.0

    def test_100_values(self):
        m = ConnectorMetrics()
        values = list(range(1, 101))
        result = m.p95_latency(values)
        assert result == 96


class TestSignalYield:
    def test_50_percent(self):
        m = ConnectorMetrics()
        assert m.signal_yield(50, 100) == 50.0

    def test_zero_signals(self):
        m = ConnectorMetrics()
        assert m.signal_yield(50, 0) == 0.0

    def test_100_percent(self):
        m = ConnectorMetrics()
        assert m.signal_yield(100, 100) == 100.0


class TestRevenueYield:
    def test_10_percent(self):
        m = ConnectorMetrics()
        assert m.revenue_yield(10, 100) == 10.0

    def test_zero_signals(self):
        m = ConnectorMetrics()
        assert m.revenue_yield(10, 0) == 0.0


class TestMeetingYield:
    def test_5_percent(self):
        m = ConnectorMetrics()
        assert m.meeting_yield(5, 100) == 5.0

    def test_zero_signals(self):
        m = ConnectorMetrics()
        assert m.meeting_yield(5, 0) == 0.0


class TestConversionRate:
    def test_2_percent(self):
        m = ConnectorMetrics()
        assert m.conversion_rate(2, 100) == 2.0

    def test_zero_signals(self):
        m = ConnectorMetrics()
        assert m.conversion_rate(2, 0) == 0.0


class TestRevenuePerSignal:
    def test_5_dollars(self):
        m = ConnectorMetrics()
        assert m.revenue_per_signal(500, 100) == 5.0

    def test_zero_signals(self):
        m = ConnectorMetrics()
        assert m.revenue_per_signal(500, 0) == 0.0

    def test_rounding(self):
        m = ConnectorMetrics()
        assert m.revenue_per_signal(1, 3) == 0.33


class TestCalculateAll:
    def test_full(self):
        m = ConnectorMetrics()
        result = m.calculate_all(MetricsInput(
            accepted=80, rejected=20, failures=5, runs=100,
            latencies=(100, 200, 300), signals=100,
            revenue_ready=10, meetings=5, won=2, revenue=500,
        ))
        assert result["acceptance_rate"] == 80.0
        assert result["rejection_rate"] == 20.0
        assert result["failure_rate"] == 5.0
        assert result["average_latency"] == 200.0
        assert result["signal_yield"] == 80.0
        assert result["revenue_yield"] == 10.0
        assert result["meeting_yield"] == 5.0
        assert result["conversion_rate"] == 2.0
        assert result["revenue_per_signal"] == 5.0

    def test_empty(self):
        m = ConnectorMetrics()
        result = m.calculate_all(MetricsInput())
        for v in result.values():
            assert v == 0.0
