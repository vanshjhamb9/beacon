"""Tests for IndustryFilter."""

from __future__ import annotations

from discovery_quality_engine.industry_filter import IndustryFilter, IndustryFilterResult
from discovery_quality_engine.quality_engine import QualityDecision, QualityGate, RejectionReason


class TestIndustryFilter:
    def setup_method(self) -> None:
        self.filter = IndustryFilter()

    def test_technology_accepted(self) -> None:
        result = self.filter.evaluate("technology")
        assert result.decision == QualityDecision.ACCEPT

    def test_software_accepted(self) -> None:
        result = self.filter.evaluate("software")
        assert result.decision == QualityDecision.ACCEPT

    def test_saas_accepted(self) -> None:
        result = self.filter.evaluate("saas")
        assert result.decision == QualityDecision.ACCEPT

    def test_fintech_accepted(self) -> None:
        result = self.filter.evaluate("fintech")
        assert result.decision == QualityDecision.ACCEPT

    def test_healthcare_accepted(self) -> None:
        result = self.filter.evaluate("healthcare")
        assert result.decision == QualityDecision.ACCEPT

    def test_finance_accepted(self) -> None:
        result = self.filter.evaluate("finance")
        assert result.decision == QualityDecision.ACCEPT

    def test_missing_industry_rejected(self) -> None:
        result = self.filter.evaluate(None)
        assert result.decision == QualityDecision.REJECT
        assert "Missing industry" in result.reasons

    def test_empty_industry_rejected(self) -> None:
        result = self.filter.evaluate("")
        assert result.decision == QualityDecision.REJECT

    def test_unknown_industry_rejected(self) -> None:
        result = self.filter.evaluate("underwater basket weaving")
        assert result.decision == QualityDecision.REJECT
        assert "OUTSIDE_ICP" in result.reasons

    def test_partial_match_accepted(self) -> None:
        result = self.filter.evaluate("cloud technology")
        assert result.decision == QualityDecision.ACCEPT

    def test_gate_name(self) -> None:
        assert self.filter.gate_name() == QualityGate.INDUSTRY_RULES.value

    def test_custom_industries(self) -> None:
        filter = IndustryFilter(allowed_industries=frozenset({"mining", "agriculture"}))
        result = filter.evaluate("mining")
        assert result.decision == QualityDecision.ACCEPT

    def test_custom_industries_reject(self) -> None:
        filter = IndustryFilter(allowed_industries=frozenset({"mining"}))
        result = filter.evaluate("technology")
        assert result.decision == QualityDecision.REJECT

    def test_case_insensitive(self) -> None:
        result = self.filter.evaluate("Technology")
        assert result.decision == QualityDecision.ACCEPT

    def test_whitespace_handled(self) -> None:
        result = self.filter.evaluate("  technology  ")
        assert result.decision == QualityDecision.ACCEPT
