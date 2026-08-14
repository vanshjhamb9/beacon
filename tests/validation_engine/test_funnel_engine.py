"""Tests for FunnelEngine."""

from __future__ import annotations

from validation_engine.funnel_engine import FunnelEngine
from validation_engine.lead_validator import LeadValidator


class TestFunnelEngineCalculateFunnel:
    def test_empty_funnel(self, funnel_engine: FunnelEngine) -> None:
        funnel = funnel_engine.calculate_funnel()
        assert len(funnel) > 0
        assert all(f["count"] == 0 for f in funnel)

    def test_funnel_with_data(
        self,
        funnel_engine: FunnelEngine,
        lead_validator: LeadValidator,
    ) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        lead_validator.record_transition("company_1", "REPLIED")
        funnel = funnel_engine.calculate_funnel()
        assert any(f["stage"] == "REVENUE_READY" and f["count"] == 1 for f in funnel)
        assert any(f["stage"] == "CONTACTED" and f["count"] == 1 for f in funnel)


class TestFunnelEngineCalculateConversion:
    def test_conversion_zero(self, funnel_engine: FunnelEngine) -> None:
        result = funnel_engine.calculate_conversion("REVENUE_READY", "CONTACTED")
        assert result["conversion_rate"] == 0.0
        assert result["drop_off"] == 100.0

    def test_conversion_calculated(
        self,
        funnel_engine: FunnelEngine,
        lead_validator: LeadValidator,
    ) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_2", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        result = funnel_engine.calculate_conversion("REVENUE_READY", "CONTACTED")
        assert result["conversion_rate"] == 50.0
        assert result["drop_off"] == 50.0


class TestFunnelEngineGetBiggestBottleneck:
    def test_biggest_bottleneck_empty(self, funnel_engine: FunnelEngine) -> None:
        bottleneck = funnel_engine.get_biggest_bottleneck()
        assert bottleneck["stage"] == "REVENUE_READY"
        assert bottleneck["drop_off"] == 0.0

    def test_biggest_bottleneck_calculated(
        self,
        funnel_engine: FunnelEngine,
        lead_validator: LeadValidator,
    ) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_2", "REVENUE_READY")
        lead_validator.record_transition("company_3", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        bottleneck = funnel_engine.get_biggest_bottleneck()
        assert bottleneck["drop_off"] > 0


class TestFunnelEngineGetStageConversions:
    def test_get_stage_conversions(self, funnel_engine: FunnelEngine) -> None:
        conversions = funnel_engine.get_stage_conversions()
        assert len(conversions) > 0
        assert all("from_stage" in c and "to_stage" in c for c in conversions)


class TestFunnelEngineGetConversionSummary:
    def test_conversion_summary_empty(self, funnel_engine: FunnelEngine) -> None:
        summary = funnel_engine.get_conversion_summary()
        assert summary["total_companies"] == 0
        assert summary["total_won"] == 0
        assert summary["overall_conversion_rate"] == 0.0
