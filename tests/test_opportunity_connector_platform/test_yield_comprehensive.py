"""Comprehensive tests for connector yield engine."""

from __future__ import annotations

import pytest

from opportunity_connector_platform.connector_yield import ConnectorYield, ConnectorYieldEngine


class TestConnectorYieldComprehensive:
    def test_all_zeros(self):
        y = ConnectorYield()
        assert y.signals == 0
        assert y.revenue == 0.0

    def test_full_funnel(self):
        y = ConnectorYield(
            signals=1000, accepted=200, identity_matched=150,
            verified_companies=100, sales_ready=50, revenue_ready=30,
            contacted=20, replies=10, meetings=5, won=2, revenue=10000,
        )
        assert y.signals == 1000
        assert y.won == 2
        assert y.revenue == 10000

    def test_frozen(self):
        y = ConnectorYield()
        with pytest.raises(AttributeError):
            y.signals = 100  # type: ignore[misc]


class TestYieldEngineComprehensive:
    def test_signal_yield(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, accepted=25)
        result = e.calculate(y)
        assert result["signal_yield"] == 25.0

    def test_revenue_yield(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=200, revenue_ready=40)
        result = e.calculate(y)
        assert result["revenue_yield"] == 20.0

    def test_meeting_yield(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=500, meetings=10)
        result = e.calculate(y)
        assert result["meeting_yield"] == 2.0

    def test_acceptance_rate(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=80, accepted=60)
        result = e.calculate(y)
        assert result["acceptance_rate"] == 75.0

    def test_conversion_rate(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, won=3)
        result = e.calculate(y)
        assert result["conversion_rate"] == 3.0

    def test_revenue_per_signal(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=10, revenue=5000)
        result = e.calculate(y)
        assert result["revenue_per_signal"] == 500.0

    def test_identity_match_rate(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, accepted=50, identity_matched=25)
        result = e.calculate(y)
        assert result["identity_match_rate"] == 50.0

    def test_verification_rate(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, accepted=50, identity_matched=50, verified_companies=25)
        result = e.calculate(y)
        assert result["verification_rate"] == 50.0

    def test_sales_readiness_rate(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, verified_companies=50, sales_ready=25)
        result = e.calculate(y)
        assert result["sales_readiness_rate"] == 50.0

    def test_revenue_readiness_rate(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, sales_ready=50, revenue_ready=25)
        result = e.calculate(y)
        assert result["revenue_readiness_rate"] == 50.0

    def test_contact_rate(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, revenue_ready=50, contacted=25)
        result = e.calculate(y)
        assert result["contact_rate"] == 50.0

    def test_reply_rate(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, contacted=50, replies=25)
        result = e.calculate(y)
        assert result["reply_rate"] == 50.0

    def test_meeting_rate(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, replies=20, meetings=10)
        result = e.calculate(y)
        assert result["meeting_rate"] == 50.0

    def test_win_rate(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, meetings=10, won=3)
        result = e.calculate(y)
        assert result["win_rate"] == 30.0

    def test_all_zeros(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield()
        result = e.calculate(y)
        for key in ["signal_yield", "revenue_yield", "meeting_yield", "conversion_rate", "revenue_per_signal"]:
            assert result[key] == 0.0

    def test_funnel_summary_all_zeros(self):
        e = ConnectorYieldEngine()
        summary = e.funnel_summary(ConnectorYield())
        for v in summary.values():
            assert v == 0

    def test_funnel_summary_full(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(
            signals=100, accepted=50, identity_matched=40,
            verified_companies=30, sales_ready=20, revenue_ready=10,
            contacted=8, replies=4, meetings=2, won=1,
        )
        summary = e.funnel_summary(y)
        assert summary["signals"] == 100
        assert summary["won"] == 1

    def test_high_revenue_per_signal(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=5, revenue=100000)
        result = e.calculate(y)
        assert result["revenue_per_signal"] == 20000.0
