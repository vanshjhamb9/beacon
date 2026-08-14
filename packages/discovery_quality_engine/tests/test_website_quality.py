"""Tests for WebsiteQualityEngine."""

from __future__ import annotations

from discovery_quality_engine.website_quality import WebsiteQualityEngine, WebsiteQualityResult
from discovery_quality_engine.quality_engine import QualityDecision, QualityGate, RejectionReason


class TestWebsiteQualityEngine:
    def setup_method(self) -> None:
        self.engine = WebsiteQualityEngine()

    def test_valid_website_accepted(self) -> None:
        result = self.engine.evaluate("https://example.com")
        assert result.decision == QualityDecision.ACCEPT

    def test_missing_website_rejected(self) -> None:
        result = self.engine.evaluate(None)
        assert result.decision == QualityDecision.REJECT
        assert "Missing website" in result.reasons

    def test_empty_website_rejected(self) -> None:
        result = self.engine.evaluate("")
        assert result.decision == QualityDecision.REJECT

    def test_no_https_rejected(self) -> None:
        result = self.engine.evaluate("http://example.com", has_https=False)
        assert result.decision == QualityDecision.REJECT
        assert "NO_HTTPS" in result.reasons

    def test_parked_domain_rejected(self) -> None:
        result = self.engine.evaluate("https://example.com", page_text="This domain is parked and for sale")
        assert result.decision == QualityDecision.REJECT
        assert "PARKED_DOMAIN" in result.reasons

    def test_coming_soon_rejected(self) -> None:
        result = self.engine.evaluate("https://example.com", page_text="Coming soon! We are under construction.")
        assert result.decision == QualityDecision.REJECT

    def test_maintenance_rejected(self) -> None:
        result = self.engine.evaluate("https://example.com", page_text="Site is under maintenance")
        assert result.decision == QualityDecision.REJECT

    def test_404_rejected(self) -> None:
        result = self.engine.evaluate("https://example.com", page_text="404 page not found error")
        assert result.decision == QualityDecision.REJECT

    def test_spam_rejected(self) -> None:
        result = self.engine.evaluate("https://example.com", page_text="This is spam content")
        assert result.decision == QualityDecision.REJECT

    def test_low_content_rejected(self) -> None:
        result = self.engine.evaluate("https://example.com", content_length=50)
        assert result.decision == QualityDecision.REJECT
        assert "LOW_CONTENT" in result.reasons

    def test_sufficient_content_accepted(self) -> None:
        result = self.engine.evaluate("https://example.com", content_length=300)
        assert result.decision == QualityDecision.ACCEPT

    def test_domain_for_sale_rejected(self) -> None:
        result = self.engine.evaluate("https://example.com", page_text="Buy this domain")
        assert result.decision == QualityDecision.REJECT

    def test_temporarily_unavailable_rejected(self) -> None:
        result = self.engine.evaluate("https://example.com", page_text="Temporarily unavailable")
        assert result.decision == QualityDecision.REJECT

    def test_gate_name(self) -> None:
        assert self.engine.gate_name() == QualityGate.WEBSITE_QUALITY.value

    def test_domain_extracted_from_url(self) -> None:
        result = self.engine.evaluate("https://www.example.com/path/page")
        assert result.domain == "www.example.com"

    def test_valid_website_with_content(self) -> None:
        result = self.engine.evaluate(
            "https://example.com",
            has_https=True,
            content_length=500,
            page_text="A legitimate company website with real content about their products and services.",
        )
        assert result.decision == QualityDecision.ACCEPT

    def test_custom_min_content(self) -> None:
        engine = WebsiteQualityEngine(min_content_length=1000)
        result = engine.evaluate("https://example.com", content_length=500)
        assert result.decision == QualityDecision.REJECT

    def test_custom_parked_keywords(self) -> None:
        engine = WebsiteQualityEngine(parked_keywords=frozenset({"custom_keyword"}))
        result = engine.evaluate("https://example.com", page_text="This has custom_keyword in it")
        assert result.decision == QualityDecision.REJECT

    def test_no_https_with_valid_url(self) -> None:
        result = self.engine.evaluate("https://example.com", has_https=True)
        assert result.decision == QualityDecision.ACCEPT

    def test_wellbe_back_soon(self) -> None:
        result = self.engine.evaluate("https://example.com", page_text="We'll be back soon")
        assert result.decision == QualityDecision.REJECT

    def test_click_here_to_buy(self) -> None:
        result = self.engine.evaluate("https://example.com", page_text="Click here to buy this domain")
        assert result.decision == QualityDecision.REJECT

    def test_domain_expired(self) -> None:
        result = self.engine.evaluate("https://example.com", page_text="Domain expired")
        assert result.decision == QualityDecision.REJECT

    def test_under_construction(self) -> None:
        result = self.engine.evaluate("https://example.com", page_text="Under construction")
        assert result.decision == QualityDecision.REJECT

    def test_sorry_for_inconvenience(self) -> None:
        result = self.engine.evaluate("https://example.com", page_text="Sorry for the inconvenience")
        assert result.decision == QualityDecision.REJECT
