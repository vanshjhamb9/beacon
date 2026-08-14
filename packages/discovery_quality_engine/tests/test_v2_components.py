"""Tests for DQE v2 components — score, grade, freshness v2, buying signal v2."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from discovery_quality_engine.buying_signal_engine_v2 import (
    NOT_BUYING_SIGNALS,
    VALID_BUYING_SIGNALS,
    BuyingSignalEngineV2,
)
from discovery_quality_engine.freshness_engine_v2 import FreshnessEngineV2, FreshnessStatus
from discovery_quality_engine.quality_grade_engine import QualityGradeEngine
from discovery_quality_engine.quality_report_engine import QualityReportEngine
from discovery_quality_engine.quality_score_engine import QualityScoreEngine
from discovery_quality_engine.v2_schemas import (
    BuyingSignalVerdict,
    QualityEvidence,
    QualityGrade,
    QualityReport,
    QualityScore,
    ScoreWeight,
    grade_from_score,
)


class TestGradeFromScore:
    def test_grade_a_plus(self):
        assert grade_from_score(95) == QualityGrade.A_PLUS
        assert grade_from_score(100) == QualityGrade.A_PLUS
        assert grade_from_score(98) == QualityGrade.A_PLUS

    def test_grade_a(self):
        assert grade_from_score(90) == QualityGrade.A
        assert grade_from_score(94) == QualityGrade.A

    def test_grade_b(self):
        assert grade_from_score(85) == QualityGrade.B
        assert grade_from_score(89) == QualityGrade.B

    def test_grade_c(self):
        assert grade_from_score(75) == QualityGrade.C
        assert grade_from_score(84) == QualityGrade.C

    def test_grade_reject(self):
        assert grade_from_score(74) == QualityGrade.REJECT
        assert grade_from_score(0) == QualityGrade.REJECT

    def test_boundary_95(self):
        assert grade_from_score(95) == QualityGrade.A_PLUS

    def test_boundary_94(self):
        assert grade_from_score(94) == QualityGrade.A

    def test_boundary_90(self):
        assert grade_from_score(90) == QualityGrade.A

    def test_boundary_89(self):
        assert grade_from_score(89) == QualityGrade.B

    def test_boundary_85(self):
        assert grade_from_score(85) == QualityGrade.B

    def test_boundary_84(self):
        assert grade_from_score(84) == QualityGrade.C

    def test_boundary_75(self):
        assert grade_from_score(75) == QualityGrade.C

    def test_boundary_74(self):
        assert grade_from_score(74) == QualityGrade.REJECT


class TestQualityScoreEngine:
    def test_weights_sum_to_100(self):
        engine = QualityScoreEngine()
        total = sum(w.weight for w in engine.weights)
        assert total == 100

    def test_weights_unique_names(self):
        engine = QualityScoreEngine()
        names = [w.name for w in engine.weights]
        assert len(names) == len(set(names))

    def test_custom_weights(self):
        weights = [
            ScoreWeight(name="test", weight=100),
        ]
        engine = QualityScoreEngine(weights=weights)
        assert len(engine.weights) == 1

    def test_invalid_weights_sum(self):
        weights = [
            ScoreWeight(name="test", weight=50),
        ]
        with pytest.raises(ValueError):
            QualityScoreEngine(weights=weights)

    def test_calculate_perfect_score(self):
        engine = QualityScoreEngine()
        evidence = QualityEvidence()
        score = engine.calculate(
            evidence=evidence,
            freshness_raw_score=100.0,
            buying_signal_raw_score=100.0,
            source_trust_raw_score=100.0,
            website_quality_raw_score=100.0,
            company_validation_raw_score=100.0,
            icp_match_raw_score=100.0,
            region_raw_score=100.0,
            industry_raw_score=100.0,
        )
        assert score.total_score == 100
        assert len(score.components) == 8

    def test_calculate_zero_score(self):
        engine = QualityScoreEngine()
        evidence = QualityEvidence()
        score = engine.calculate(
            evidence=evidence,
            freshness_raw_score=0.0,
            buying_signal_raw_score=0.0,
            source_trust_raw_score=0.0,
            website_quality_raw_score=0.0,
            company_validation_raw_score=0.0,
            icp_match_raw_score=0.0,
            region_raw_score=0.0,
            industry_raw_score=0.0,
        )
        assert score.total_score == 0

    def test_calculate_mixed_score(self):
        engine = QualityScoreEngine()
        evidence = QualityEvidence()
        score = engine.calculate(
            evidence=evidence,
            freshness_raw_score=100.0,
            buying_signal_raw_score=100.0,
            source_trust_raw_score=0.0,
            website_quality_raw_score=0.0,
            company_validation_raw_score=0.0,
            icp_match_raw_score=0.0,
            region_raw_score=0.0,
            industry_raw_score=0.0,
        )
        assert 0 < score.total_score < 100

    def test_score_clamped_to_100(self):
        engine = QualityScoreEngine()
        evidence = QualityEvidence()
        score = engine.calculate(
            evidence=evidence,
            freshness_raw_score=150.0,
            buying_signal_raw_score=150.0,
            source_trust_raw_score=150.0,
            website_quality_raw_score=150.0,
            company_validation_raw_score=150.0,
            icp_match_raw_score=150.0,
            region_raw_score=150.0,
            industry_raw_score=150.0,
        )
        assert score.total_score == 100

    def test_score_clamped_to_0(self):
        engine = QualityScoreEngine()
        evidence = QualityEvidence()
        score = engine.calculate(
            evidence=evidence,
            freshness_raw_score=-50.0,
            buying_signal_raw_score=-50.0,
            source_trust_raw_score=-50.0,
            website_quality_raw_score=-50.0,
            company_validation_raw_score=-50.0,
            icp_match_raw_score=-50.0,
            region_raw_score=-50.0,
            industry_raw_score=-50.0,
        )
        assert score.total_score == 0

    def test_freshness_score_accepted_recent(self):
        engine = QualityScoreEngine()
        score = engine.calculate_freshness_score(
            status=FreshnessStatus.ACCEPTED,
            signal_age_days=10,
        )
        assert score == 100.0

    def test_freshness_score_accepted_old(self):
        engine = QualityScoreEngine()
        score = engine.calculate_freshness_score(
            status=FreshnessStatus.ACCEPTED,
            signal_age_days=80,
        )
        assert 50.0 <= score <= 100.0

    def test_freshness_score_borderline(self):
        engine = QualityScoreEngine()
        score = engine.calculate_freshness_score(
            status=FreshnessStatus.BORDERLINE,
            signal_age_days=120,
        )
        assert 25.0 <= score <= 50.0

    def test_freshness_score_expired(self):
        engine = QualityScoreEngine()
        score = engine.calculate_freshness_score(
            status=FreshnessStatus.EXPIRED,
            signal_age_days=200,
        )
        assert score == 0.0

    def test_buying_signal_score_all_valid(self):
        engine = QualityScoreEngine()
        score = engine.calculate_buying_signal_score(
            valid_count=3,
            not_valid_count=0,
            borderline_count=0,
        )
        assert score == 100.0

    def test_buying_signal_score_all_not_valid(self):
        engine = QualityScoreEngine()
        score = engine.calculate_buying_signal_score(
            valid_count=0,
            not_valid_count=3,
            borderline_count=0,
        )
        assert score == 0.0

    def test_buying_signal_score_mixed(self):
        engine = QualityScoreEngine()
        score = engine.calculate_buying_signal_score(
            valid_count=1,
            not_valid_count=1,
            borderline_count=1,
        )
        assert 0.0 < score < 100.0


class TestQualityGradeEngine:
    def test_grade_a_plus(self):
        engine = QualityGradeEngine()
        score = QualityScore(
            total_score=98,
            components=[],
            calculated_at=datetime.now(UTC),
        )
        assert engine.evaluate(score) == QualityGrade.A_PLUS

    def test_grade_a(self):
        engine = QualityGradeEngine()
        score = QualityScore(
            total_score=92,
            components=[],
            calculated_at=datetime.now(UTC),
        )
        assert engine.evaluate(score) == QualityGrade.A

    def test_grade_b(self):
        engine = QualityGradeEngine()
        score = QualityScore(
            total_score=87,
            components=[],
            calculated_at=datetime.now(UTC),
        )
        assert engine.evaluate(score) == QualityGrade.B

    def test_grade_c(self):
        engine = QualityGradeEngine()
        score = QualityScore(
            total_score=80,
            components=[],
            calculated_at=datetime.now(UTC),
        )
        assert engine.evaluate(score) == QualityGrade.C

    def test_grade_reject(self):
        engine = QualityGradeEngine()
        score = QualityScore(
            total_score=70,
            components=[],
            calculated_at=datetime.now(UTC),
        )
        assert engine.evaluate(score) == QualityGrade.REJECT

    def test_grade_to_decision_accept(self):
        engine = QualityGradeEngine()
        assert engine.grade_to_decision(QualityGrade.A_PLUS) == "ACCEPT"
        assert engine.grade_to_decision(QualityGrade.A) == "ACCEPT"
        assert engine.grade_to_decision(QualityGrade.B) == "ACCEPT"

    def test_grade_to_decision_hold(self):
        engine = QualityGradeEngine()
        assert engine.grade_to_decision(QualityGrade.C) == "HOLD"

    def test_grade_to_decision_reject(self):
        engine = QualityGradeEngine()
        assert engine.grade_to_decision(QualityGrade.REJECT) == "REJECT"

    def test_get_decision(self):
        engine = QualityGradeEngine()
        score = QualityScore(
            total_score=95,
            components=[],
            calculated_at=datetime.now(UTC),
        )
        grade, decision = engine.get_decision(score)
        assert grade == QualityGrade.A_PLUS
        assert decision == "ACCEPT"

    def test_is_acceptable(self):
        engine = QualityGradeEngine()
        assert engine.is_acceptable(QualityGrade.A_PLUS) is True
        assert engine.is_acceptable(QualityGrade.A) is True
        assert engine.is_acceptable(QualityGrade.B) is True
        assert engine.is_acceptable(QualityGrade.C) is False
        assert engine.is_acceptable(QualityGrade.REJECT) is False

    def test_is_hold(self):
        engine = QualityGradeEngine()
        assert engine.is_hold(QualityGrade.C) is True
        assert engine.is_hold(QualityGrade.A) is False

    def test_is_reject(self):
        engine = QualityGradeEngine()
        assert engine.is_reject(QualityGrade.REJECT) is True
        assert engine.is_reject(QualityGrade.A) is False


class TestFreshnessEngineV2:
    def test_accepted_recent(self):
        engine = FreshnessEngineV2()
        now = datetime.now(UTC)
        signal_time = now - timedelta(days=30)
        result = engine.evaluate(signal_timestamp=signal_time, now=now)
        assert result.status == FreshnessStatus.ACCEPTED
        assert result.signal_age_days == 30

    def test_accepted_boundary(self):
        engine = FreshnessEngineV2()
        now = datetime.now(UTC)
        signal_time = now - timedelta(days=90)
        result = engine.evaluate(signal_timestamp=signal_time, now=now)
        assert result.status == FreshnessStatus.ACCEPTED

    def test_borderline(self):
        engine = FreshnessEngineV2()
        now = datetime.now(UTC)
        signal_time = now - timedelta(days=120)
        result = engine.evaluate(signal_timestamp=signal_time, now=now)
        assert result.status == FreshnessStatus.BORDERLINE

    def test_borderline_boundary(self):
        engine = FreshnessEngineV2()
        now = datetime.now(UTC)
        signal_time = now - timedelta(days=180)
        result = engine.evaluate(signal_timestamp=signal_time, now=now)
        assert result.status == FreshnessStatus.BORDERLINE

    def test_expired(self):
        engine = FreshnessEngineV2()
        now = datetime.now(UTC)
        signal_time = now - timedelta(days=200)
        result = engine.evaluate(signal_timestamp=signal_time, now=now)
        assert result.status == FreshnessStatus.EXPIRED

    def test_naive_timestamp(self):
        engine = FreshnessEngineV2()
        now = datetime.now(UTC)
        signal_time = datetime(2026, 6, 1, 12, 0, 0)
        result = engine.evaluate(signal_timestamp=signal_time, now=now)
        assert result.status in (FreshnessStatus.ACCEPTED, FreshnessStatus.BORDERLINE, FreshnessStatus.EXPIRED)

    def test_get_score_multiplier(self):
        engine = FreshnessEngineV2()
        assert engine.get_score_multiplier(FreshnessStatus.ACCEPTED) == 1.0
        assert engine.get_score_multiplier(FreshnessStatus.BORDERLINE) == 0.5
        assert engine.get_score_multiplier(FreshnessStatus.EXPIRED) == 0.0

    def test_should_reject(self):
        engine = FreshnessEngineV2()
        assert engine.should_reject(FreshnessStatus.EXPIRED) is True
        assert engine.should_reject(FreshnessStatus.ACCEPTED) is False
        assert engine.should_reject(FreshnessStatus.BORDERLINE) is False

    def test_should_hold(self):
        engine = FreshnessEngineV2()
        assert engine.should_hold(FreshnessStatus.BORDERLINE) is True
        assert engine.should_hold(FreshnessStatus.ACCEPTED) is False
        assert engine.should_hold(FreshnessStatus.EXPIRED) is False

    def test_custom_thresholds(self):
        engine = FreshnessEngineV2(
            accepted_threshold_days=30,
            borderline_threshold_days=60,
        )
        now = datetime.now(UTC)
        signal_time = now - timedelta(days=45)
        result = engine.evaluate(signal_timestamp=signal_time, now=now)
        assert result.status == FreshnessStatus.BORDERLINE


class TestBuyingSignalEngineV2:
    def test_valid_signals_list(self):
        assert "Hiring" in VALID_BUYING_SIGNALS
        assert "Funding" in VALID_BUYING_SIGNALS
        assert "Expansion" in VALID_BUYING_SIGNALS
        assert len(VALID_BUYING_SIGNALS) == 17

    def test_not_valid_signals_list(self):
        assert "Blog posts" in NOT_BUYING_SIGNALS
        assert "Random tweets" in NOT_BUYING_SIGNALS
        assert len(NOT_BUYING_SIGNALS) == 5

    def test_evaluate_valid(self):
        engine = BuyingSignalEngineV2()
        result = engine.evaluate(signal_types=["Hiring", "Funding"])
        assert result.verdict.value == "valid"
        assert len(result.valid_signals) == 2
        assert len(result.not_valid_signals) == 0

    def test_evaluate_not_valid(self):
        engine = BuyingSignalEngineV2()
        result = engine.evaluate(signal_types=["Blog posts", "Random tweets"])
        assert result.verdict.value == "not_valid"
        assert len(result.valid_signals) == 0
        assert len(result.not_valid_signals) == 2

    def test_evaluate_mixed(self):
        engine = BuyingSignalEngineV2()
        result = engine.evaluate(signal_types=["Hiring", "Blog posts"])
        assert result.verdict.value == "borderline"
        assert len(result.valid_signals) == 1
        assert len(result.not_valid_signals) == 1

    def test_evaluate_borderline(self):
        engine = BuyingSignalEngineV2()
        result = engine.evaluate(signal_types=["Unknown Signal"])
        assert result.verdict.value == "borderline"
        assert len(result.borderline_signals) == 1

    def test_evaluate_empty(self):
        engine = BuyingSignalEngineV2()
        result = engine.evaluate(signal_types=[])
        assert result.verdict.value == "not_valid"

    def test_is_valid_signal(self):
        engine = BuyingSignalEngineV2()
        assert engine.is_valid_signal("Hiring") is True
        assert engine.is_valid_signal("hiring") is True
        assert engine.is_valid_signal("Blog posts") is False

    def test_is_not_valid_signal(self):
        engine = BuyingSignalEngineV2()
        assert engine.is_not_valid_signal("Blog posts") is True
        assert engine.is_not_valid_signal("blog posts") is True
        assert engine.is_not_valid_signal("Hiring") is False

    def test_should_reject(self):
        engine = BuyingSignalEngineV2()
        from discovery_quality_engine.v2_schemas import BuyingSignalVerdict
        assert engine.should_reject(BuyingSignalVerdict.NOT_VALID) is True
        assert engine.should_reject(BuyingSignalVerdict.VALID) is False

    def test_should_hold(self):
        engine = BuyingSignalEngineV2()
        from discovery_quality_engine.v2_schemas import BuyingSignalVerdict
        assert engine.should_hold(BuyingSignalVerdict.BORDERLINE) is True
        assert engine.should_hold(BuyingSignalVerdict.VALID) is False


class TestQualityReportEngine:
    def test_generate_report(self):
        from uuid import uuid4
        engine = QualityReportEngine()
        evidence = QualityEvidence(
            signal_freshness_days=30,
            signal_freshness_status=FreshnessStatus.ACCEPTED,
            buying_signals_detected=["Hiring"],
            buying_signal_verdict=BuyingSignalVerdict.VALID,
        )
        report = engine.generate(
            company_id=uuid4(),
            company_name="Test Corp",
            evidence=evidence,
            gates_passed=["company", "signal", "freshness"],
            gates_failed=[],
            rejection_reasons=[],
            freshness_raw_score=100.0,
            buying_signal_raw_score=100.0,
            source_trust_raw_score=100.0,
            website_quality_raw_score=100.0,
            company_validation_raw_score=100.0,
            icp_match_raw_score=100.0,
            region_raw_score=100.0,
            industry_raw_score=100.0,
        )
        assert report.quality_score is not None
        assert report.quality_grade == QualityGrade.A_PLUS
        assert report.decision == "ACCEPT"
        assert len(report.gates_passed) == 3

    def test_generate_rejection_report(self):
        from uuid import uuid4
        engine = QualityReportEngine()
        report = engine.generate_rejection_report(
            company_id=uuid4(),
            company_name="Bad Corp",
            rejection_reasons=["COMPETITOR"],
            gates_failed=["competitor"],
        )
        assert report.quality_score is None
        assert report.quality_grade == QualityGrade.REJECT
        assert report.decision == "REJECT"
