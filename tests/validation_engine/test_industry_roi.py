"""Tests for IndustryRoiEngine."""

from __future__ import annotations

from validation_engine.industry_roi import IndustryRoiEngine


class TestIndustryRoiEngineRecord:
    def test_record_company(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_company("healthcare")
        roi = industry_roi.calculate("healthcare")
        assert roi.companies == 1

    def test_record_revenue_ready(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_revenue_ready("healthcare")
        industry_roi.record_revenue_ready("healthcare")
        roi = industry_roi.calculate("healthcare")
        assert roi.revenue_ready == 2

    def test_record_reply(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_reply("healthcare")
        roi = industry_roi.calculate("healthcare")
        assert roi.replies == 1

    def test_record_meeting(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_meeting("healthcare")
        roi = industry_roi.calculate("healthcare")
        assert roi.meetings == 1

    def test_record_deal(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_deal("healthcare", revenue=100000.0)
        roi = industry_roi.calculate("healthcare")
        assert roi.deals == 1
        assert roi.revenue == 100000.0


class TestIndustryRoiEngineCalculate:
    def test_calculate_empty(self, industry_roi: IndustryRoiEngine) -> None:
        roi = industry_roi.calculate("nonexistent")
        assert roi.companies == 0
        assert roi.revenue == 0.0

    def test_calculate_reply_rate(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_revenue_ready("healthcare")
        industry_roi.record_revenue_ready("healthcare")
        industry_roi.record_reply("healthcare")
        roi = industry_roi.calculate("healthcare")
        assert roi.reply_rate == 50.0

    def test_calculate_meeting_rate(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_reply("healthcare")
        industry_roi.record_reply("healthcare")
        industry_roi.record_meeting("healthcare")
        roi = industry_roi.calculate("healthcare")
        assert roi.meeting_rate == 50.0

    def test_calculate_win_rate(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_meeting("healthcare")
        industry_roi.record_meeting("healthcare")
        industry_roi.record_deal("healthcare")
        roi = industry_roi.calculate("healthcare")
        assert roi.win_rate == 50.0


class TestIndustryRoiEngineRanking:
    def test_rank_by_revenue(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_deal("healthcare", revenue=100000.0)
        industry_roi.record_deal("fintech", revenue=200000.0)
        industry_roi.record_deal("saas", revenue=150000.0)
        ranked = industry_roi.rank_by_revenue()
        assert ranked[0].industry == "fintech"
        assert ranked[1].industry == "saas"
        assert ranked[2].industry == "healthcare"

    def test_rank_by_win_rate(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_meeting("healthcare")
        industry_roi.record_deal("healthcare")
        industry_roi.record_meeting("fintech")
        industry_roi.record_meeting("fintech")
        ranked = industry_roi.rank_by_win_rate()
        assert ranked[0].industry == "healthcare"

    def test_get_best_industry(self, industry_roi: IndustryRoiEngine) -> None:
        industry_roi.record_deal("healthcare", revenue=100000.0)
        best = industry_roi.get_best_industry()
        assert best is not None
        assert best.industry == "healthcare"

    def test_get_best_industry_none(self, industry_roi: IndustryRoiEngine) -> None:
        best = industry_roi.get_best_industry()
        assert best is None
