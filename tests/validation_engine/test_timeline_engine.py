"""Tests for TimelineEngine."""

from __future__ import annotations

import pytest

from validation_engine.timeline_engine import TimelineEngine


class TestTimelineEngineAddEvent:
    def test_add_valid_event(self, timeline_engine: TimelineEngine) -> None:
        entry = timeline_engine.add_event("company_1", "REVENUE_READY")
        assert entry.stage == "REVENUE_READY"

    def test_add_invalid_stage_raises(self, timeline_engine: TimelineEngine) -> None:
        with pytest.raises(ValueError, match="Invalid stage"):
            timeline_engine.add_event("company_1", "INVALID")

    def test_add_multiple_events(self, timeline_engine: TimelineEngine) -> None:
        timeline_engine.add_event("company_1", "REVENUE_READY")
        timeline_engine.add_event("company_1", "CONTACTED")
        timeline_engine.add_event("company_1", "REPLIED")
        timeline = timeline_engine.get_timeline("company_1")
        assert len(timeline) == 3

    def test_add_with_evidence(self, timeline_engine: TimelineEngine) -> None:
        entry = timeline_engine.add_event("company_1", "CONTACTED", evidence={"source": "email"})
        assert entry.evidence == {"source": "email"}

    def test_add_with_source(self, timeline_engine: TimelineEngine) -> None:
        entry = timeline_engine.add_event("company_1", "CONTACTED", source="linkedin")
        assert entry.source == "linkedin"

    def test_add_with_duration(self, timeline_engine: TimelineEngine) -> None:
        entry = timeline_engine.add_event("company_1", "CONTACTED", duration_seconds=3600.0)
        assert entry.duration_seconds == 3600.0


class TestTimelineEngineGetTimeline:
    def test_get_empty_timeline(self, timeline_engine: TimelineEngine) -> None:
        timeline = timeline_engine.get_timeline("nonexistent")
        assert timeline == []

    def test_get_timeline_returns_copy(self, timeline_engine: TimelineEngine) -> None:
        timeline_engine.add_event("company_1", "REVENUE_READY")
        t1 = timeline_engine.get_timeline("company_1")
        t2 = timeline_engine.get_timeline("company_1")
        assert t1 is not t2


class TestTimelineEngineGetLatestStage:
    def test_get_latest_stage_empty(self, timeline_engine: TimelineEngine) -> None:
        stage = timeline_engine.get_latest_stage("nonexistent")
        assert stage is None

    def test_get_latest_stage(self, timeline_engine: TimelineEngine) -> None:
        timeline_engine.add_event("company_1", "REVENUE_READY")
        timeline_engine.add_event("company_1", "CONTACTED")
        stage = timeline_engine.get_latest_stage("company_1")
        assert stage == "CONTACTED"


class TestTimelineEngineGetStageHistory:
    def test_get_stage_history_empty(self, timeline_engine: TimelineEngine) -> None:
        history = timeline_engine.get_stage_history("nonexistent")
        assert history == []

    def test_get_stage_history(self, timeline_engine: TimelineEngine) -> None:
        timeline_engine.add_event("company_1", "REVENUE_READY")
        timeline_engine.add_event("company_1", "CONTACTED")
        timeline_engine.add_event("company_1", "REPLIED")
        history = timeline_engine.get_stage_history("company_1")
        assert history == ["REVENUE_READY", "CONTACTED", "REPLIED"]


class TestTimelineEngineGetCompaniesAtStage:
    def test_get_companies_at_stage_empty(self, timeline_engine: TimelineEngine) -> None:
        companies = timeline_engine.get_companies_at_stage("REVENUE_READY")
        assert companies == []

    def test_get_companies_at_stage(self, timeline_engine: TimelineEngine) -> None:
        timeline_engine.add_event("company_1", "REVENUE_READY")
        timeline_engine.add_event("company_1", "CONTACTED")
        timeline_engine.add_event("company_2", "REVENUE_READY")
        companies = timeline_engine.get_companies_at_stage("REVENUE_READY")
        assert companies == ["company_2"]


class TestTimelineEngineGetCompaniesWhoReachedStage:
    def test_get_companies_who_reached_stage(self, timeline_engine: TimelineEngine) -> None:
        timeline_engine.add_event("company_1", "REVENUE_READY")
        timeline_engine.add_event("company_1", "CONTACTED")
        timeline_engine.add_event("company_2", "REVENUE_READY")
        companies = timeline_engine.get_companies_who_reached_stage("CONTACTED")
        assert companies == ["company_1"]


class TestTimelineEngineBuildStageSummary:
    def test_build_stage_summary(self, timeline_engine: TimelineEngine) -> None:
        timeline_engine.add_event("company_1", "REVENUE_READY")
        timeline_engine.add_event("company_1", "CONTACTED")
        timeline_engine.add_event("company_2", "REVENUE_READY")
        summary = timeline_engine.build_stage_summary()
        assert "REVENUE_READY" in summary
        assert "CONTACTED" in summary
        assert summary["REVENUE_READY"]["current_count"] == 1
        assert summary["REVENUE_READY"]["total_reached"] == 2
