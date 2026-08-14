"""Tests for RegionFilter."""

from __future__ import annotations

from discovery_quality_engine.region_filter import RegionFilter, RegionFilterResult
from discovery_quality_engine.quality_engine import QualityDecision, QualityGate, RejectionReason


class TestRegionFilter:
    def setup_method(self) -> None:
        self.filter = RegionFilter()

    def test_us_accepted(self) -> None:
        result = self.filter.evaluate("US")
        assert result.decision == QualityDecision.ACCEPT

    def test_canada_accepted(self) -> None:
        result = self.filter.evaluate("CA")
        assert result.decision == QualityDecision.ACCEPT

    def test_uk_accepted(self) -> None:
        result = self.filter.evaluate("UK")
        assert result.decision == QualityDecision.ACCEPT

    def test_germany_accepted(self) -> None:
        result = self.filter.evaluate("DE")
        assert result.decision == QualityDecision.ACCEPT

    def test_france_accepted(self) -> None:
        result = self.filter.evaluate("FR")
        assert result.decision == QualityDecision.ACCEPT

    def test_australia_accepted(self) -> None:
        result = self.filter.evaluate("AU")
        assert result.decision == QualityDecision.ACCEPT

    def test_india_accepted(self) -> None:
        result = self.filter.evaluate("IN")
        assert result.decision == QualityDecision.ACCEPT

    def test_uae_accepted(self) -> None:
        result = self.filter.evaluate("AE")
        assert result.decision == QualityDecision.ACCEPT

    def test_missing_country_rejected(self) -> None:
        result = self.filter.evaluate(None)
        assert result.decision == QualityDecision.REJECT
        assert "Missing country/region" in result.reasons

    def test_empty_country_rejected(self) -> None:
        result = self.filter.evaluate("")
        assert result.decision == QualityDecision.REJECT

    def test_unsupported_country_rejected(self) -> None:
        result = self.filter.evaluate("KP")
        assert result.decision == QualityDecision.REJECT
        assert "UNSUPPORTED_REGION" in result.reasons

    def test_gate_name(self) -> None:
        assert self.filter.gate_name() == QualityGate.REGION_RULES.value

    def test_custom_regions(self) -> None:
        filter = RegionFilter(supported_regions=["US", "JP"])
        result = filter.evaluate("JP")
        assert result.decision == QualityDecision.ACCEPT

    def test_custom_regions_reject(self) -> None:
        filter = RegionFilter(supported_regions=["US"])
        result = filter.evaluate("UK")
        assert result.decision == QualityDecision.REJECT

    def test_case_normalization(self) -> None:
        result = self.filter.evaluate("us")
        assert result.decision == QualityDecision.ACCEPT

    def test_whitespace_handled(self) -> None:
        result = self.filter.evaluate("  US  ")
        assert result.decision == QualityDecision.ACCEPT
