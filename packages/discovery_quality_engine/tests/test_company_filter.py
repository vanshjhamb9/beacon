"""Tests for CompanyFilter."""

from __future__ import annotations

from discovery_quality_engine.company_filter import CompanyFilter, CompanyValidationResult
from discovery_quality_engine.quality_engine import QualityDecision, QualityGate, RejectionReason


class TestCompanyFilter:
    def setup_method(self) -> None:
        self.filter = CompanyFilter()

    def test_valid_company_name(self) -> None:
        result = self.filter.evaluate(company_name="Acme Corp")
        assert result.decision == QualityDecision.ACCEPT

    def test_missing_company_name(self) -> None:
        result = self.filter.evaluate(company_name=None)
        assert result.decision == QualityDecision.REJECT
        assert "Missing company name" in result.reasons

    def test_empty_company_name(self) -> None:
        result = self.filter.evaluate(company_name="")
        assert result.decision == QualityDecision.REJECT

    def test_whitespace_company_name(self) -> None:
        result = self.filter.evaluate(company_name="   ")
        assert result.decision == QualityDecision.REJECT

    def test_single_char_company_name(self) -> None:
        result = self.filter.evaluate(company_name="A")
        assert result.decision == QualityDecision.REJECT
        assert "too short" in result.reasons[0].lower()

    def test_two_char_company_name(self) -> None:
        result = self.filter.evaluate(company_name="AB")
        assert result.decision == QualityDecision.ACCEPT

    def test_long_company_name(self) -> None:
        result = self.filter.evaluate(company_name="A" * 255)
        assert result.decision == QualityDecision.ACCEPT

    def test_gate_name(self) -> None:
        assert self.filter.gate_name() == QualityGate.COMPANY_VALIDATION.value

    def test_rejection_includes_unknown(self) -> None:
        result = self.filter.evaluate(company_name=None)
        assert RejectionReason.UNKNOWN.value in result.reasons
