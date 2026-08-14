"""Tests for PersonaRoiEngine."""

from __future__ import annotations

from validation_engine.persona_roi import PersonaRoiEngine


class TestPersonaRoiEngineRecord:
    def test_record_contacted(self, persona_roi: PersonaRoiEngine) -> None:
        persona_roi.record_contacted("founder")
        roi = persona_roi.calculate("founder")
        assert roi.contacted == 1

    def test_record_reply(self, persona_roi: PersonaRoiEngine) -> None:
        persona_roi.record_reply("founder")
        roi = persona_roi.calculate("founder")
        assert roi.replies == 1

    def test_record_meeting(self, persona_roi: PersonaRoiEngine) -> None:
        persona_roi.record_meeting("founder")
        roi = persona_roi.calculate("founder")
        assert roi.meetings == 1

    def test_record_deal(self, persona_roi: PersonaRoiEngine) -> None:
        persona_roi.record_deal("founder", revenue=100000.0)
        roi = persona_roi.calculate("founder")
        assert roi.deals == 1
        assert roi.revenue == 100000.0


class TestPersonaRoiEngineCalculate:
    def test_calculate_empty(self, persona_roi: PersonaRoiEngine) -> None:
        roi = persona_roi.calculate("nonexistent")
        assert roi.contacted == 0
        assert roi.revenue == 0.0

    def test_calculate_reply_rate(self, persona_roi: PersonaRoiEngine) -> None:
        persona_roi.record_contacted("founder")
        persona_roi.record_contacted("founder")
        persona_roi.record_reply("founder")
        roi = persona_roi.calculate("founder")
        assert roi.reply_rate == 50.0

    def test_calculate_meeting_rate(self, persona_roi: PersonaRoiEngine) -> None:
        persona_roi.record_reply("founder")
        persona_roi.record_reply("founder")
        persona_roi.record_meeting("founder")
        roi = persona_roi.calculate("founder")
        assert roi.meeting_rate == 50.0


class TestPersonaRoiEngineRanking:
    def test_rank_by_revenue(self, persona_roi: PersonaRoiEngine) -> None:
        persona_roi.record_deal("founder", revenue=100000.0)
        persona_roi.record_deal("cto", revenue=200000.0)
        persona_roi.record_deal("ceo", revenue=150000.0)
        ranked = persona_roi.rank_by_revenue()
        assert ranked[0].persona == "cto"
        assert ranked[1].persona == "ceo"
        assert ranked[2].persona == "founder"

    def test_rank_by_reply_rate(self, persona_roi: PersonaRoiEngine) -> None:
        persona_roi.record_contacted("founder")
        persona_roi.record_reply("founder")
        persona_roi.record_contacted("cto")
        persona_roi.record_contacted("cto")
        ranked = persona_roi.rank_by_reply_rate()
        assert ranked[0].persona == "founder"

    def test_get_best_persona(self, persona_roi: PersonaRoiEngine) -> None:
        persona_roi.record_deal("founder", revenue=100000.0)
        best = persona_roi.get_best_persona()
        assert best is not None
        assert best.persona == "founder"

    def test_get_best_persona_none(self, persona_roi: PersonaRoiEngine) -> None:
        best = persona_roi.get_best_persona()
        assert best is None
