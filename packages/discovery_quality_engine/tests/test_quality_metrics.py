"""Tests for QualityMetricsCollector."""

from __future__ import annotations

from discovery_quality_engine.quality_metrics import QualityMetricsCollector, QualityMetrics


class TestQualityMetricsCollector:
    def setup_method(self) -> None:
        self.collector = QualityMetricsCollector()

    def test_initial_state(self) -> None:
        metrics = self.collector.build()
        assert metrics.total_signals == 0
        assert metrics.total_accepted == 0
        assert metrics.total_rejected == 0

    def test_record_accept(self) -> None:
        self.collector.record_decision("ACCEPT")
        metrics = self.collector.build()
        assert metrics.total_signals == 1
        assert metrics.total_accepted == 1

    def test_record_reject(self) -> None:
        self.collector.record_decision("REJECT", rejection_reasons=["STALE_SIGNAL"])
        metrics = self.collector.build()
        assert metrics.total_signals == 1
        assert metrics.total_rejected == 1
        assert metrics.rejection_by_reason["STALE_SIGNAL"] == 1

    def test_record_hold(self) -> None:
        self.collector.record_decision("HOLD")
        metrics = self.collector.build()
        assert metrics.total_held == 1

    def test_acceptance_rate(self) -> None:
        for _ in range(3):
            self.collector.record_decision("ACCEPT")
        for _ in range(7):
            self.collector.record_decision("REJECT")
        metrics = self.collector.build()
        assert metrics.acceptance_rate == 30.0

    def test_gate_evaluation(self) -> None:
        self.collector.record_gate_evaluation("FRESHNESS", passed=True, duration_ms=1.5)
        self.collector.record_gate_evaluation("FRESHNESS", passed=False, duration_ms=2.0)
        metrics = self.collector.build()
        gm = metrics.gate_metrics["FRESHNESS"]
        assert gm.total_evaluated == 2
        assert gm.total_passed == 1
        assert gm.total_failed == 1

    def test_connector_metric(self) -> None:
        self.collector.record_connector_signal("linkedin", accepted=True, trust_score=98.0)
        self.collector.record_connector_signal("linkedin", accepted=False, trust_score=98.0)
        metrics = self.collector.build()
        cm = metrics.connector_metrics["linkedin"]
        assert cm.total_signals == 2
        assert cm.accepted == 1
        assert cm.rejected == 1
        assert cm.acceptance_rate == 50.0

    def test_rejection_by_gate(self) -> None:
        self.collector.record_decision("REJECT", gates_failed=["FRESHNESS", "WEBSITE_QUALITY"])
        metrics = self.collector.build()
        assert metrics.rejection_by_gate["FRESHNESS"] == 1
        assert metrics.rejection_by_gate["WEBSITE_QUALITY"] == 1

    def test_freshness_stats(self) -> None:
        self.collector.record_decision("REJECT", freshness_age_days=45)
        self.collector.record_decision("REJECT", freshness_age_days=90)
        metrics = self.collector.build()
        assert metrics.freshness_avg_age_days == 67.5
        assert metrics.freshness_max_age_days == 90

    def test_trust_stats(self) -> None:
        self.collector.record_decision("ACCEPT", trust_score=98.0)
        self.collector.record_decision("ACCEPT", trust_score=88.0)
        metrics = self.collector.build()
        assert metrics.source_trust_avg == 93.0

    def test_duplicate_rate(self) -> None:
        self.collector.record_decision("REJECT", is_duplicate=True)
        self.collector.record_decision("ACCEPT")
        metrics = self.collector.build()
        assert metrics.duplicate_rate == 50.0

    def test_reset(self) -> None:
        self.collector.record_decision("ACCEPT")
        self.collector.reset()
        metrics = self.collector.build()
        assert metrics.total_signals == 0

    def test_gate_avg_duration(self) -> None:
        self.collector.record_gate_evaluation("FRESHNESS", passed=True, duration_ms=1.0)
        self.collector.record_gate_evaluation("FRESHNESS", passed=True, duration_ms=3.0)
        metrics = self.collector.build()
        assert metrics.gate_metrics["FRESHNESS"].avg_duration_ms == 2.0

    def test_period_timestamps(self) -> None:
        metrics = self.collector.build()
        assert metrics.period_start is not None
        assert metrics.period_end is not None
