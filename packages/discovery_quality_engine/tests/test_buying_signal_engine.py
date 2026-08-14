"""Tests for BuyingSignalEngine."""

from __future__ import annotations

from discovery_quality_engine.buying_signal_engine import BuyingSignalEngine, BuyingSignalResult
from discovery_quality_engine.quality_engine import QualityDecision, QualityGate, RejectionReason


class TestBuyingSignalEngine:
    def setup_method(self) -> None:
        self.engine = BuyingSignalEngine()

    def test_hiring_signal_accepted(self) -> None:
        result = self.engine.evaluate(["HIRING"])
        assert result.decision == QualityDecision.ACCEPT
        assert "HIRING" in result.signals_found

    def test_funding_signal_accepted(self) -> None:
        result = self.engine.evaluate(["FUNDING"])
        assert result.decision == QualityDecision.ACCEPT

    def test_expansion_signal_accepted(self) -> None:
        result = self.engine.evaluate(["EXPANSION"])
        assert result.decision == QualityDecision.ACCEPT

    def test_technology_adoption_signal_accepted(self) -> None:
        result = self.engine.evaluate(["TECHNOLOGY_ADOPTION"])
        assert result.decision == QualityDecision.ACCEPT

    def test_compliance_signal_accepted(self) -> None:
        result = self.engine.evaluate(["COMPLIANCE"])
        assert result.decision == QualityDecision.ACCEPT

    def test_executive_hiring_signal_accepted(self) -> None:
        result = self.engine.evaluate(["EXECUTIVE_HIRING"])
        assert result.decision == QualityDecision.ACCEPT

    def test_office_expansion_signal_accepted(self) -> None:
        result = self.engine.evaluate(["OFFICE_EXPANSION"])
        assert result.decision == QualityDecision.ACCEPT

    def test_acquisition_signal_accepted(self) -> None:
        result = self.engine.evaluate(["ACQUISITION"])
        assert result.decision == QualityDecision.ACCEPT

    def test_infrastructure_upgrade_signal_accepted(self) -> None:
        result = self.engine.evaluate(["INFRASTRUCTURE_UPGRADE"])
        assert result.decision == QualityDecision.ACCEPT

    def test_security_incident_signal_accepted(self) -> None:
        result = self.engine.evaluate(["SECURITY_INCIDENT"])
        assert result.decision == QualityDecision.ACCEPT

    def test_api_release_signal_accepted(self) -> None:
        result = self.engine.evaluate(["API_RELEASE"])
        assert result.decision == QualityDecision.ACCEPT

    def test_marketplace_expansion_signal_accepted(self) -> None:
        result = self.engine.evaluate(["MARKETPLACE_EXPANSION"])
        assert result.decision == QualityDecision.ACCEPT

    def test_product_launch_signal_accepted(self) -> None:
        result = self.engine.evaluate(["PRODUCT_LAUNCH"])
        assert result.decision == QualityDecision.ACCEPT

    def test_partnership_signal_accepted(self) -> None:
        result = self.engine.evaluate(["PARTNERSHIP"])
        assert result.decision == QualityDecision.ACCEPT

    def test_empty_signals_rejected(self) -> None:
        result = self.engine.evaluate([])
        assert result.decision == QualityDecision.REJECT
        assert result.signals_found == []
        assert "NO_BUYING_SIGNAL" in result.reasons

    def test_invalid_signal_rejected(self) -> None:
        result = self.engine.evaluate(["INVALID_SIGNAL"])
        assert result.decision == QualityDecision.REJECT

    def test_multiple_valid_signals(self) -> None:
        result = self.engine.evaluate(["HIRING", "FUNDING", "EXPANSION"])
        assert result.decision == QualityDecision.ACCEPT
        assert len(result.signals_found) == 3

    def test_mixed_valid_invalid_signals(self) -> None:
        result = self.engine.evaluate(["HIRING", "INVALID", "FUNDING"])
        assert result.decision == QualityDecision.ACCEPT
        assert len(result.signals_found) == 2

    def test_all_invalid_signals_rejected(self) -> None:
        result = self.engine.evaluate(["FOO", "BAR", "BAZ"])
        assert result.decision == QualityDecision.REJECT

    def test_gate_name(self) -> None:
        assert self.engine.gate_name() == QualityGate.BUYING_SIGNAL.value

    def test_custom_valid_signals(self) -> None:
        engine = BuyingSignalEngine(valid_signals=frozenset({"CUSTOM_SIGNAL"}))
        result = engine.evaluate(["CUSTOM_SIGNAL"])
        assert result.decision == QualityDecision.ACCEPT

    def test_custom_valid_signals_reject_standard(self) -> None:
        engine = BuyingSignalEngine(valid_signals=frozenset({"CUSTOM_SIGNAL"}))
        result = engine.evaluate(["HIRING"])
        assert result.decision == QualityDecision.REJECT

    def test_case_insensitive(self) -> None:
        result = self.engine.evaluate(["hiring"])
        assert result.decision == QualityDecision.ACCEPT

    def test_result_has_signals_found(self) -> None:
        result = self.engine.evaluate(["HIRING", "FUNDING"])
        assert isinstance(result.signals_found, list)
        assert "HIRING" in result.signals_found
        assert "FUNDING" in result.signals_found

    def test_rejection_reason_includes_enum_value(self) -> None:
        result = self.engine.evaluate([])
        assert RejectionReason.NO_BUYING_SIGNAL.value in result.reasons

    def test_accept_reasons_descriptive(self) -> None:
        result = self.engine.evaluate(["HIRING"])
        assert any("valid buying signal" in r.lower() for r in result.reasons)
