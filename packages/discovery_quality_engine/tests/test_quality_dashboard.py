"""Tests for QualityDashboard."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from discovery_quality_engine.quality_dashboard import QualityDashboard
from discovery_quality_engine.quality_engine import QualityDecision, QualityEvent


def _make_event(
    *,
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


class TestQualityDashboard:
    def setup_method(self) -> None:
        self.dashboard = QualityDashboard()

    def test_empty_dashboard(self) -> None:
        snap = self.dashboard.snapshot()
        assert snap.signals_collected == 0
        assert snap.signals_accepted == 0
        assert snap.signals_rejected == 0
        assert snap.acceptance_rate == 0.0

    def test_record_single_event(self) -> None:
        self.dashboard.record(_make_event(decision=QualityDecision.ACCEPT))
        snap = self.dashboard.snapshot()
        assert snap.signals_collected == 1
        assert snap.signals_accepted == 1

    def test_record_batch(self) -> None:
        events = [
            _make_event(decision=QualityDecision.ACCEPT),
            _make_event(decision=QualityDecision.REJECT, rejection_reasons=["STALE_SIGNAL"]),
        ]
        self.dashboard.record_batch(events)
        snap = self.dashboard.snapshot()
        assert snap.signals_collected == 2
        assert snap.signals_accepted == 1
        assert snap.signals_rejected == 1
        assert snap.acceptance_rate == 50.0

    def test_acceptance_rate_calculation(self) -> None:
        for _ in range(3):
            self.dashboard.record(_make_event(decision=QualityDecision.ACCEPT))
        for _ in range(7):
            self.dashboard.record(_make_event(decision=QualityDecision.REJECT))
        snap = self.dashboard.snapshot()
        assert snap.acceptance_rate == 30.0

    def test_freshness_failures_counted(self) -> None:
        self.dashboard.record(_make_event(
            decision=QualityDecision.REJECT,
            rejection_reasons=["STALE_SIGNAL"],
        ))
        snap = self.dashboard.snapshot()
        assert snap.freshness_failures == 1

    def test_duplicate_failures_counted(self) -> None:
        self.dashboard.record(_make_event(
            decision=QualityDecision.REJECT,
            rejection_reasons=["DUPLICATE_DOMAIN"],
        ))
        snap = self.dashboard.snapshot()
        assert snap.duplicate_failures == 1

    def test_competitor_failures_counted(self) -> None:
        self.dashboard.record(_make_event(
            decision=QualityDecision.REJECT,
            rejection_reasons=["COMPETITOR"],
        ))
        snap = self.dashboard.snapshot()
        assert snap.competitor_failures == 1

    def test_website_failures_counted(self) -> None:
        self.dashboard.record(_make_event(
            decision=QualityDecision.REJECT,
            rejection_reasons=["PARKED_DOMAIN"],
        ))
        snap = self.dashboard.snapshot()
        assert snap.website_failures == 1

    def test_buying_signal_failures_counted(self) -> None:
        self.dashboard.record(_make_event(
            decision=QualityDecision.REJECT,
            rejection_reasons=["NO_BUYING_SIGNAL"],
        ))
        snap = self.dashboard.snapshot()
        assert snap.buying_signal_failures == 1

    def test_ai_company_failures_counted(self) -> None:
        self.dashboard.record(_make_event(
            decision=QualityDecision.REJECT,
            rejection_reasons=["AI_COMPANY"],
        ))
        snap = self.dashboard.snapshot()
        assert snap.ai_company_failures == 1

    def test_icp_failures_counted(self) -> None:
        self.dashboard.record(_make_event(
            decision=QualityDecision.REJECT,
            rejection_reasons=["OUTSIDE_ICP"],
        ))
        snap = self.dashboard.snapshot()
        assert snap.icp_failures == 1

    def test_region_failures_counted(self) -> None:
        self.dashboard.record(_make_event(
            decision=QualityDecision.REJECT,
            rejection_reasons=["UNSUPPORTED_REGION"],
        ))
        snap = self.dashboard.snapshot()
        assert snap.region_failures == 1

    def test_source_trust_failures_counted(self) -> None:
        self.dashboard.record(_make_event(
            decision=QualityDecision.REJECT,
            rejection_reasons=["LOW_SOURCE_TRUST"],
        ))
        snap = self.dashboard.snapshot()
        assert snap.source_trust_failures == 1

    def test_activity_failures_counted(self) -> None:
        self.dashboard.record(_make_event(
            decision=QualityDecision.REJECT,
            rejection_reasons=["NO_RECENT_ACTIVITY"],
        ))
        snap = self.dashboard.snapshot()
        assert snap.activity_failures == 1

    def test_expired_opportunities_counted(self) -> None:
        self.dashboard.record(_make_event(
            decision=QualityDecision.REJECT,
            rejection_reasons=["EXPIRED_OPPORTUNITY"],
        ))
        snap = self.dashboard.snapshot()
        assert snap.expired_opportunities == 1

    def test_connector_quality_computed(self) -> None:
        self.dashboard.record(_make_event(source="linkedin", decision=QualityDecision.ACCEPT))
        self.dashboard.record(_make_event(source="linkedin", decision=QualityDecision.ACCEPT))
        self.dashboard.record(_make_event(source="linkedin", decision=QualityDecision.REJECT))
        snap = self.dashboard.snapshot()
        assert snap.connector_quality["linkedin"] == pytest.approx(66.67, rel=0.01)

    def test_top_rejection_reasons(self) -> None:
        for _ in range(5):
            self.dashboard.record(_make_event(
                decision=QualityDecision.REJECT,
                rejection_reasons=["STALE_SIGNAL"],
            ))
        for _ in range(3):
            self.dashboard.record(_make_event(
                decision=QualityDecision.REJECT,
                rejection_reasons=["COMPETITOR"],
            ))
        snap = self.dashboard.snapshot()
        assert len(snap.top_rejection_reasons) > 0
        assert snap.top_rejection_reasons[0]["reason"] == "STALE_SIGNAL"
        assert snap.top_rejection_reasons[0]["count"] == 5

    def test_summary(self) -> None:
        self.dashboard.record(_make_event(decision=QualityDecision.ACCEPT))
        summary = self.dashboard.summary()
        assert summary["signals_collected"] == 1
        assert summary["signals_accepted"] == 1

    def test_events_by_decision(self) -> None:
        self.dashboard.record(_make_event(decision=QualityDecision.ACCEPT))
        self.dashboard.record(_make_event(decision=QualityDecision.REJECT))
        accepted = self.dashboard.events_by_decision(QualityDecision.ACCEPT)
        assert len(accepted) == 1

    def test_events_by_gate(self) -> None:
        self.dashboard.record(_make_event(
            decision=QualityDecision.REJECT,
            gates_failed=["FRESHNESS"],
        ))
        events = self.dashboard.events_by_gate("FRESHNESS")
        assert len(events) == 1

    def test_rejection_reasons_summary(self) -> None:
        self.dashboard.record(_make_event(
            decision=QualityDecision.REJECT,
            rejection_reasons=["STALE_SIGNAL", "COMPETITOR"],
        ))
        summary = self.dashboard.rejection_reasons_summary()
        assert summary["STALE_SIGNAL"] == 1
        assert summary["COMPETITOR"] == 1

    def test_clear(self) -> None:
        self.dashboard.record(_make_event())
        self.dashboard.clear()
        snap = self.dashboard.snapshot()
        assert snap.signals_collected == 0


import pytest
