"""Additional deterministic tests for DQE coverage — 600+ total."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from discovery_quality_engine.activity_engine import ActivityEngine, ActivityEvidence
from discovery_quality_engine.buying_signal_engine import BuyingSignalEngine
from discovery_quality_engine.company_age import CompanyAgeFilter
from discovery_quality_engine.company_filter import CompanyFilter
from discovery_quality_engine.competitor_engine import CompetitorConfig, CompetitorEngine
from discovery_quality_engine.duplicate_engine import DuplicateEngine
from discovery_quality_engine.freshness_engine import FreshnessEngine
from discovery_quality_engine.industry_filter import IndustryFilter
from discovery_quality_engine.quality_dashboard import QualityDashboard
from discovery_quality_engine.quality_engine import (
    QualityDecision,
    QualityEvent,
    QualityGate,
    QualitySnapshot,
    RejectionReason,
    SignalType,
)
from discovery_quality_engine.quality_metrics import QualityMetricsCollector
from discovery_quality_engine.quality_reports import QualityReportGenerator
from discovery_quality_engine.quality_scheduler import QualityScheduler
from discovery_quality_engine.region_filter import RegionFilter
from discovery_quality_engine.signal_filter import SignalFilter
from discovery_quality_engine.source_quality import SourceQualityEngine
from discovery_quality_engine.technology_filter import TechnologyFilter
from discovery_quality_engine.website_quality import WebsiteQualityEngine
from discovery_quality_engine.dqe_orchestrator import DQEOrchestrator
from discovery_quality_engine.competitor_engine import CompetitorEngine


# ═══════════════════════════════════════════════════════════════════════════════
# FreshnessEngine — additional boundary and type tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFreshnessAdditional:
    def setup_method(self) -> None:
        self.engine = FreshnessEngine()

    def test_hiring_at_29_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("HIRING", now - timedelta(days=29), now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_hiring_at_30_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("HIRING", now - timedelta(days=30), now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_hiring_at_31_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("HIRING", now - timedelta(days=31), now=now)
        assert result.decision == QualityDecision.REJECT

    def test_funding_at_89_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("FUNDING", now - timedelta(days=89), now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_funding_at_91_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("FUNDING", now - timedelta(days=91), now=now)
        assert result.decision == QualityDecision.REJECT

    def test_conference_at_14_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("CONFERENCE", now - timedelta(days=14), now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_conference_at_16_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("CONFERENCE", now - timedelta(days=16), now=now)
        assert result.decision == QualityDecision.REJECT

    def test_award_at_30_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("AWARD", now - timedelta(days=30), now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_press_release_at_31_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("PRESS_RELEASE", now - timedelta(days=31), now=now)
        assert result.decision == QualityDecision.REJECT

    def test_partnership_at_45_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("PARTNERSHIP", now - timedelta(days=45), now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_partnership_at_46_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("PARTNERSHIP", now - timedelta(days=46), now=now)
        assert result.decision == QualityDecision.REJECT

    def test_expansion_at_90_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("EXPANSION", now - timedelta(days=90), now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_technology_adoption_at_60_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("TECHNOLOGY_ADOPTION", now - timedelta(days=60), now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_technology_adoption_at_61_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("TECHNOLOGY_ADOPTION", now - timedelta(days=61), now=now)
        assert result.decision == QualityDecision.REJECT

    def test_result_reasons_is_tuple(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("HIRING", now - timedelta(days=5), now=now)
        assert isinstance(result.reasons, tuple)

    def test_reject_result_has_max_age(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("HIRING", now - timedelta(days=45), now=now)
        assert result.max_age_days == 30

    def test_accept_result_has_max_age(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("HIRING", now - timedelta(days=5), now=now)
        assert result.max_age_days == 30

    def test_signal_type_preserved(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.engine.evaluate("FUNDING", now - timedelta(days=5), now=now)
        assert result.signal_type == "FUNDING"


# ═══════════════════════════════════════════════════════════════════════════════
# BuyingSignalEngine — additional tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuyingSignalAdditional:
    def setup_method(self) -> None:
        self.engine = BuyingSignalEngine()

    def test_single_valid_hiring(self) -> None:
        result = self.engine.evaluate(["HIRING"])
        assert result.decision == QualityDecision.ACCEPT
        assert len(result.signals_found) == 1

    def test_two_valid_signals(self) -> None:
        result = self.engine.evaluate(["HIRING", "FUNDING"])
        assert result.decision == QualityDecision.ACCEPT
        assert len(result.signals_found) == 2

    def test_all_valid_14_types(self) -> None:
        signals = [
            "HIRING", "FUNDING", "PRODUCT_LAUNCH", "TECHNOLOGY_ADOPTION",
            "PARTNERSHIP", "EXPANSION", "COMPLIANCE", "EXECUTIVE_HIRING",
            "OFFICE_EXPANSION", "ACQUISITION", "INFRASTRUCTURE_UPGRADE",
            "SECURITY_INCIDENT", "API_RELEASE", "MARKETPLACE_EXPANSION",
        ]
        result = self.engine.evaluate(signals)
        assert result.decision == QualityDecision.ACCEPT
        assert len(result.signals_found) == 14

    def test_mixed_valid_invalid_5_valid(self) -> None:
        result = self.engine.evaluate(["HIRING", "FOO", "FUNDING", "BAR", "EXPANSION"])
        assert result.decision == QualityDecision.ACCEPT
        assert len(result.signals_found) == 3

    def test_all_invalid_5(self) -> None:
        result = self.engine.evaluate(["A", "B", "C", "D", "E"])
        assert result.decision == QualityDecision.REJECT
        assert len(result.signals_found) == 0

    def test_duplicate_valid_signals(self) -> None:
        result = self.engine.evaluate(["HIRING", "HIRING", "HIRING"])
        assert result.decision == QualityDecision.ACCEPT
        assert len(result.signals_found) == 3

    def test_result_reasons_is_tuple(self) -> None:
        result = self.engine.evaluate(["HIRING"])
        assert isinstance(result.reasons, tuple)

    def test_result_signals_found_is_list(self) -> None:
        result = self.engine.evaluate(["HIRING", "FUNDING"])
        assert isinstance(result.signals_found, list)


# ═══════════════════════════════════════════════════════════════════════════════
# CompanyFilter — additional tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCompanyFilterAdditional:
    def setup_method(self) -> None:
        self.filter = CompanyFilter()

    def test_3_char_name(self) -> None:
        result = self.filter.evaluate(company_name="ABC")
        assert result.decision == QualityDecision.ACCEPT

    def test_255_char_name(self) -> None:
        result = self.filter.evaluate(company_name="A" * 255)
        assert result.decision == QualityDecision.ACCEPT

    def test_name_with_numbers(self) -> None:
        result = self.filter.evaluate(company_name="Company123")
        assert result.decision == QualityDecision.ACCEPT

    def test_name_with_special_chars(self) -> None:
        result = self.filter.evaluate(company_name="Acme & Co.")
        assert result.decision == QualityDecision.ACCEPT

    def test_name_with_unicode(self) -> None:
        result = self.filter.evaluate(company_name="Munich GmbH")
        assert result.decision == QualityDecision.ACCEPT

    def test_whitespace_only(self) -> None:
        result = self.filter.evaluate(company_name="     ")
        assert result.decision == QualityDecision.REJECT

    def test_single_space(self) -> None:
        result = self.filter.evaluate(company_name=" ")
        assert result.decision == QualityDecision.REJECT

    def test_tab_only(self) -> None:
        result = self.filter.evaluate(company_name="\t")
        assert result.decision == QualityDecision.REJECT

    def test_newline_only(self) -> None:
        result = self.filter.evaluate(company_name="\n")
        assert result.decision == QualityDecision.REJECT


# ═══════════════════════════════════════════════════════════════════════════════
# DuplicateEngine — additional hash and normalization tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestDuplicateAdditional:
    def setup_method(self) -> None:
        self.engine = DuplicateEngine()

    def test_10_unique_domains(self) -> None:
        for i in range(10):
            result = self.engine.check_domain(f"domain{i}.com")
            assert result.decision == QualityDecision.ACCEPT

    def test_10_unique_companies(self) -> None:
        for i in range(10):
            result = self.engine.check_company(f"Company {i}")
            assert result.decision == QualityDecision.ACCEPT

    def test_10_unique_opportunities(self) -> None:
        for i in range(10):
            result = self.engine.check_opportunity(f"Company {i}", "HIRING", "linkedin")
            assert result.decision == QualityDecision.ACCEPT

    def test_10_unique_evidence(self) -> None:
        for i in range(10):
            result = self.engine.check_evidence(f"https://example.com/{i}", f"Title {i}")
            assert result.decision == QualityDecision.ACCEPT

    def test_10_unique_signals(self) -> None:
        for i in range(10):
            result = self.engine.check_signal(f"Company {i}", "HIRING")
            assert result.decision == QualityDecision.ACCEPT

    def test_domain_key_format(self) -> None:
        result = self.engine.check_domain("test.com")
        assert result.duplicate_key.startswith("domain:")
        assert len(result.duplicate_key) > 7

    def test_company_key_format(self) -> None:
        result = self.engine.check_company("Test")
        assert result.duplicate_key.startswith("company:")
        assert len(result.duplicate_key) > 8

    def test_opportunity_key_format(self) -> None:
        result = self.engine.check_opportunity("Test", "HIRING", "web")
        assert result.duplicate_key.startswith("opportunity:")
        assert len(result.duplicate_key) > 12

    def test_evidence_key_format(self) -> None:
        result = self.engine.check_evidence("url", "title")
        assert result.duplicate_key.startswith("evidence:")
        assert len(result.duplicate_key) > 9

    def test_signal_key_format(self) -> None:
        result = self.engine.check_signal("Test", "HIRING")
        assert result.duplicate_key.startswith("signal:")
        assert len(result.duplicate_key) > 7

    def test_domain_with_multiple_slashes(self) -> None:
        self.engine.check_domain("a.com/x/y/z")
        result = self.engine.check_domain("a.com")
        assert result.decision == QualityDecision.REJECT

    def test_domain_with_query_params(self) -> None:
        self.engine.check_domain("a.com?foo=bar")
        result = self.engine.check_domain("a.com?foo=bar")
        assert result.decision == QualityDecision.REJECT

    def test_domain_with_fragment(self) -> None:
        self.engine.check_domain("a.com#section")
        result = self.engine.check_domain("a.com#section")
        assert result.decision == QualityDecision.REJECT


# ═══════════════════════════════════════════════════════════════════════════════
# CompetitorEngine — additional tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCompetitorAdditional:
    def setup_method(self) -> None:
        self.config = CompetitorConfig(
            competitors=["alpha", "beta", "gamma"],
            partners=["partner1"],
            existing_clients=["client1"],
            internal_test=["test1"],
            demo_companies=["demo1"],
        )
        self.engine = CompetitorEngine(config=self.config)

    def test_alpha_exact(self) -> None:
        result = self.engine.evaluate("alpha")
        assert result.decision == QualityDecision.REJECT
        assert result.category == "competitor"

    def test_beta_exact(self) -> None:
        result = self.engine.evaluate("beta")
        assert result.decision == QualityDecision.REJECT

    def test_gamma_exact(self) -> None:
        result = self.engine.evaluate("gamma")
        assert result.decision == QualityDecision.REJECT

    def test_alpha_inc(self) -> None:
        result = self.engine.evaluate("alpha inc")
        assert result.decision == QualityDecision.REJECT

    def test_partner1(self) -> None:
        result = self.engine.evaluate("partner1")
        assert result.decision == QualityDecision.ACCEPT

    def test_client1(self) -> None:
        result = self.engine.evaluate("client1")
        assert result.decision == QualityDecision.REJECT
        assert result.category == "existing_client"

    def test_test1(self) -> None:
        result = self.engine.evaluate("test1")
        assert result.decision == QualityDecision.REJECT
        assert result.category == "internal_test"

    def test_demo1(self) -> None:
        result = self.engine.evaluate("demo1")
        assert result.decision == QualityDecision.REJECT
        assert result.category == "demo_company"

    def test_unrelated_company(self) -> None:
        result = self.engine.evaluate("unrelated company")
        assert result.decision == QualityDecision.ACCEPT

    def test_case_insensitive_alpha(self) -> None:
        result = self.engine.evaluate("ALPHA")
        assert result.decision == QualityDecision.REJECT

    def test_case_insensitive_beta(self) -> None:
        result = self.engine.evaluate("BETA")
        assert result.decision == QualityDecision.REJECT

    def test_case_insensitive_gamma(self) -> None:
        result = self.engine.evaluate("GAMMA")
        assert result.decision == QualityDecision.REJECT

    def test_empty_name(self) -> None:
        result = self.engine.evaluate("")
        assert result.decision == QualityDecision.REJECT

    def test_config_all_blocked_count(self) -> None:
        blocked = self.config.all_blocked()
        assert len(blocked) == 7


# ═══════════════════════════════════════════════════════════════════════════════
# IndustryFilter — additional tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestIndustryAdditional:
    def setup_method(self) -> None:
        self.filter = IndustryFilter()

    def test_all_default_industries_accepted(self) -> None:
        industries = [
            "technology", "software", "saas", "fintech", "healthtech",
            "edtech", "ecommerce", "retail", "manufacturing", "healthcare",
            "finance", "insurance", "real estate", "construction", "energy",
            "utilities", "transportation", "logistics", "telecommunications",
            "media", "entertainment", "education", "professional services",
            "consulting", "legal", "accounting", "marketing", "advertising",
            "nonprofit", "government", "agriculture", "mining", "automotive",
            "aerospace", "defense", "pharmaceuticals", "biotechnology",
            "food and beverage", "hospitality", "travel", "sports", "recreation",
        ]
        for industry in industries:
            result = self.filter.evaluate(industry)
            assert result.decision == QualityDecision.ACCEPT, f"Industry '{industry}' should be accepted"

    def test_custom_industry_set(self) -> None:
        f = IndustryFilter(allowed_industries=frozenset({"crypto", "blockchain"}))
        assert f.evaluate("crypto").decision == QualityDecision.ACCEPT
        assert f.evaluate("blockchain").decision == QualityDecision.ACCEPT
        assert f.evaluate("technology").decision == QualityDecision.REJECT

    def test_empty_industry_set_rejects_all(self) -> None:
        f = IndustryFilter(allowed_industries=frozenset())
        assert f.evaluate("nonexistent").decision == QualityDecision.REJECT


# ═══════════════════════════════════════════════════════════════════════════════
# RegionFilter — additional tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegionAdditional:
    def setup_method(self) -> None:
        self.filter = RegionFilter()

    def test_all_default_regions_accepted(self) -> None:
        regions = ["US", "CA", "UK", "GB", "EU", "DE", "FR", "NL", "SE", "NO", "DK", "FI", "IE", "ES", "IT", "AU", "AE", "SA", "IN", "SG"]
        for region in regions:
            result = self.filter.evaluate(region)
            assert result.decision == QualityDecision.ACCEPT, f"Region '{region}' should be accepted"

    def test_unsupported_regions_rejected(self) -> None:
        regions = ["KP", "IR", "SY", "VE", "CU", "MM", "BY"]
        for region in regions:
            result = self.filter.evaluate(region)
            assert result.decision == QualityDecision.REJECT, f"Region '{region}' should be rejected"

    def test_custom_region_set(self) -> None:
        f = RegionFilter(supported_regions=["US", "JP", "KR"])
        assert f.evaluate("JP").decision == QualityDecision.ACCEPT
        assert f.evaluate("KR").decision == QualityDecision.ACCEPT
        assert f.evaluate("UK").decision == QualityDecision.REJECT


# ═══════════════════════════════════════════════════════════════════════════════
# SourceQualityEngine — additional tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSourceAdditional:
    def setup_method(self) -> None:
        self.engine = SourceQualityEngine()

    def test_linkedin_trust_98(self) -> None:
        result = self.engine.evaluate("linkedin")
        assert result.trust_score == 98.0

    def test_company_website_trust_97(self) -> None:
        result = self.engine.evaluate("company_website")
        assert result.trust_score == 97.0

    def test_crunchbase_trust_95(self) -> None:
        result = self.engine.evaluate("crunchbase")
        assert result.trust_score == 95.0

    def test_government_trust_95(self) -> None:
        result = self.engine.evaluate("government")
        assert result.trust_score == 95.0

    def test_github_trust_88(self) -> None:
        result = self.engine.evaluate("github")
        assert result.trust_score == 88.0

    def test_twitter_trust_82(self) -> None:
        result = self.engine.evaluate("twitter")
        assert result.trust_score == 82.0

    def test_rss_trust_71(self) -> None:
        result = self.engine.evaluate("rss")
        assert result.trust_score == 71.0

    def test_unknown_blog_trust_42(self) -> None:
        result = self.engine.evaluate("unknown_blog")
        assert result.trust_score == 42.0

    def test_unknown_source_trust_50(self) -> None:
        result = self.engine.evaluate("random")
        assert result.trust_score == 50.0

    def test_custom_min_90_rejects_88(self) -> None:
        engine = SourceQualityEngine(min_trust=90.0)
        result = engine.evaluate("github")
        assert result.decision == QualityDecision.REJECT

    def test_custom_min_80_accepts_88(self) -> None:
        engine = SourceQualityEngine(min_trust=80.0)
        result = engine.evaluate("github")
        assert result.decision == QualityDecision.ACCEPT


# ═══════════════════════════════════════════════════════════════════════════════
# WebsiteQualityEngine — additional tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestWebsiteAdditional:
    def setup_method(self) -> None:
        self.engine = WebsiteQualityEngine()

    def test_https_url_accepted(self) -> None:
        result = self.engine.evaluate("https://example.com")
        assert result.decision == QualityDecision.ACCEPT

    def test_http_no_https_check_accepted(self) -> None:
        result = self.engine.evaluate("http://example.com")
        assert result.decision == QualityDecision.ACCEPT

    def test_http_with_https_false_rejected(self) -> None:
        result = self.engine.evaluate("http://example.com", has_https=False)
        assert result.decision == QualityDecision.REJECT

    def test_content_199_rejected(self) -> None:
        engine = WebsiteQualityEngine(min_content_length=200)
        result = engine.evaluate("https://example.com", content_length=199)
        assert result.decision == QualityDecision.REJECT

    def test_content_201_accepted(self) -> None:
        engine = WebsiteQualityEngine(min_content_length=200)
        result = engine.evaluate("https://example.com", content_length=201)
        assert result.decision == QualityDecision.ACCEPT

    def test_parked_domain_keyword(self) -> None:
        result = self.engine.evaluate("https://x.com", page_text="This domain is parked")
        assert result.decision == QualityDecision.REJECT

    def test_for_sale_keyword(self) -> None:
        result = self.engine.evaluate("https://x.com", page_text="Domain for sale")
        assert result.decision == QualityDecision.REJECT

    def test_under_construction_keyword(self) -> None:
        result = self.engine.evaluate("https://x.com", page_text="Under construction")
        assert result.decision == QualityDecision.REJECT

    def test_temporarily_unavailable_keyword(self) -> None:
        result = self.engine.evaluate("https://x.com", page_text="Temporarily unavailable")
        assert result.decision == QualityDecision.REJECT

    def test_page_not_found_keyword(self) -> None:
        result = self.engine.evaluate("https://x.com", page_text="Page not found")
        assert result.decision == QualityDecision.REJECT

    def test_error_keyword(self) -> None:
        result = self.engine.evaluate("https://x.com", page_text="error 404")
        assert result.decision == QualityDecision.REJECT

    def test_spam_keyword(self) -> None:
        result = self.engine.evaluate("https://x.com", page_text="This is spam")
        assert result.decision == QualityDecision.REJECT

    def test_click_here_to_buy_keyword(self) -> None:
        result = self.engine.evaluate("https://x.com", page_text="Click here to buy")
        assert result.decision == QualityDecision.REJECT

    def test_domain_expired_keyword(self) -> None:
        result = self.engine.evaluate("https://x.com", page_text="Domain expired")
        assert result.decision == QualityDecision.REJECT

    def test_we_back_soon_keyword(self) -> None:
        result = self.engine.evaluate("https://x.com", page_text="We'll be back soon")
        assert result.decision == QualityDecision.REJECT

    def test_sorry_inconvenience_keyword(self) -> None:
        result = self.engine.evaluate("https://x.com", page_text="Sorry for the inconvenience")
        assert result.decision == QualityDecision.REJECT

    def test_valid_website_no_issues(self) -> None:
        result = self.engine.evaluate(
            "https://example.com",
            has_https=True,
            content_length=1000,
            page_text="Welcome to our company. We provide excellent services.",
        )
        assert result.decision == QualityDecision.ACCEPT


# ═══════════════════════════════════════════════════════════════════════════════
# CompanyAgeFilter — additional tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCompanyAgeAdditional:
    def setup_method(self) -> None:
        self.filter = CompanyAgeFilter()

    def test_age_0_min_0_accepted(self) -> None:
        f = CompanyAgeFilter(min_age_days=0)
        assert f.evaluate(0).decision == QualityDecision.ACCEPT

    def test_age_29_min_30_rejected(self) -> None:
        assert self.filter.evaluate(29).decision == QualityDecision.REJECT

    def test_age_30_min_30_accepted(self) -> None:
        assert self.filter.evaluate(30).decision == QualityDecision.ACCEPT

    def test_age_36500_max_36500_accepted(self) -> None:
        assert self.filter.evaluate(36500).decision == QualityDecision.ACCEPT

    def test_age_36501_max_36500_rejected(self) -> None:
        assert self.filter.evaluate(36501).decision == QualityDecision.REJECT

    def test_age_none_accepted(self) -> None:
        assert self.filter.evaluate(None).decision == QualityDecision.ACCEPT

    def test_age_100_accepted(self) -> None:
        assert self.filter.evaluate(100).decision == QualityDecision.ACCEPT

    def test_age_1000_accepted(self) -> None:
        assert self.filter.evaluate(1000).decision == QualityDecision.ACCEPT

    def test_age_10000_accepted(self) -> None:
        assert self.filter.evaluate(10000).decision == QualityDecision.ACCEPT


# ═══════════════════════════════════════════════════════════════════════════════
# TechnologyFilter — additional tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestTechnologyAdditional:
    def setup_method(self) -> None:
        self.filter = TechnologyFilter()

    def test_ai_model_rejected(self) -> None:
        assert self.filter.evaluate(description="We build AI models").decision == QualityDecision.REJECT

    def test_llm_rejected(self) -> None:
        assert self.filter.evaluate(description="Our LLM platform").decision == QualityDecision.REJECT

    def test_ai_startup_rejected(self) -> None:
        assert self.filter.evaluate(description="AI startup from YC").decision == QualityDecision.REJECT

    def test_open_source_ai_rejected(self) -> None:
        assert self.filter.evaluate(description="Open source AI tools").decision == QualityDecision.REJECT

    def test_ai_developer_tools_rejected(self) -> None:
        assert self.filter.evaluate(description="AI developer tools").decision == QualityDecision.REJECT

    def test_ai_infrastructure_rejected(self) -> None:
        assert self.filter.evaluate(description="AI infrastructure").decision == QualityDecision.REJECT

    def test_llm_sdk_rejected(self) -> None:
        assert self.filter.evaluate(description="LLM SDK").decision == QualityDecision.REJECT

    def test_model_hosting_rejected(self) -> None:
        assert self.filter.evaluate(description="Model hosting platform").decision == QualityDecision.REJECT

    def test_prompt_engineering_rejected(self) -> None:
        assert self.filter.evaluate(description="Prompt engineering tools").decision == QualityDecision.REJECT

    def test_inference_platform_rejected(self) -> None:
        assert self.filter.evaluate(description="Inference platform").decision == QualityDecision.REJECT

    def test_ai_framework_rejected(self) -> None:
        assert self.filter.evaluate(description="AI framework for deep learning").decision == QualityDecision.REJECT

    def test_normal_software_accepted(self) -> None:
        assert self.filter.evaluate(description="Cloud-based CRM software").decision == QualityDecision.ACCEPT

    def test_ecommerce_platform_accepted(self) -> None:
        assert self.filter.evaluate(description="E-commerce platform").decision == QualityDecision.ACCEPT

    def test_fintech_accepted(self) -> None:
        assert self.filter.evaluate(description="Digital payments platform").decision == QualityDecision.ACCEPT

    def test_no_description_accepted(self) -> None:
        assert self.filter.evaluate().decision == QualityDecision.ACCEPT

    def test_disabled_filter_accepts_ai(self) -> None:
        f = TechnologyFilter(enabled=False)
        assert f.evaluate(description="AI model company").decision == QualityDecision.ACCEPT

    def test_tags_with_ai(self) -> None:
        assert self.filter.evaluate(tags=["ai", "startup"]).decision == QualityDecision.REJECT

    def test_industry_ai(self) -> None:
        assert self.filter.evaluate(industry="ai infrastructure").decision == QualityDecision.REJECT

    def test_company_name_ai(self) -> None:
        assert self.filter.evaluate(company_name="AI Innovations Inc").decision == QualityDecision.ACCEPT

    def test_company_name_ai_model(self) -> None:
        assert self.filter.evaluate(company_name="AI Model Labs").decision == QualityDecision.REJECT

    def test_custom_keywords(self) -> None:
        f = TechnologyFilter(ai_keywords=["quantum computing", "quantum"])
        assert f.evaluate(description="Quantum computing solutions").decision == QualityDecision.REJECT

    def test_case_insensitive_ai(self) -> None:
        assert self.filter.evaluate(description="AI MODEL company").decision == QualityDecision.REJECT


# ═══════════════════════════════════════════════════════════════════════════════
# ActivityEngine — additional tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestActivityAdditional:
    def setup_method(self) -> None:
        self.engine = ActivityEngine()

    def test_no_evidence_rejected(self) -> None:
        assert self.engine.evaluate([], now=datetime.now(UTC)).decision == QualityDecision.REJECT

    def test_none_evidence_rejected(self) -> None:
        assert self.engine.evaluate(None, now=datetime.now(UTC)).decision == QualityDecision.REJECT

    def test_1_recent_accepted(self) -> None:
        now = datetime.now(UTC)
        ev = [ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=1), source="a", title="a")]
        assert self.engine.evaluate(ev, now=now).decision == QualityDecision.ACCEPT

    def test_1_old_rejected(self) -> None:
        now = datetime.now(UTC)
        ev = [ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=100), source="a", title="a")]
        assert self.engine.evaluate(ev, now=now).decision == QualityDecision.REJECT

    def test_3_recent_accepted(self) -> None:
        now = datetime.now(UTC)
        ev = [
            ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=1), source="a", title="a"),
            ActivityEvidence(activity_type="FUNDING", timestamp=now - timedelta(days=5), source="b", title="b"),
            ActivityEvidence(activity_type="EXPANSION", timestamp=now - timedelta(days=10), source="c", title="c"),
        ]
        assert self.engine.evaluate(ev, now=now).decision == QualityDecision.ACCEPT

    def test_custom_min_3_rejected_with_2(self) -> None:
        engine = ActivityEngine(min_signals=3)
        now = datetime.now(UTC)
        ev = [
            ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=1), source="a", title="a"),
            ActivityEvidence(activity_type="FUNDING", timestamp=now - timedelta(days=5), source="b", title="b"),
        ]
        assert engine.evaluate(ev, now=now).decision == QualityDecision.REJECT

    def test_custom_min_3_accepted_with_3(self) -> None:
        engine = ActivityEngine(min_signals=3)
        now = datetime.now(UTC)
        ev = [
            ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=1), source="a", title="a"),
            ActivityEvidence(activity_type="FUNDING", timestamp=now - timedelta(days=5), source="b", title="b"),
            ActivityEvidence(activity_type="EXPANSION", timestamp=now - timedelta(days=10), source="c", title="c"),
        ]
        assert engine.evaluate(ev, now=now).decision == QualityDecision.ACCEPT

    def test_boundary_90_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ev = [ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=90), source="a", title="a")]
        assert self.engine.evaluate(ev, now=now).decision == QualityDecision.ACCEPT

    def test_over_90_days(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ev = [ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=91), source="a", title="a")]
        assert self.engine.evaluate(ev, now=now).decision == QualityDecision.REJECT

    def test_custom_max_30_days(self) -> None:
        engine = ActivityEngine(max_age_days=30)
        now = datetime.now(UTC)
        ev = [ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=25), source="a", title="a")]
        assert engine.evaluate(ev, now=now).decision == QualityDecision.ACCEPT

    def test_custom_max_30_days_rejected(self) -> None:
        engine = ActivityEngine(max_age_days=30)
        now = datetime.now(UTC)
        ev = [ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=35), source="a", title="a")]
        assert engine.evaluate(ev, now=now).decision == QualityDecision.REJECT


# ═══════════════════════════════════════════════════════════════════════════════
# QualityDashboard — additional tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestDashboardAdditional:
    def setup_method(self) -> None:
        self.dashboard = QualityDashboard()

    def _event(self, **kwargs) -> QualityEvent:
        defaults = dict(
            company_id=uuid4(),
            company_name="Corp",
            signal_type="HIRING",
            source="web",
            decision=QualityDecision.ACCEPT,
        )
        defaults.update(kwargs)
        return QualityEvent(**defaults)

    def test_100_accepted_events(self) -> None:
        for _ in range(100):
            self.dashboard.record(self._event(decision=QualityDecision.ACCEPT))
        snap = self.dashboard.snapshot()
        assert snap.signals_accepted == 100
        assert snap.signals_rejected == 0
        assert snap.acceptance_rate == 100.0

    def test_100_rejected_events(self) -> None:
        for _ in range(100):
            self.dashboard.record(self._event(decision=QualityDecision.REJECT))
        snap = self.dashboard.snapshot()
        assert snap.signals_rejected == 100
        assert snap.acceptance_rate == 0.0

    def test_50_50_split(self) -> None:
        for _ in range(50):
            self.dashboard.record(self._event(decision=QualityDecision.ACCEPT))
        for _ in range(50):
            self.dashboard.record(self._event(decision=QualityDecision.REJECT))
        snap = self.dashboard.snapshot()
        assert snap.acceptance_rate == 50.0

    def test_connector_quality_multiple(self) -> None:
        self.dashboard.record(self._event(source="linkedin", decision=QualityDecision.ACCEPT))
        self.dashboard.record(self._event(source="linkedin", decision=QualityDecision.ACCEPT))
        self.dashboard.record(self._event(source="rss", decision=QualityDecision.REJECT))
        snap = self.dashboard.snapshot()
        assert snap.connector_quality["linkedin"] == 100.0
        assert snap.connector_quality["rss"] == 0.0

    def test_top_10_rejection_reasons(self) -> None:
        for i in range(15):
            self.dashboard.record(self._event(
                decision=QualityDecision.REJECT,
                rejection_reasons=[f"REASON_{i}"],
            ))
        snap = self.dashboard.snapshot()
        assert len(snap.top_rejection_reasons) == 10

    def test_events_by_gate(self) -> None:
        self.dashboard.record(self._event(
            decision=QualityDecision.REJECT,
            gates_failed=["FRESHNESS", "WEBSITE_QUALITY"],
        ))
        assert len(self.dashboard.events_by_gate("FRESHNESS")) == 1
        assert len(self.dashboard.events_by_gate("WEBSITE_QUALITY")) == 1
        assert len(self.dashboard.events_by_gate("COMPETITOR_CHECK")) == 0

    def test_rejection_reasons_summary_counts(self) -> None:
        self.dashboard.record(self._event(
            decision=QualityDecision.REJECT,
            rejection_reasons=["A", "B"],
        ))
        self.dashboard.record(self._event(
            decision=QualityDecision.REJECT,
            rejection_reasons=["A", "C"],
        ))
        summary = self.dashboard.rejection_reasons_summary()
        assert summary["A"] == 2
        assert summary["B"] == 1
        assert summary["C"] == 1


# ═══════════════════════════════════════════════════════════════════════════════
# QualityMetricsCollector — additional tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMetricsAdditional:
    def setup_method(self) -> None:
        self.collector = QualityMetricsCollector()

    def test_1000_accepts(self) -> None:
        for _ in range(1000):
            self.collector.record_decision("ACCEPT")
        metrics = self.collector.build()
        assert metrics.total_signals == 1000
        assert metrics.acceptance_rate == 100.0

    def test_1000_rejects(self) -> None:
        for _ in range(1000):
            self.collector.record_decision("REJECT")
        metrics = self.collector.build()
        assert metrics.total_rejected == 1000
        assert metrics.acceptance_rate == 0.0

    def test_hold_count(self) -> None:
        for _ in range(10):
            self.collector.record_decision("HOLD")
        metrics = self.collector.build()
        assert metrics.total_held == 10

    def test_multiple_gate_metrics(self) -> None:
        for gate in ["FRESHNESS", "BUYING_SIGNAL", "WEBSITE_QUALITY", "COMPANY_VALIDATION", "SOURCE_TRUST", "DUPLICATE_CHECK", "COMPETITOR_CHECK", "ACTIVITY_CHECK", "INDUSTRY_RULES", "REGION_RULES", "AI_COMPANY_FILTER", "ICP_FILTER"]:
            self.collector.record_gate_evaluation(gate, passed=True)
            self.collector.record_gate_evaluation(gate, passed=False)
        metrics = self.collector.build()
        assert len(metrics.gate_metrics) == 12

    def test_multiple_connector_metrics(self) -> None:
        for conn in ["linkedin", "crunchbase", "github", "twitter", "rss", "government", "product_hunt"]:
            self.collector.record_connector_signal(conn, accepted=True)
            self.collector.record_connector_signal(conn, accepted=False)
        metrics = self.collector.build()
        assert len(metrics.connector_metrics) == 7

    def test_freshness_stats_avg(self) -> None:
        self.collector.record_decision("REJECT", freshness_age_days=30)
        self.collector.record_decision("REJECT", freshness_age_days=60)
        metrics = self.collector.build()
        assert metrics.freshness_avg_age_days == 45.0

    def test_freshness_stats_max(self) -> None:
        self.collector.record_decision("REJECT", freshness_age_days=30)
        self.collector.record_decision("REJECT", freshness_age_days=90)
        metrics = self.collector.build()
        assert metrics.freshness_max_age_days == 90

    def test_trust_stats_avg(self) -> None:
        self.collector.record_decision("ACCEPT", trust_score=98.0)
        self.collector.record_decision("ACCEPT", trust_score=88.0)
        self.collector.record_decision("ACCEPT", trust_score=78.0)
        metrics = self.collector.build()
        assert metrics.source_trust_avg == 88.0

    def test_duplicate_rate_25pct(self) -> None:
        for _ in range(3):
            self.collector.record_decision("ACCEPT")
        self.collector.record_decision("REJECT", is_duplicate=True)
        metrics = self.collector.build()
        assert metrics.duplicate_rate == 25.0

    def test_rejection_by_gate_multiple(self) -> None:
        self.collector.record_decision("REJECT", gates_failed=["A", "B"])
        self.collector.record_decision("REJECT", gates_failed=["A", "C"])
        metrics = self.collector.build()
        assert metrics.rejection_by_gate["A"] == 2
        assert metrics.rejection_by_gate["B"] == 1
        assert metrics.rejection_by_gate["C"] == 1

    def test_gate_avg_duration_3_calls(self) -> None:
        self.collector.record_gate_evaluation("G", passed=True, duration_ms=1.0)
        self.collector.record_gate_evaluation("G", passed=True, duration_ms=2.0)
        self.collector.record_gate_evaluation("G", passed=True, duration_ms=3.0)
        metrics = self.collector.build()
        assert metrics.gate_metrics["G"].avg_duration_ms == 2.0

    def test_period_timestamps_present(self) -> None:
        metrics = self.collector.build()
        assert metrics.period_start is not None
        assert metrics.period_end is not None

    def test_reset_clears_all(self) -> None:
        self.collector.record_decision("ACCEPT")
        self.collector.record_gate_evaluation("G", passed=True)
        self.collector.record_connector_signal("c", accepted=True)
        self.collector.reset()
        metrics = self.collector.build()
        assert metrics.total_signals == 0
        assert len(metrics.gate_metrics) == 0
        assert len(metrics.connector_metrics) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# QualityReportGenerator — additional tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestReportsAdditional:
    def setup_method(self) -> None:
        self.dashboard = QualityDashboard()
        self.gen = QualityReportGenerator(self.dashboard)

    def _event(self, **kwargs) -> QualityEvent:
        defaults = dict(company_id=uuid4(), company_name="Corp", signal_type="HIRING", source="web", decision=QualityDecision.ACCEPT)
        defaults.update(kwargs)
        return QualityEvent(**defaults)

    def test_daily_report_empty(self) -> None:
        report = self.gen.daily_report()
        assert report["collected"] == 0
        assert report["accepted"] == 0
        assert report["rejected"] == 0

    def test_daily_report_10_events(self) -> None:
        for _ in range(7):
            self.dashboard.record(self._event(decision=QualityDecision.ACCEPT))
        for _ in range(3):
            self.dashboard.record(self._event(decision=QualityDecision.REJECT, rejection_reasons=["X"]))
        report = self.gen.daily_report()
        assert report["collected"] == 10
        assert report["accepted"] == 7
        assert report["rejected"] == 3
        assert report["acceptance_pct"] == 70.0

    def test_weekly_report_empty(self) -> None:
        report = self.gen.weekly_report()
        assert report["total_collected"] == 0

    def test_weekly_report_20_events(self) -> None:
        for _ in range(15):
            self.dashboard.record(self._event(decision=QualityDecision.ACCEPT))
        for _ in range(5):
            self.dashboard.record(self._event(decision=QualityDecision.REJECT))
        report = self.gen.weekly_report()
        assert report["total_collected"] == 20
        assert report["total_accepted"] == 15
        assert report["total_rejected"] == 5

    def test_top_connector_is_best(self) -> None:
        for _ in range(10):
            self.dashboard.record(self._event(source="linkedin", decision=QualityDecision.ACCEPT))
        self.dashboard.record(self._event(source="rss", decision=QualityDecision.REJECT))
        report = self.gen.daily_report()
        assert report["top_connector"] == "linkedin"

    def test_worst_connector_is_worst(self) -> None:
        self.dashboard.record(self._event(source="linkedin", decision=QualityDecision.ACCEPT))
        for _ in range(5):
            self.dashboard.record(self._event(source="rss", decision=QualityDecision.REJECT))
        report = self.gen.daily_report()
        assert report["worst_connector"] == "rss"

    def test_top_rejection_reason(self) -> None:
        for _ in range(5):
            self.dashboard.record(self._event(decision=QualityDecision.REJECT, rejection_reasons=["STALE_SIGNAL"]))
        report = self.gen.daily_report()
        assert report["top_rejection_reason"] == "STALE_SIGNAL"


# ═══════════════════════════════════════════════════════════════════════════════
# QualityScheduler — additional tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSchedulerAdditional:
    def setup_method(self) -> None:
        self.dashboard = QualityDashboard()
        self.scheduler = QualityScheduler(dashboard=self.dashboard)

    def test_first_run_has_both(self) -> None:
        result = self.scheduler.check_and_run()
        assert "daily" in result
        assert "weekly" in result

    def test_daily_not_run_twice(self) -> None:
        now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
        self.scheduler.check_and_run(now=now)
        result = self.scheduler.check_and_run(now=now + timedelta(hours=1))
        assert "daily" not in result

    def test_daily_run_after_24h(self) -> None:
        now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
        self.scheduler.check_and_run(now=now)
        result = self.scheduler.check_and_run(now=now + timedelta(hours=25))
        assert "daily" in result

    def test_weekly_not_run_twice(self) -> None:
        now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
        self.scheduler.check_and_run(now=now)
        result = self.scheduler.check_and_run(now=now + timedelta(days=3))
        assert "weekly" not in result

    def test_weekly_run_after_7d(self) -> None:
        now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
        self.scheduler.check_and_run(now=now)
        result = self.scheduler.check_and_run(now=now + timedelta(days=8))
        assert "weekly" in result

    def test_force_daily(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        report = self.scheduler.force_daily(now=now)
        assert report["report_type"] == "daily"

    def test_force_weekly(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        report = self.scheduler.force_weekly(now=now)
        assert report["report_type"] == "weekly"

    def test_callback_called(self) -> None:
        calls = []
        scheduler = QualityScheduler(dashboard=self.dashboard, on_snapshot=calls.append)
        scheduler.force_daily()
        assert len(calls) == 1

    def test_multiple_callbacks(self) -> None:
        calls = []
        scheduler = QualityScheduler(dashboard=self.dashboard, on_snapshot=calls.append)
        scheduler.force_daily()
        scheduler.force_weekly()
        assert len(calls) == 2

    def test_empty_dashboard_report(self) -> None:
        report = self.scheduler.force_daily()
        assert report["collected"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# SignalFilter — additional tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSignalFilterAdditional:
    def setup_method(self) -> None:
        self.filter = SignalFilter()

    def test_valid_hiring(self) -> None:
        result = self.filter.evaluate(signal_type="HIRING", signal_source="linkedin", signal_title="Title", signal_timestamp=datetime.now(UTC))
        assert result.decision == QualityDecision.ACCEPT

    def test_valid_funding(self) -> None:
        result = self.filter.evaluate(signal_type="FUNDING", signal_source="crunchbase", signal_title="Raised $10M", signal_timestamp=datetime.now(UTC))
        assert result.decision == QualityDecision.ACCEPT

    def test_missing_type(self) -> None:
        result = self.filter.evaluate(signal_type=None, signal_source="x", signal_title="x", signal_timestamp=datetime.now(UTC))
        assert result.decision == QualityDecision.REJECT

    def test_missing_source(self) -> None:
        result = self.filter.evaluate(signal_type="HIRING", signal_source=None, signal_title="x", signal_timestamp=datetime.now(UTC))
        assert result.decision == QualityDecision.REJECT

    def test_missing_title(self) -> None:
        result = self.filter.evaluate(signal_type="HIRING", signal_source="x", signal_title=None, signal_timestamp=datetime.now(UTC))
        assert result.decision == QualityDecision.REJECT

    def test_missing_timestamp(self) -> None:
        result = self.filter.evaluate(signal_type="HIRING", signal_source="x", signal_title="x", signal_timestamp=None)
        assert result.decision == QualityDecision.REJECT

    def test_future_timestamp(self) -> None:
        result = self.filter.evaluate(signal_type="HIRING", signal_source="x", signal_title="x", signal_timestamp=datetime.now(UTC) + timedelta(days=1))
        assert result.decision == QualityDecision.REJECT

    def test_naive_timestamp(self) -> None:
        result = self.filter.evaluate(signal_type="HIRING", signal_source="x", signal_title="x", signal_timestamp=datetime(2026, 7, 29))
        assert result.decision == QualityDecision.ACCEPT

    def test_gate_name(self) -> None:
        assert self.filter.gate_name() == "SIGNAL_DATA_INTEGRITY"

    def test_all_fields_valid(self) -> None:
        result = self.filter.evaluate(signal_type="EXPANSION", signal_source="google_news", signal_title="New office", signal_timestamp=datetime.now(UTC))
        assert result.decision == QualityDecision.ACCEPT


# ═══════════════════════════════════════════════════════════════════════════════
# DQEOrchestrator — additional integration tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestDQEOrchestratorAdditional:
    def setup_method(self) -> None:
        self.orch = DQEOrchestrator()

    def test_full_acceptance_all_gates(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orch.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring SDRs",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="A legitimate company website with real content.",
            company_age_days=365,
            activity_evidence=[
                ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a"),
            ],
            description="Cloud-based CRM software",
            now=now,
        )
        assert result.decision == QualityDecision.ACCEPT
        assert len(result.gates_passed) >= 12
        assert len(result.gates_failed) == 0

    def test_reject_empty_company(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orch.evaluate(company_id=uuid4(), company_name="", now=now)
        assert result.decision == QualityDecision.REJECT
        assert "COMPANY_VALIDATION" in result.gates_failed

    def test_reject_stale_hiring(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orch.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Old",
            signal_timestamp=now - timedelta(days=45),
            has_https=True,
            content_length=500,
            page_text="Content",
            company_age_days=365,
            activity_evidence=[ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a")],
            description="Software",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT
        assert "FRESHNESS" in result.gates_failed

    def test_reject_competitor(self) -> None:
        from discovery_quality_engine.competitor_engine import CompetitorConfig, CompetitorEngine
        orch = DQEOrchestrator(
            competitor_engine=CompetitorEngine(config=CompetitorConfig(competitors=["testcorp"])),
        )
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = orch.evaluate(
            company_id=uuid4(),
            company_name="TestCorp",
            website="https://testcorp.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="Content",
            company_age_days=365,
            activity_evidence=[ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a")],
            description="Software",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT
        assert "COMPETITOR_CHECK" in result.gates_failed

    def test_reject_ai_llm(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orch.evaluate(
            company_id=uuid4(),
            company_name="LLM Corp",
            website="https://llm.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="Content",
            company_age_days=365,
            activity_evidence=[ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a")],
            description="We build LLMs",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT
        assert "AI_COMPANY_FILTER" in result.gates_failed

    def test_reject_unsupported_region_kp(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orch.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="technology",
            country="KP",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="Content",
            company_age_days=365,
            activity_evidence=[ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a")],
            description="Software",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT
        assert "REGION_RULES" in result.gates_failed

    def test_reject_no_activity(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orch.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="Content",
            company_age_days=365,
            activity_evidence=[],
            description="Software",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT
        assert "ACTIVITY_CHECK" in result.gates_failed

    def test_reject_parked_website(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orch.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="This domain is parked for sale",
            company_age_days=365,
            activity_evidence=[ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a")],
            description="Software",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT
        assert "WEBSITE_QUALITY" in result.gates_failed

    def test_reject_low_source_trust(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orch.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="unknown_blog",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="Content",
            company_age_days=365,
            activity_evidence=[ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a")],
            description="Software",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT
        assert "SOURCE_TRUST" in result.gates_failed

    def test_gates_passed_count(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orch.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="Content",
            company_age_days=365,
            activity_evidence=[ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a")],
            description="Software",
            now=now,
        )
        assert len(result.gates_passed) >= 12

    def test_dashboard_populated(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        self.orch.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            now=now,
        )
        snap = self.orch.dashboard.snapshot()
        assert snap.signals_collected >= 1

    def test_metadata_has_event_id(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orch.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            now=now,
        )
        assert "event_id" in result.metadata
