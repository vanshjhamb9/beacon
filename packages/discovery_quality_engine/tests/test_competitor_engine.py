"""Tests for CompetitorEngine."""

from __future__ import annotations

from discovery_quality_engine.competitor_engine import CompetitorConfig, CompetitorEngine, CompetitorResult
from discovery_quality_engine.quality_engine import QualityDecision, QualityGate, RejectionReason


class TestCompetitorEngine:
    def setup_method(self) -> None:
        self.config = CompetitorConfig(
            competitors=["google", "microsoft", "salesforce"],
            partners=["deloitte"],
            existing_clients=["acme corp"],
            internal_test=["test company"],
            demo_companies=["demo company"],
        )
        self.engine = CompetitorEngine(config=self.config)

    def test_non_competitor_accepted(self) -> None:
        result = self.engine.evaluate("Random Startup Inc")
        assert result.decision == QualityDecision.ACCEPT

    def test_competitor_rejected(self) -> None:
        result = self.engine.evaluate("Google")
        assert result.decision == QualityDecision.REJECT
        assert result.category == "competitor"
        assert "COMPETITOR" in result.reasons

    def test_competitor_exact_match(self) -> None:
        result = self.engine.evaluate("microsoft")
        assert result.decision == QualityDecision.REJECT

    def test_competitor_partial_match(self) -> None:
        result = self.engine.evaluate("Salesforce Inc")
        assert result.decision == QualityDecision.REJECT

    def test_existing_client_rejected(self) -> None:
        result = self.engine.evaluate("Acme Corp")
        assert result.decision == QualityDecision.REJECT
        assert result.category == "existing_client"
        assert "EXISTING_CLIENT" in result.reasons

    def test_demo_company_rejected(self) -> None:
        result = self.engine.evaluate("Demo Company")
        assert result.decision == QualityDecision.REJECT
        assert result.category == "demo_company"
        assert "DEMO_COMPANY" in result.reasons

    def test_internal_test_rejected(self) -> None:
        result = self.engine.evaluate("Test Company")
        assert result.decision == QualityDecision.REJECT
        assert result.category == "internal_test"

    def test_partner_not_rejected(self) -> None:
        result = self.engine.evaluate("Deloitte")
        assert result.decision == QualityDecision.ACCEPT

    def test_gate_name(self) -> None:
        assert self.engine.gate_name() == QualityGate.COMPETITOR_CHECK.value

    def test_empty_config_accepts_all(self) -> None:
        engine = CompetitorEngine(config=CompetitorConfig())
        result = engine.evaluate("Google")
        assert result.decision == QualityDecision.ACCEPT

    def test_case_insensitive(self) -> None:
        result = self.engine.evaluate("GOOGLE")
        assert result.decision == QualityDecision.REJECT

    def test_partial_name_match(self) -> None:
        result = self.engine.evaluate("microsoft corporation")
        assert result.decision == QualityDecision.REJECT


class TestCompetitorConfig:
    def test_empty_config(self) -> None:
        config = CompetitorConfig()
        assert config.competitors == []
        assert config.partners == []
        assert config.existing_clients == []
        assert config.internal_test == []
        assert config.demo_companies == []

    def test_all_blocked(self) -> None:
        config = CompetitorConfig(
            competitors=["a"],
            partners=["b"],
            existing_clients=["c"],
            internal_test=["d"],
            demo_companies=["e"],
        )
        blocked = config.all_blocked()
        assert len(blocked) == 5

    def test_from_yaml_missing_file(self) -> None:
        config = CompetitorConfig.from_yaml("/nonexistent/path.yaml")
        assert config.competitors == []
