"""Comprehensive tests for connector quality engine."""

from __future__ import annotations

import pytest

from opportunity_connector_platform.connector_quality import ConnectorQuality


class TestRoiActionComprehensive:
    def test_keep_enabled(self):
        q = ConnectorQuality()
        assert q.roi_action(revenue_per_signal=5.0, failure_rate=10, acceptance_rate=50) == "keep_enabled"

    def test_keep_enabled_high_revenue(self):
        q = ConnectorQuality()
        assert q.roi_action(revenue_per_signal=100, failure_rate=0, acceptance_rate=100) == "keep_enabled"

    def test_disable_review_failure_rate_50(self):
        q = ConnectorQuality()
        assert q.roi_action(revenue_per_signal=10, failure_rate=50, acceptance_rate=80) == "disable_review"

    def test_disable_review_failure_rate_100(self):
        q = ConnectorQuality()
        assert q.roi_action(revenue_per_signal=10, failure_rate=100, acceptance_rate=80) == "disable_review"

    def test_disable_review_low_acceptance(self):
        q = ConnectorQuality()
        assert q.roi_action(revenue_per_signal=10, failure_rate=10, acceptance_rate=3) == "disable_review"

    def test_deprioritize(self):
        q = ConnectorQuality()
        assert q.roi_action(revenue_per_signal=0.5, failure_rate=10, acceptance_rate=9) == "deprioritize"

    def test_deprioritize_zero_revenue(self):
        q = ConnectorQuality()
        assert q.roi_action(revenue_per_signal=0, failure_rate=10, acceptance_rate=9) == "deprioritize"

    def test_disable_review_over_deprioritize(self):
        q = ConnectorQuality()
        assert q.roi_action(revenue_per_signal=0.5, failure_rate=50, acceptance_rate=4) == "disable_review"


class TestHealthGradeComprehensive:
    def test_grade_a_100(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=100, acceptance_rate=100, revenue_yield=100) == "A"

    def test_grade_a_90(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=90, acceptance_rate=90, revenue_yield=90) == "A"

    def test_grade_b_80(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=80, acceptance_rate=80, revenue_yield=80) == "A"

    def test_grade_b_70(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=70, acceptance_rate=70, revenue_yield=70) == "B"

    def test_grade_c_60(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=60, acceptance_rate=60, revenue_yield=60) == "B"

    def test_grade_c_50(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=50, acceptance_rate=50, revenue_yield=50) == "C"

    def test_grade_d_40(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=40, acceptance_rate=40, revenue_yield=40) == "C"

    def test_grade_d_30(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=30, acceptance_rate=30, revenue_yield=30) == "D"

    def test_grade_f_20(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=20, acceptance_rate=20, revenue_yield=20) == "D"

    def test_grade_f_0(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=0, acceptance_rate=0, revenue_yield=0) == "F"


class TestShouldDisableComprehensive:
    def test_disable_high_failure(self):
        q = ConnectorQuality()
        assert q.should_disable(failure_rate=50, acceptance_rate=80, revenue_per_signal=5) is True

    def test_disable_low_acceptance_low_revenue(self):
        q = ConnectorQuality()
        assert q.should_disable(failure_rate=10, acceptance_rate=4, revenue_per_signal=0.005) is True

    def test_not_disable_healthy(self):
        q = ConnectorQuality()
        assert q.should_disable(failure_rate=10, acceptance_rate=50, revenue_per_signal=5) is False

    def test_not_disable_high_acceptance(self):
        q = ConnectorQuality()
        assert q.should_disable(failure_rate=10, acceptance_rate=50, revenue_per_signal=0) is False

    def test_disable_boundary_failure(self):
        q = ConnectorQuality()
        assert q.should_disable(failure_rate=51, acceptance_rate=80, revenue_per_signal=10) is True


class TestPriorityScoreComprehensive:
    def test_high_yield_high_revenue(self):
        q = ConnectorQuality()
        score = q.priority_score(signal_yield=80, revenue_per_signal=10, failure_rate=5)
        assert 30 < score < 50

    def test_zero_everything(self):
        q = ConnectorQuality()
        assert q.priority_score(signal_yield=0, revenue_per_signal=0, failure_rate=0) == 0.0

    def test_max_possible(self):
        q = ConnectorQuality()
        score = q.priority_score(signal_yield=100, revenue_per_signal=100, failure_rate=0)
        assert score == 80.0

    def test_negative_result_clamped(self):
        q = ConnectorQuality()
        score = q.priority_score(signal_yield=0, revenue_per_signal=0, failure_rate=100)
        assert score == 0.0

    def test_formula(self):
        q = ConnectorQuality()
        score = q.priority_score(signal_yield=50, revenue_per_signal=20, failure_rate=10)
        expected = 50 * 0.4 + 20 * 0.4 - 10 * 0.2
        assert score == round(max(0.0, min(100.0, expected)), 2)
