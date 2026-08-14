"""Tests for SourceQualityEngine."""

from __future__ import annotations

from discovery_quality_engine.source_quality import SourceQualityEngine, SourceTrustResult
from discovery_quality_engine.quality_engine import QualityDecision, QualityGate, RejectionReason


class TestSourceQualityEngine:
    def setup_method(self) -> None:
        self.engine = SourceQualityEngine()

    def test_linkedin_high_trust(self) -> None:
        result = self.engine.evaluate("linkedin")
        assert result.decision == QualityDecision.ACCEPT
        assert result.trust_score == 98.0

    def test_company_website_high_trust(self) -> None:
        result = self.engine.evaluate("company_website")
        assert result.decision == QualityDecision.ACCEPT
        assert result.trust_score == 97.0

    def test_crunchbase_high_trust(self) -> None:
        result = self.engine.evaluate("crunchbase")
        assert result.decision == QualityDecision.ACCEPT
        assert result.trust_score == 95.0

    def test_government_high_trust(self) -> None:
        result = self.engine.evaluate("government")
        assert result.decision == QualityDecision.ACCEPT
        assert result.trust_score == 95.0

    def test_github_medium_trust(self) -> None:
        result = self.engine.evaluate("github")
        assert result.decision == QualityDecision.ACCEPT
        assert result.trust_score == 88.0

    def test_twitter_medium_trust(self) -> None:
        result = self.engine.evaluate("twitter")
        assert result.decision == QualityDecision.ACCEPT
        assert result.trust_score == 82.0

    def test_rss_medium_trust(self) -> None:
        result = self.engine.evaluate("rss")
        assert result.decision == QualityDecision.ACCEPT
        assert result.trust_score == 71.0

    def test_unknown_blog_low_trust(self) -> None:
        result = self.engine.evaluate("unknown_blog")
        assert result.decision == QualityDecision.REJECT
        assert result.trust_score == 42.0

    def test_unknown_source_default_trust(self) -> None:
        result = self.engine.evaluate("random_source")
        assert result.decision == QualityDecision.REJECT
        assert result.trust_score == 50.0

    def test_custom_min_trust(self) -> None:
        engine = SourceQualityEngine(min_trust=40.0)
        result = engine.evaluate("unknown_blog")
        assert result.decision == QualityDecision.ACCEPT

    def test_custom_source_trust(self) -> None:
        engine = SourceQualityEngine(source_trust={"custom_source": 99.0})
        result = engine.evaluate("custom_source")
        assert result.decision == QualityDecision.ACCEPT
        assert result.trust_score == 99.0

    def test_gate_name(self) -> None:
        assert self.engine.gate_name() == QualityGate.SOURCE_TRUST.value

    def test_rejection_includes_low_source_trust(self) -> None:
        result = self.engine.evaluate("unknown_blog")
        assert "LOW_SOURCE_TRUST" in result.reasons

    def test_case_insensitive(self) -> None:
        result = self.engine.evaluate("LinkedIn")
        assert result.decision == QualityDecision.ACCEPT

    def test_whitespace_handled(self) -> None:
        result = self.engine.evaluate("  linkedin  ")
        assert result.decision == QualityDecision.ACCEPT

    def test_result_has_source(self) -> None:
        result = self.engine.evaluate("linkedin")
        assert result.source == "linkedin"
