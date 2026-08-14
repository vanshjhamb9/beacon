"""Tests for connector yield engine."""

from __future__ import annotations

import pytest

from opportunity_connector_platform.connector_yield import ConnectorYield, ConnectorYieldEngine


class TestConnectorYield:
    def test_defaults(self):
        y = ConnectorYield()
        assert y.signals == 0
        assert y.accepted == 0
        assert y.identity_matched == 0
        assert y.verified_companies == 0
        assert y.sales_ready == 0
        assert y.revenue_ready == 0
        assert y.contacted == 0
        assert y.replies == 0
        assert y.meetings == 0
        assert y.won == 0
        assert y.revenue == 0.0

    def test_frozen(self):
        y = ConnectorYield()
        with pytest.raises(AttributeError):
            y.signals = 100  # type: ignore[misc]

    def test_custom(self):
        y = ConnectorYield(
            signals=1000,
            accepted=200,
            identity_matched=150,
            verified_companies=100,
            sales_ready=50,
            revenue_ready=30,
            contacted=20,
            replies=10,
            meetings=5,
            won=2,
            revenue=10000.0,
        )
        assert y.signals == 1000
        assert y.won == 2
        assert y.revenue == 10000.0


class TestConnectorYieldEngine:
    def test_full_funnel(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(
            signals=1000,
            accepted=200,
            identity_matched=150,
            verified_companies=100,
            sales_ready=50,
            revenue_ready=30,
            contacted=20,
            replies=10,
            meetings=5,
            won=2,
            revenue=10000.0,
        )
        result = e.calculate(y)
        assert result["signal_yield"] == 20.0
        assert result["revenue_yield"] == 3.0
        assert result["meeting_yield"] == 0.5
        assert result["acceptance_rate"] == 20.0
        assert result["conversion_rate"] == 0.2
        assert result["revenue_per_signal"] == 10.0
        assert result["identity_match_rate"] == 75.0
        assert result["verification_rate"] == 66.67
        assert result["sales_readiness_rate"] == 50.0
        assert result["revenue_readiness_rate"] == 60.0
        assert result["contact_rate"] == 66.67
        assert result["reply_rate"] == 50.0
        assert result["meeting_rate"] == 50.0
        assert result["win_rate"] == 40.0

    def test_zero_signals(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield()
        result = e.calculate(y)
        assert result["signal_yield"] == 0.0
        assert result["revenue_yield"] == 0.0
        assert result["meeting_yield"] == 0.0
        assert result["revenue_per_signal"] == 0.0

    def test_funnel_summary(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, accepted=50, meetings=5, won=2)
        summary = e.funnel_summary(y)
        assert summary["signals"] == 100
        assert summary["accepted"] == 50
        assert summary["meetings"] == 5
        assert summary["won"] == 2

    def test_acceptance_rate_100(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, accepted=100)
        result = e.calculate(y)
        assert result["acceptance_rate"] == 100.0

    def test_conversion_rate_zero(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, accepted=50)
        result = e.calculate(y)
        assert result["conversion_rate"] == 0.0

    def test_revenue_per_signal_high(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=10, revenue=100000)
        result = e.calculate(y)
        assert result["revenue_per_signal"] == 10000.0

    def test_meeting_yield_percentage(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=200, meetings=10)
        result = e.calculate(y)
        assert result["meeting_yield"] == 5.0

    def test_identity_match_rate_zero_accepted(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, accepted=0, identity_matched=0)
        result = e.calculate(y)
        assert result["identity_match_rate"] == 0.0

    def test_verification_rate_zero_matched(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, accepted=50, identity_matched=0)
        result = e.calculate(y)
        assert result["verification_rate"] == 0.0

    def test_sales_readiness_rate(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, accepted=50, identity_matched=50, verified_companies=50, sales_ready=25)
        result = e.calculate(y)
        assert result["sales_readiness_rate"] == 50.0

    def test_revenue_readiness_rate(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, sales_ready=50, revenue_ready=25)
        result = e.calculate(y)
        assert result["revenue_readiness_rate"] == 50.0

    def test_reply_rate(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, contacted=20, replies=10)
        result = e.calculate(y)
        assert result["reply_rate"] == 50.0

    def test_meeting_rate(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, replies=10, meetings=5)
        result = e.calculate(y)
        assert result["meeting_rate"] == 50.0

    def test_win_rate(self):
        e = ConnectorYieldEngine()
        y = ConnectorYield(signals=100, meetings=10, won=3)
        result = e.calculate(y)
        assert result["win_rate"] == 30.0

    def test_all_zeros_funnel_summary(self):
        e = ConnectorYieldEngine()
        summary = e.funnel_summary(ConnectorYield())
        for v in summary.values():
            assert v == 0
