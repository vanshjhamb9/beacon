"""Tests for ServiceRoiEngine."""

from __future__ import annotations

from validation_engine.service_roi import ServiceRoiEngine


class TestServiceRoiEngineRecord:
    def test_record_company(self, service_roi: ServiceRoiEngine) -> None:
        service_roi.record_company("ai_automation")
        roi = service_roi.calculate("ai_automation")
        assert roi.companies == 1

    def test_record_reply(self, service_roi: ServiceRoiEngine) -> None:
        service_roi.record_reply("ai_automation")
        roi = service_roi.calculate("ai_automation")
        assert roi.replies == 1

    def test_record_meeting(self, service_roi: ServiceRoiEngine) -> None:
        service_roi.record_meeting("ai_automation")
        roi = service_roi.calculate("ai_automation")
        assert roi.meetings == 1

    def test_record_proposal(self, service_roi: ServiceRoiEngine) -> None:
        service_roi.record_proposal("ai_automation")
        roi = service_roi.calculate("ai_automation")
        assert roi.meetings == 0

    def test_record_deal(self, service_roi: ServiceRoiEngine) -> None:
        service_roi.record_deal("ai_automation", revenue=75000.0)
        roi = service_roi.calculate("ai_automation")
        assert roi.deals == 1
        assert roi.revenue == 75000.0


class TestServiceRoiEngineCalculate:
    def test_calculate_empty(self, service_roi: ServiceRoiEngine) -> None:
        roi = service_roi.calculate("nonexistent")
        assert roi.companies == 0
        assert roi.revenue == 0.0

    def test_calculate_reply_rate(self, service_roi: ServiceRoiEngine) -> None:
        service_roi.record_company("ai_automation")
        service_roi.record_company("ai_automation")
        service_roi.record_reply("ai_automation")
        roi = service_roi.calculate("ai_automation")
        assert roi.reply_rate == 50.0

    def test_calculate_meeting_rate(self, service_roi: ServiceRoiEngine) -> None:
        service_roi.record_reply("ai_automation")
        service_roi.record_reply("ai_automation")
        service_roi.record_meeting("ai_automation")
        roi = service_roi.calculate("ai_automation")
        assert roi.meeting_rate == 50.0

    def test_calculate_win_rate(self, service_roi: ServiceRoiEngine) -> None:
        service_roi.record_proposal("ai_automation")
        service_roi.record_proposal("ai_automation")
        service_roi.record_deal("ai_automation")
        roi = service_roi.calculate("ai_automation")
        assert roi.win_rate == 50.0


class TestServiceRoiEngineRanking:
    def test_rank_by_revenue(self, service_roi: ServiceRoiEngine) -> None:
        service_roi.record_deal("ai_automation", revenue=100000.0)
        service_roi.record_deal("crm", revenue=200000.0)
        service_roi.record_deal("website", revenue=150000.0)
        ranked = service_roi.rank_by_revenue()
        assert ranked[0].service == "crm"
        assert ranked[1].service == "website"
        assert ranked[2].service == "ai_automation"

    def test_rank_by_win_rate(self, service_roi: ServiceRoiEngine) -> None:
        service_roi.record_meeting("ai_automation")
        service_roi.record_deal("ai_automation")
        service_roi.record_meeting("crm")
        service_roi.record_meeting("crm")
        ranked = service_roi.rank_by_win_rate()
        assert ranked[0].service == "ai_automation"

    def test_get_best_service(self, service_roi: ServiceRoiEngine) -> None:
        service_roi.record_deal("ai_automation", revenue=100000.0)
        best = service_roi.get_best_service()
        assert best is not None
        assert best.service == "ai_automation"

    def test_get_best_service_none(self, service_roi: ServiceRoiEngine) -> None:
        best = service_roi.get_best_service()
        assert best is None
