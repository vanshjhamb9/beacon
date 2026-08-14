"""Edge case and integration tests for the DQE package."""

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


class TestFreshnessEngineEdgeCases:
    def test_future_timestamp(self) -> None:
        engine = FreshnessEngine()
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now + timedelta(days=5)
        result = engine.evaluate("HIRING", ts, now=now)
        assert result.age_days == 0
        assert result.decision == QualityDecision.ACCEPT

    def test_boundary_0_days(self) -> None:
        engine = FreshnessEngine()
        now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
        ts = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
        result = engine.evaluate("HIRING", ts, now=now)
        assert result.age_days == 0
        assert result.decision == QualityDecision.ACCEPT

    def test_boundary_1_day(self) -> None:
        engine = FreshnessEngine()
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=1)
        result = engine.evaluate("HIRING", ts, now=now)
        assert result.age_days == 1
        assert result.decision == QualityDecision.ACCEPT

    def test_boundary_30_days(self) -> None:
        engine = FreshnessEngine()
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=30)
        result = engine.evaluate("HIRING", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_boundary_31_days(self) -> None:
        engine = FreshnessEngine()
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=31)
        result = engine.evaluate("HIRING", ts, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_very_long_ago(self) -> None:
        engine = FreshnessEngine()
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = now - timedelta(days=3650)
        result = engine.evaluate("HIRING", ts, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_tz_naive_becomes_utc(self) -> None:
        engine = FreshnessEngine()
        now = datetime(2026, 7, 29, tzinfo=UTC)
        ts = datetime(2026, 7, 25)
        result = engine.evaluate("HIRING", ts, now=now)
        assert result.decision == QualityDecision.ACCEPT
        assert result.age_days >= 3


class TestBuyingSignalEdgeCases:
    def test_all_valid_signals(self) -> None:
        engine = BuyingSignalEngine()
        signals = [
            "HIRING", "FUNDING", "PRODUCT_LAUNCH", "TECHNOLOGY_ADOPTION",
            "PARTNERSHIP", "EXPANSION", "COMPLIANCE", "EXECUTIVE_HIRING",
            "OFFICE_EXPANSION", "ACQUISITION", "INFRASTRUCTURE_UPGRADE",
            "SECURITY_INCIDENT", "API_RELEASE", "MARKETPLACE_EXPANSION",
        ]
        result = engine.evaluate(signals)
        assert result.decision == QualityDecision.ACCEPT
        assert len(result.signals_found) == 14

    def test_empty_string_signal(self) -> None:
        engine = BuyingSignalEngine()
        result = engine.evaluate([""])
        assert result.decision == QualityDecision.REJECT

    def test_whitespace_signal(self) -> None:
        engine = BuyingSignalEngine()
        result = engine.evaluate(["  "])
        assert result.decision == QualityDecision.REJECT


class TestDuplicateEngineEdgeCases:
    def test_multiple_domains_unique(self) -> None:
        engine = DuplicateEngine()
        for i in range(10):
            result = engine.check_domain(f"example{i}.com")
            assert result.decision == QualityDecision.ACCEPT

    def test_domain_normalization_complex(self) -> None:
        engine = DuplicateEngine()
        engine.check_domain("HTTPS://WWW.Example.COM/path/page?query=1")
        result = engine.check_domain("example.com")
        assert result.decision == QualityDecision.REJECT

    def test_company_normalization_corporation(self) -> None:
        engine = DuplicateEngine()
        engine.check_company("Acme Corporation")
        result = engine.check_company("Acme corporation")
        assert result.decision == QualityDecision.REJECT

    def test_company_normalization_holdings(self) -> None:
        engine = DuplicateEngine()
        engine.check_company("Acme Holdings")
        result = engine.check_company("Acme")
        assert result.decision == QualityDecision.REJECT

    def test_company_normalization_group(self) -> None:
        engine = DuplicateEngine()
        engine.check_company("Acme Group")
        result = engine.check_company("Acme")
        assert result.decision == QualityDecision.REJECT

    def test_company_normalization_company(self) -> None:
        engine = DuplicateEngine()
        engine.check_company("Acme Company")
        result = engine.check_company("Acme")
        assert result.decision == QualityDecision.REJECT

    def test_company_normalization_case(self) -> None:
        engine = DuplicateEngine()
        engine.check_company("ACME CORP")
        result = engine.check_company("acme")
        assert result.decision == QualityDecision.REJECT

    def test_company_normalization_whitespace(self) -> None:
        engine = DuplicateEngine()
        engine.check_company("  Acme   Corp  ")
        result = engine.check_company("Acme Corp")
        assert result.decision == QualityDecision.REJECT


class TestCompetitorEngineEdgeCases:
    def test_competitor_substring_match(self) -> None:
        config = CompetitorConfig(competitors=["micro"])
        engine = CompetitorEngine(config=config)
        result = engine.evaluate("microsoft")
        assert result.decision == QualityDecision.REJECT

    def test_company_name_in_competitor(self) -> None:
        config = CompetitorConfig(competitors=["microsoft corporation"])
        engine = CompetitorEngine(config=config)
        result = engine.evaluate("microsoft")
        assert result.decision == QualityDecision.REJECT

    def test_empty_company_name(self) -> None:
        engine = CompetitorEngine()
        result = engine.evaluate("")
        assert result.decision == QualityDecision.REJECT


class TestIndustryFilterEdgeCases:
    def test_partial_match_cloud(self) -> None:
        filter = IndustryFilter()
        result = filter.evaluate("cloud technology services")
        assert result.decision == QualityDecision.ACCEPT

    def test_exact_match(self) -> None:
        filter = IndustryFilter()
        result = filter.evaluate("saas")
        assert result.decision == QualityDecision.ACCEPT

    def test_case_insensitive(self) -> None:
        filter = IndustryFilter()
        result = filter.evaluate("Technology")
        assert result.decision == QualityDecision.ACCEPT

    def test_whitespace(self) -> None:
        filter = IndustryFilter()
        result = filter.evaluate("  technology  ")
        assert result.decision == QualityDecision.ACCEPT


class TestRegionFilterEdgeCases:
    def test_lowercase_code(self) -> None:
        filter = RegionFilter()
        result = filter.evaluate("us")
        assert result.decision == QualityDecision.ACCEPT

    def test_whitespace(self) -> None:
        filter = RegionFilter()
        result = filter.evaluate("  US  ")
        assert result.decision == QualityDecision.ACCEPT

    def test_mixed_case(self) -> None:
        filter = RegionFilter()
        result = filter.evaluate("Uk")
        assert result.decision == QualityDecision.ACCEPT


class TestSourceQualityEngineEdgeCases:
    def test_all_known_sources(self) -> None:
        engine = SourceQualityEngine()
        sources = ["linkedin", "company_website", "crunchbase", "government", "github", "twitter", "rss"]
        for source in sources:
            result = engine.evaluate(source)
            assert result.decision == QualityDecision.ACCEPT

    def test_custom_high_trust_source(self) -> None:
        engine = SourceQualityEngine(source_trust={"my_source": 99.0})
        result = engine.evaluate("my_source")
        assert result.decision == QualityDecision.ACCEPT

    def test_custom_low_trust_source(self) -> None:
        engine = SourceQualityEngine(source_trust={"bad_source": 10.0})
        result = engine.evaluate("bad_source")
        assert result.decision == QualityDecision.REJECT


class TestWebsiteQualityEngineEdgeCases:
    def test_valid_https_website(self) -> None:
        engine = WebsiteQualityEngine()
        result = engine.evaluate("https://example.com", has_https=True)
        assert result.decision == QualityDecision.ACCEPT

    def test_no_page_text(self) -> None:
        engine = WebsiteQualityEngine()
        result = engine.evaluate("https://example.com")
        assert result.decision == QualityDecision.ACCEPT

    def test_content_length_boundary(self) -> None:
        engine = WebsiteQualityEngine(min_content_length=200)
        result = engine.evaluate("https://example.com", content_length=200)
        assert result.decision == QualityDecision.ACCEPT

    def test_content_length_one_below(self) -> None:
        engine = WebsiteQualityEngine(min_content_length=200)
        result = engine.evaluate("https://example.com", content_length=199)
        assert result.decision == QualityDecision.REJECT


class TestCompanyAgeFilterEdgeCases:
    def test_exactly_min_age(self) -> None:
        filter = CompanyAgeFilter(min_age_days=30)
        result = filter.evaluate(30)
        assert result.decision == QualityDecision.ACCEPT

    def test_one_below_min_age(self) -> None:
        filter = CompanyAgeFilter(min_age_days=30)
        result = filter.evaluate(29)
        assert result.decision == QualityDecision.REJECT

    def test_exactly_max_age(self) -> None:
        filter = CompanyAgeFilter(max_age_days=36500)
        result = filter.evaluate(36500)
        assert result.decision == QualityDecision.ACCEPT

    def test_one_above_max_age(self) -> None:
        filter = CompanyAgeFilter(max_age_days=36500)
        result = filter.evaluate(36501)
        assert result.decision == QualityDecision.REJECT

    def test_zero_age(self) -> None:
        filter = CompanyAgeFilter(min_age_days=0)
        result = filter.evaluate(0)
        assert result.decision == QualityDecision.ACCEPT


class TestActivityEngineEdgeCases:
    def test_exact_boundary_90_days(self) -> None:
        engine = ActivityEngine(max_age_days=90)
        now = datetime(2026, 7, 29, tzinfo=UTC)
        evidence = [
            ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=90), source="a", title="a"),
        ]
        result = engine.evaluate(evidence, now=now)
        assert result.decision == QualityDecision.ACCEPT

    def test_one_day_over_90_days(self) -> None:
        engine = ActivityEngine(max_age_days=90)
        now = datetime(2026, 7, 29, tzinfo=UTC)
        evidence = [
            ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=91), source="a", title="a"),
        ]
        result = engine.evaluate(evidence, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_min_signals_3_with_2(self) -> None:
        engine = ActivityEngine(min_signals=3)
        now = datetime.now(UTC)
        evidence = [
            ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a"),
            ActivityEvidence(activity_type="FUNDING", timestamp=now - timedelta(days=7), source="b", title="b"),
        ]
        result = engine.evaluate(evidence, now=now)
        assert result.decision == QualityDecision.REJECT

    def test_min_signals_3_with_3(self) -> None:
        engine = ActivityEngine(min_signals=3)
        now = datetime.now(UTC)
        evidence = [
            ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a"),
            ActivityEvidence(activity_type="FUNDING", timestamp=now - timedelta(days=7), source="b", title="b"),
            ActivityEvidence(activity_type="EXPANSION", timestamp=now - timedelta(days=14), source="c", title="c"),
        ]
        result = engine.evaluate(evidence, now=now)
        assert result.decision == QualityDecision.ACCEPT


class TestQualityDashboardEdgeCases:
    def test_all_rejection_reasons(self) -> None:
        dashboard = QualityDashboard()
        for reason in RejectionReason:
            event = QualityEvent(
                company_id=uuid4(),
                company_name="Corp",
                signal_type="HIRING",
                source="web",
                decision=QualityDecision.REJECT,
                rejection_reasons=[reason.value],
            )
            dashboard.record(event)
        summary = dashboard.rejection_reasons_summary()
        assert len(summary) == len(RejectionReason)

    def test_multiple_sources(self) -> None:
        dashboard = QualityDashboard()
        for source in ["linkedin", "crunchbase", "github", "twitter", "rss"]:
            event = QualityEvent(
                company_id=uuid4(),
                company_name="Corp",
                signal_type="HIRING",
                source=source,
                decision=QualityDecision.ACCEPT,
            )
            dashboard.record(event)
        snap = dashboard.snapshot()
        assert len(snap.connector_quality) == 5


class TestQualityMetricsEdgeCases:
    def test_many_decisions(self) -> None:
        collector = QualityMetricsCollector()
        for _ in range(1000):
            collector.record_decision("ACCEPT")
        for _ in range(500):
            collector.record_decision("REJECT")
        metrics = collector.build()
        assert metrics.total_signals == 1500
        assert metrics.acceptance_rate == pytest.approx(66.67, rel=0.01)

    def test_gate_metrics_multiple_gates(self) -> None:
        collector = QualityMetricsCollector()
        for gate in ["FRESHNESS", "BUYING_SIGNAL", "WEBSITE_QUALITY"]:
            collector.record_gate_evaluation(gate, passed=True)
            collector.record_gate_evaluation(gate, passed=False)
        metrics = collector.build()
        assert len(metrics.gate_metrics) == 3
        for gm in metrics.gate_metrics.values():
            assert gm.total_evaluated == 2
            assert gm.total_passed == 1
            assert gm.total_failed == 1


class TestQualitySchedulerEdgeCases:
    def test_multiple_daily_checks_within_24h(self) -> None:
        dashboard = QualityDashboard()
        scheduler = QualityScheduler(dashboard=dashboard)
        now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
        results = []
        for i in range(24):
            result = scheduler.check_and_run(now=now + timedelta(hours=i))
            results.append(result)
        daily_runs = sum(1 for r in results if "daily" in r)
        assert daily_runs == 1

    def test_multiple_weekly_checks_within_7d(self) -> None:
        dashboard = QualityDashboard()
        scheduler = QualityScheduler(dashboard=dashboard)
        now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
        results = []
        for i in range(7):
            result = scheduler.check_and_run(now=now + timedelta(days=i))
            results.append(result)
        weekly_runs = sum(1 for r in results if "weekly" in r)
        assert weekly_runs == 1


class TestQualityReportGeneratorEdgeCases:
    def test_daily_report_connector_ranking(self) -> None:
        dashboard = QualityDashboard()
        for _ in range(10):
            event = QualityEvent(
                company_id=uuid4(),
                company_name="Corp",
                signal_type="HIRING",
                source="linkedin",
                decision=QualityDecision.ACCEPT,
            )
            dashboard.record(event)
        for _ in range(5):
            event = QualityEvent(
                company_id=uuid4(),
                company_name="Corp",
                signal_type="HIRING",
                source="rss",
                decision=QualityDecision.REJECT,
                rejection_reasons=["LOW_SOURCE_TRUST"],
            )
            dashboard.record(event)
        gen = QualityReportGenerator(dashboard)
        report = gen.daily_report()
        assert report["top_connector"] == "linkedin"
        assert report["worst_connector"] == "rss"
