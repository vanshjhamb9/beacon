"""Tests for connector quality engine."""

from __future__ import annotations

import pytest

from opportunity_connector_platform.connector_quality import ConnectorQuality


class TestConnectorQuality:
    def test_roi_action_keep_enabled(self):
        q = ConnectorQuality()
        assert q.roi_action(revenue_per_signal=5.0, failure_rate=10.0, acceptance_rate=50.0) == "keep_enabled"

    def test_roi_action_disable_review_high_failure(self):
        q = ConnectorQuality()
        assert q.roi_action(revenue_per_signal=5.0, failure_rate=50.0, acceptance_rate=50.0) == "disable_review"

    def test_roi_action_disable_review_low_acceptance(self):
        q = ConnectorQuality()
        assert q.roi_action(revenue_per_signal=5.0, failure_rate=10.0, acceptance_rate=4.0) == "disable_review"

    def test_roi_action_deprioritize(self):
        q = ConnectorQuality()
        assert q.roi_action(revenue_per_signal=0.5, failure_rate=10.0, acceptance_rate=9.0) == "deprioritize"

    def test_health_grade_a(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=90, acceptance_rate=90, revenue_yield=90) == "A"

    def test_health_grade_b(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=70, acceptance_rate=70, revenue_yield=70) == "B"

    def test_health_grade_c(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=50, acceptance_rate=50, revenue_yield=50) == "C"

    def test_health_grade_d(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=30, acceptance_rate=30, revenue_yield=30) == "D"

    def test_health_grade_f(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=10, acceptance_rate=10, revenue_yield=10) == "F"

    def test_should_disable_high_failure(self):
        q = ConnectorQuality()
        assert q.should_disable(failure_rate=50, acceptance_rate=50, revenue_per_signal=5.0) is True

    def test_should_disable_low_acceptance_low_revenue(self):
        q = ConnectorQuality()
        assert q.should_disable(failure_rate=10, acceptance_rate=4, revenue_per_signal=0.005) is True

    def test_should_not_disable(self):
        q = ConnectorQuality()
        assert q.should_disable(failure_rate=10, acceptance_rate=50, revenue_per_signal=5.0) is False

    def test_priority_score_high(self):
        q = ConnectorQuality()
        score = q.priority_score(signal_yield=80, revenue_per_signal=10, failure_rate=5)
        assert score > 0

    def test_priority_score_zero(self):
        q = ConnectorQuality()
        score = q.priority_score(signal_yield=0, revenue_per_signal=0, failure_rate=100)
        assert score == 0.0

    def test_priority_score_formula(self):
        q = ConnectorQuality()
        score = q.priority_score(signal_yield=100, revenue_per_signal=100, failure_rate=0)
        assert score == 80.0

    def test_health_grade_boundary_80(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=100, acceptance_rate=100, revenue_yield=100) == "A"

    def test_health_grade_boundary_60(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=66.67, acceptance_rate=66.67, revenue_yield=66.67) == "B"

    def test_health_grade_boundary_40(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=50, acceptance_rate=50, revenue_yield=25) == "C"

    def test_health_grade_boundary_20(self):
        q = ConnectorQuality()
        assert q.health_grade(success_rate=25, acceptance_rate=25, revenue_yield=10) == "F"

    def test_disable_review_priority(self):
        q = ConnectorQuality()
        score = q.priority_score(signal_yield=0, revenue_per_signal=0, failure_rate=100)
        assert score <= 0.0
