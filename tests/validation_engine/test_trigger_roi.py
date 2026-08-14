"""Tests for TriggerRoiEngine."""

from __future__ import annotations

from validation_engine.trigger_roi import TriggerRoiEngine


class TestTriggerRoiEngineRecord:
    def test_record_company(self, trigger_roi: TriggerRoiEngine) -> None:
        trigger_roi.record_company("funding")
        roi = trigger_roi.calculate("funding")
        assert roi.companies == 1

    def test_record_reply(self, trigger_roi: TriggerRoiEngine) -> None:
        trigger_roi.record_reply("funding")
        roi = trigger_roi.calculate("funding")
        assert roi.replies == 1

    def test_record_meeting(self, trigger_roi: TriggerRoiEngine) -> None:
        trigger_roi.record_meeting("funding")
        roi = trigger_roi.calculate("funding")
        assert roi.meetings == 1

    def test_record_deal(self, trigger_roi: TriggerRoiEngine) -> None:
        trigger_roi.record_deal("funding", revenue=100000.0)
        roi = trigger_roi.calculate("funding")
        assert roi.deals == 1
        assert roi.revenue == 100000.0


class TestTriggerRoiEngineCalculate:
    def test_calculate_empty(self, trigger_roi: TriggerRoiEngine) -> None:
        roi = trigger_roi.calculate("nonexistent")
        assert roi.companies == 0
        assert roi.revenue == 0.0

    def test_calculate_reply_rate(self, trigger_roi: TriggerRoiEngine) -> None:
        trigger_roi.record_company("funding")
        trigger_roi.record_company("funding")
        trigger_roi.record_reply("funding")
        roi = trigger_roi.calculate("funding")
        assert roi.reply_rate == 50.0

    def test_calculate_meeting_rate(self, trigger_roi: TriggerRoiEngine) -> None:
        trigger_roi.record_reply("funding")
        trigger_roi.record_reply("funding")
        trigger_roi.record_meeting("funding")
        roi = trigger_roi.calculate("funding")
        assert roi.meeting_rate == 50.0

    def test_calculate_revenue_rate(self, trigger_roi: TriggerRoiEngine) -> None:
        trigger_roi.record_company("funding")
        trigger_roi.record_company("funding")
        trigger_roi.record_deal("funding")
        roi = trigger_roi.calculate("funding")
        assert roi.revenue_rate == 50.0


class TestTriggerRoiEngineRanking:
    def test_rank_by_revenue(self, trigger_roi: TriggerRoiEngine) -> None:
        trigger_roi.record_deal("funding", revenue=100000.0)
        trigger_roi.record_deal("hiring", revenue=200000.0)
        trigger_roi.record_deal("expansion", revenue=150000.0)
        ranked = trigger_roi.rank_by_revenue()
        assert ranked[0].trigger == "hiring"
        assert ranked[1].trigger == "expansion"
        assert ranked[2].trigger == "funding"

    def test_rank_by_conversion(self, trigger_roi: TriggerRoiEngine) -> None:
        trigger_roi.record_company("funding")
        trigger_roi.record_deal("funding")
        trigger_roi.record_company("hiring")
        trigger_roi.record_company("hiring")
        ranked = trigger_roi.rank_by_conversion()
        assert ranked[0].trigger == "funding"

    def test_get_best_trigger(self, trigger_roi: TriggerRoiEngine) -> None:
        trigger_roi.record_deal("funding", revenue=100000.0)
        best = trigger_roi.get_best_trigger()
        assert best is not None
        assert best.trigger == "funding"

    def test_get_best_trigger_none(self, trigger_roi: TriggerRoiEngine) -> None:
        best = trigger_roi.get_best_trigger()
        assert best is None
