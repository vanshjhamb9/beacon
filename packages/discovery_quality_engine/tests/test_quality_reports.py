"""Tests for QualityReportGenerator."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from discovery_quality_engine.quality_dashboard import QualityDashboard
from discovery_quality_engine.quality_engine import QualityDecision, QualityEvent
from discovery_quality_engine.quality_reports import QualityReportGenerator


def _make_event(
    decision: QualityDecision = QualityDecision.ACCEPT,
    company_name: str = "Test Corp",
    signal_type: str = "HIRING",
    source: str = "linkedin",
    rejection_reasons: list[str] | None = None,
    gates_failed: list[str] | None = None,
) -> QualityEvent:
    return QualityEvent(
        company_id=uuid4(),
        company_name=company_name,
        signal_type=signal_type,
        source=source,
        decision=decision,
        rejection_reasons=rejection_reasons or [],
        gates_failed=gates_failed or [],
    )


class TestQualityReportGenerator:
    def setup_method(self) -> None:
        self.dashboard = QualityDashboard()
        self.generator = QualityReportGenerator(self.dashboard)

    def test_daily_report_empty(self) -> None:
        report = self.generator.daily_report()
        assert report["report_type"] == "daily"
        assert report["collected"] == 0
        assert report["accepted"] == 0
        assert report["rejected"] == 0
        assert report["acceptance_pct"] == 0.0

    def test_daily_report_with_data(self) -> None:
        self.dashboard.record(_make_event(decision=QualityDecision.ACCEPT))
        self.dashboard.record(_make_event(
            decision=QualityDecision.REJECT,
            rejection_reasons=["STALE_SIGNAL"],
        ))
        report = self.generator.daily_report()
        assert report["collected"] == 2
        assert report["accepted"] == 1
        assert report["rejected"] == 1
        assert report["acceptance_pct"] == 50.0

    def test_weekly_report_empty(self) -> None:
        report = self.generator.weekly_report()
        assert report["report_type"] == "weekly"
        assert report["total_collected"] == 0

    def test_weekly_report_with_data(self) -> None:
        for _ in range(5):
            self.dashboard.record(_make_event(decision=QualityDecision.ACCEPT))
        report = self.generator.weekly_report()
        assert report["total_collected"] == 5
        assert report["total_accepted"] == 5

    def test_top_connector(self) -> None:
        for _ in range(3):
            self.dashboard.record(_make_event(source="linkedin", decision=QualityDecision.ACCEPT))
        self.dashboard.record(_make_event(source="rss", decision=QualityDecision.ACCEPT))
        report = self.generator.daily_report()
        assert report["top_connector"] == "linkedin"

    def test_worst_connector(self) -> None:
        self.dashboard.record(_make_event(source="linkedin", decision=QualityDecision.ACCEPT))
        for _ in range(3):
            self.dashboard.record(_make_event(source="rss", decision=QualityDecision.REJECT))
        report = self.generator.daily_report()
        assert report["worst_connector"] == "rss"

    def test_top_rejection_reason(self) -> None:
        for _ in range(5):
            self.dashboard.record(_make_event(
                decision=QualityDecision.REJECT,
                rejection_reasons=["STALE_SIGNAL"],
            ))
        report = self.generator.daily_report()
        assert report["top_rejection_reason"] == "STALE_SIGNAL"

    def test_freshest_opportunities(self) -> None:
        self.dashboard.record(_make_event(
            decision=QualityDecision.ACCEPT,
            company_name="Fresh Corp",
            signal_type="HIRING",
        ))
        report = self.generator.daily_report()
        assert len(report["freshest_opportunities"]) == 1
        assert report["freshest_opportunities"][0]["company"] == "Fresh Corp"

    def test_daily_report_keys(self) -> None:
        report = self.generator.daily_report()
        expected_keys = {
            "report_type", "date", "collected", "accepted", "rejected",
            "acceptance_pct", "top_connector", "worst_connector",
            "top_rejection_reason", "freshest_opportunities", "oldest_rejected",
            "freshness_failures", "duplicate_failures", "competitor_failures",
            "website_failures", "buying_signal_failures", "ai_company_failures",
            "icp_failures", "region_failures", "source_trust_failures",
            "activity_failures", "expired_opportunities", "connector_quality",
            "top_rejection_reasons",
        }
        assert expected_keys.issubset(set(report.keys()))

    def test_weekly_report_keys(self) -> None:
        report = self.generator.weekly_report()
        expected_keys = {
            "report_type", "week_ending", "total_collected", "total_accepted",
            "total_rejected", "acceptance_pct", "freshness_failures",
            "duplicate_failures", "competitor_failures", "website_failures",
            "buying_signal_failures", "ai_company_failures", "icp_failures",
            "region_failures", "source_trust_failures", "activity_failures",
            "expired_opportunities", "connector_quality", "top_rejection_reasons",
        }
        assert expected_keys.issubset(set(report.keys()))
