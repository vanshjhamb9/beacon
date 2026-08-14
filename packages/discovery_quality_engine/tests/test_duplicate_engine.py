"""Tests for DuplicateEngine."""

from __future__ import annotations

from discovery_quality_engine.duplicate_engine import DuplicateEngine, DuplicateResult
from discovery_quality_engine.quality_engine import QualityDecision, QualityGate, RejectionReason


class TestDuplicateEngine:
    def setup_method(self) -> None:
        self.engine = DuplicateEngine()

    def test_unique_domain_accepted(self) -> None:
        result = self.engine.check_domain("example.com")
        assert result.decision == QualityDecision.ACCEPT

    def test_duplicate_domain_rejected(self) -> None:
        self.engine.check_domain("example.com")
        result = self.engine.check_domain("example.com")
        assert result.decision == QualityDecision.REJECT
        assert "DUPLICATE_DOMAIN" in result.reasons

    def test_www_stripped(self) -> None:
        self.engine.check_domain("www.example.com")
        result = self.engine.check_domain("example.com")
        assert result.decision == QualityDecision.REJECT

    def test_https_stripped(self) -> None:
        self.engine.check_domain("https://example.com")
        result = self.engine.check_domain("example.com")
        assert result.decision == QualityDecision.REJECT

    def test_http_stripped(self) -> None:
        self.engine.check_domain("http://example.com")
        result = self.engine.check_domain("example.com")
        assert result.decision == QualityDecision.REJECT

    def test_path_stripped(self) -> None:
        self.engine.check_domain("example.com/path")
        result = self.engine.check_domain("example.com")
        assert result.decision == QualityDecision.REJECT

    def test_port_stripped(self) -> None:
        self.engine.check_domain("example.com:8080")
        result = self.engine.check_domain("example.com")
        assert result.decision == QualityDecision.REJECT

    def test_unique_company_accepted(self) -> None:
        result = self.engine.check_company("Acme Corp")
        assert result.decision == QualityDecision.ACCEPT

    def test_duplicate_company_rejected(self) -> None:
        self.engine.check_company("Acme Corp")
        result = self.engine.check_company("Acme Corp")
        assert result.decision == QualityDecision.REJECT
        assert "DUPLICATE_COMPANY" in result.reasons

    def test_company_normalization(self) -> None:
        self.engine.check_company("Acme Inc.")
        result = self.engine.check_company("Acme")
        assert result.decision == QualityDecision.REJECT

    def test_company_normalization_llc(self) -> None:
        self.engine.check_company("Acme LLC")
        result = self.engine.check_company("Acme")
        assert result.decision == QualityDecision.REJECT

    def test_company_normalization_ltd(self) -> None:
        self.engine.check_company("Acme Ltd")
        result = self.engine.check_company("Acme")
        assert result.decision == QualityDecision.REJECT

    def test_company_normalization_corp(self) -> None:
        self.engine.check_company("Acme Corp")
        result = self.engine.check_company("Acme")
        assert result.decision == QualityDecision.REJECT

    def test_unique_opportunity_accepted(self) -> None:
        result = self.engine.check_opportunity("Acme", "HIRING", "linkedin")
        assert result.decision == QualityDecision.ACCEPT

    def test_duplicate_opportunity_rejected(self) -> None:
        self.engine.check_opportunity("Acme", "HIRING", "linkedin")
        result = self.engine.check_opportunity("Acme", "HIRING", "linkedin")
        assert result.decision == QualityDecision.REJECT
        assert "DUPLICATE_OPPORTUNITY" in result.reasons

    def test_different_signal_type_unique(self) -> None:
        self.engine.check_opportunity("Acme", "HIRING", "linkedin")
        result = self.engine.check_opportunity("Acme", "FUNDING", "linkedin")
        assert result.decision == QualityDecision.ACCEPT

    def test_different_company_unique(self) -> None:
        self.engine.check_opportunity("Acme", "HIRING", "linkedin")
        result = self.engine.check_opportunity("Beta Corp", "HIRING", "linkedin")
        assert result.decision == QualityDecision.ACCEPT

    def test_unique_evidence_accepted(self) -> None:
        result = self.engine.check_evidence("https://example.com/article", "Title")
        assert result.decision == QualityDecision.ACCEPT

    def test_duplicate_evidence_rejected(self) -> None:
        self.engine.check_evidence("https://example.com/article", "Title")
        result = self.engine.check_evidence("https://example.com/article", "Title")
        assert result.decision == QualityDecision.REJECT
        assert "DUPLICATE_EVIDENCE" in result.reasons

    def test_unique_signal_accepted(self) -> None:
        result = self.engine.check_signal("Acme", "HIRING")
        assert result.decision == QualityDecision.ACCEPT

    def test_duplicate_signal_rejected(self) -> None:
        self.engine.check_signal("Acme", "HIRING")
        result = self.engine.check_signal("Acme", "HIRING")
        assert result.decision == QualityDecision.REJECT
        assert "DUPLICATE_SIGNAL" in result.reasons

    def test_reset_clears_all(self) -> None:
        self.engine.check_domain("example.com")
        self.engine.check_company("Acme")
        self.engine.reset()
        result = self.engine.check_domain("example.com")
        assert result.decision == QualityDecision.ACCEPT

    def test_gate_name(self) -> None:
        assert self.engine.gate_name() == QualityGate.DUPLICATE_CHECK.value

    def test_duplicate_key_populated(self) -> None:
        result = self.engine.check_domain("example.com")
        assert result.duplicate_key.startswith("domain:")

    def test_company_duplicate_key_populated(self) -> None:
        result = self.engine.check_company("Acme")
        assert result.duplicate_key.startswith("company:")

    def test_opportunity_duplicate_key_populated(self) -> None:
        result = self.engine.check_opportunity("Acme", "HIRING", "linkedin")
        assert result.duplicate_key.startswith("opportunity:")

    def test_evidence_duplicate_key_populated(self) -> None:
        result = self.engine.check_evidence("url", "title")
        assert result.duplicate_key.startswith("evidence:")

    def test_signal_duplicate_key_populated(self) -> None:
        result = self.engine.check_signal("Acme", "HIRING")
        assert result.duplicate_key.startswith("signal:")
