"""Tests for ConnectorRoiEngine."""

from __future__ import annotations

from validation_engine.connector_roi import ConnectorRoiEngine


class TestConnectorRoiEngineRecord:
    def test_record_signal(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_signal("linkedin", companies=10, revenue_ready=5)
        roi = connector_roi.calculate("linkedin")
        assert roi.signals == 1
        assert roi.companies == 10
        assert roi.revenue_ready == 5

    def test_record_reply(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_reply("linkedin")
        connector_roi.record_reply("linkedin")
        roi = connector_roi.calculate("linkedin")
        assert roi.replies == 2

    def test_record_meeting(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_meeting("linkedin")
        roi = connector_roi.calculate("linkedin")
        assert roi.meetings == 1

    def test_record_deal(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_deal("linkedin", revenue=50000.0)
        roi = connector_roi.calculate("linkedin")
        assert roi.deals == 1
        assert roi.revenue == 50000.0


class TestConnectorRoiEngineCalculate:
    def test_calculate_empty(self, connector_roi: ConnectorRoiEngine) -> None:
        roi = connector_roi.calculate("nonexistent")
        assert roi.signals == 0
        assert roi.revenue == 0.0

    def test_calculate_reply_rate(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_signal("linkedin", revenue_ready=10)
        connector_roi.record_reply("linkedin")
        roi = connector_roi.calculate("linkedin")
        assert roi.reply_rate == 10.0

    def test_calculate_meeting_rate(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_reply("linkedin")
        connector_roi.record_reply("linkedin")
        connector_roi.record_meeting("linkedin")
        roi = connector_roi.calculate("linkedin")
        assert roi.meeting_rate == 50.0

    def test_calculate_win_rate(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_meeting("linkedin")
        connector_roi.record_meeting("linkedin")
        connector_roi.record_deal("linkedin")
        roi = connector_roi.calculate("linkedin")
        assert roi.win_rate == 50.0


class TestConnectorRoiEngineRanking:
    def test_rank_by_revenue(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_deal("github", revenue=10000.0)
        connector_roi.record_deal("linkedin", revenue=50000.0)
        connector_roi.record_deal("twitter", revenue=25000.0)
        ranked = connector_roi.rank_by_revenue()
        assert ranked[0].connector == "linkedin"
        assert ranked[1].connector == "twitter"
        assert ranked[2].connector == "github"

    def test_rank_by_meetings(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_meeting("github")
        connector_roi.record_meeting("linkedin")
        connector_roi.record_meeting("linkedin")
        connector_roi.record_meeting("linkedin")
        ranked = connector_roi.rank_by_meetings()
        assert ranked[0].connector == "linkedin"

    def test_get_best_connector(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_deal("linkedin", revenue=50000.0)
        best = connector_roi.get_best_connector()
        assert best is not None
        assert best.connector == "linkedin"

    def test_get_best_connector_none(self, connector_roi: ConnectorRoiEngine) -> None:
        best = connector_roi.get_best_connector()
        assert best is None

    def test_get_worst_connector(self, connector_roi: ConnectorRoiEngine) -> None:
        connector_roi.record_deal("linkedin", revenue=50000.0)
        connector_roi.record_deal("github", revenue=10000.0)
        worst = connector_roi.get_worst_connector()
        assert worst is not None
        assert worst.connector == "github"
