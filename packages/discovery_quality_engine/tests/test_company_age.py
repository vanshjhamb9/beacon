"""Tests for CompanyAgeFilter."""

from __future__ import annotations

from discovery_quality_engine.company_age import CompanyAgeFilter, CompanyAgeResult
from discovery_quality_engine.quality_engine import QualityDecision, QualityGate, RejectionReason


class TestCompanyAgeFilter:
    def setup_method(self) -> None:
        self.filter = CompanyAgeFilter()

    def test_unknown_age_accepted(self) -> None:
        result = self.filter.evaluate(None)
        assert result.decision == QualityDecision.ACCEPT
        assert result.age_days == 0

    def test_valid_age_accepted(self) -> None:
        result = self.filter.evaluate(365)
        assert result.decision == QualityDecision.ACCEPT
        assert result.age_days == 365

    def test_young_company_rejected(self) -> None:
        result = self.filter.evaluate(10)
        assert result.decision == QualityDecision.REJECT
        assert "below minimum" in result.reasons[0].lower()

    def test_old_company_rejected(self) -> None:
        result = self.filter.evaluate(40000)
        assert result.decision == QualityDecision.REJECT
        assert "above maximum" in result.reasons[0].lower()

    def test_boundary_min_accepted(self) -> None:
        result = self.filter.evaluate(30)
        assert result.decision == QualityDecision.ACCEPT

    def test_boundary_max_accepted(self) -> None:
        result = self.filter.evaluate(36500)
        assert result.decision == QualityDecision.ACCEPT

    def test_gate_name(self) -> None:
        assert self.filter.gate_name() == QualityGate.ICP_FILTER.value

    def test_custom_min_age(self) -> None:
        filter = CompanyAgeFilter(min_age_days=100)
        result = filter.evaluate(50)
        assert result.decision == QualityDecision.REJECT

    def test_custom_max_age(self) -> None:
        filter = CompanyAgeFilter(max_age_days=1000)
        result = filter.evaluate(2000)
        assert result.decision == QualityDecision.REJECT

    def test_rejection_includes_outside_icp(self) -> None:
        result = self.filter.evaluate(10)
        assert "OUTSIDE_ICP" in result.reasons
