"""Tests for LeadValidator."""

from __future__ import annotations

import pytest

from validation_engine import VALIDATION_STAGES
from validation_engine.lead_validator import LeadValidator


class TestLeadValidatorRecordTransition:
    def test_record_valid_stage(self, lead_validator: LeadValidator) -> None:
        event = lead_validator.record_transition("company_1", "REVENUE_READY")
        assert event.company_id == "company_1"
        assert event.stage == "REVENUE_READY"
        assert event.event_id.startswith("evt_company_1")

    def test_record_invalid_stage_raises(self, lead_validator: LeadValidator) -> None:
        with pytest.raises(ValueError, match="Invalid stage"):
            lead_validator.record_transition("company_1", "INVALID_STAGE")

    def test_record_with_evidence(self, lead_validator: LeadValidator) -> None:
        evidence = {"source": "email", "campaign_id": "abc"}
        event = lead_validator.record_transition("company_1", "CONTACTED", evidence=evidence)
        assert event.evidence == evidence

    def test_record_with_source(self, lead_validator: LeadValidator) -> None:
        event = lead_validator.record_transition("company_1", "CONTACTED", source="linkedin")
        assert event.source == "linkedin"

    def test_record_with_confidence(self, lead_validator: LeadValidator) -> None:
        event = lead_validator.record_transition("company_1", "CONTACTED", confidence=0.85)
        assert event.confidence == 0.85

    def test_record_multiple_transitions(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        lead_validator.record_transition("company_1", "EMAIL_OPENED")
        assert lead_validator.get_stage_count("REVENUE_READY") == 1
        assert lead_validator.get_stage_count("CONTACTED") == 1
        assert lead_validator.get_stage_count("EMAIL_OPENED") == 1

    def test_record_default_evidence(self, lead_validator: LeadValidator) -> None:
        event = lead_validator.record_transition("company_1", "CONTACTED")
        assert event.evidence == {}

    def test_record_default_source(self, lead_validator: LeadValidator) -> None:
        event = lead_validator.record_transition("company_1", "CONTACTED")
        assert event.source == ""

    def test_record_default_confidence(self, lead_validator: LeadValidator) -> None:
        event = lead_validator.record_transition("company_1", "CONTACTED")
        assert event.confidence == 1.0


class TestLeadValidatorGetTimeline:
    def test_get_empty_timeline(self, lead_validator: LeadValidator) -> None:
        timeline = lead_validator.get_timeline("nonexistent")
        assert timeline == []

    def test_get_timeline_after_transitions(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        timeline = lead_validator.get_timeline("company_1")
        assert len(timeline) == 2
        assert timeline[0].stage == "REVENUE_READY"
        assert timeline[1].stage == "CONTACTED"

    def test_get_timeline_returns_copy(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        timeline1 = lead_validator.get_timeline("company_1")
        timeline2 = lead_validator.get_timeline("company_1")
        assert timeline1 is not timeline2
        assert len(timeline1) == len(timeline2)


class TestLeadValidatorGetAllEvents:
    def test_get_empty_events(self, lead_validator: LeadValidator) -> None:
        events = lead_validator.get_all_events()
        assert events == []

    def test_get_events_after_recording(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_2", "CONTACTED")
        events = lead_validator.get_all_events()
        assert len(events) == 2


class TestLeadValidatorGetEventsByStage:
    def test_get_events_by_stage_empty(self, lead_validator: LeadValidator) -> None:
        events = lead_validator.get_events_by_stage("REVENUE_READY")
        assert events == []

    def test_get_events_by_stage_filtered(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_2", "CONTACTED")
        lead_validator.record_transition("company_3", "REVENUE_READY")
        events = lead_validator.get_events_by_stage("REVENUE_READY")
        assert len(events) == 2


class TestLeadValidatorGetEventsByCompany:
    def test_get_events_by_company_empty(self, lead_validator: LeadValidator) -> None:
        events = lead_validator.get_events_by_company("nonexistent")
        assert events == []

    def test_get_events_by_company_filtered(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        lead_validator.record_transition("company_2", "REVENUE_READY")
        events = lead_validator.get_events_by_company("company_1")
        assert len(events) == 2


class TestLeadValidatorGetStageCount:
    def test_get_stage_count_empty(self, lead_validator: LeadValidator) -> None:
        assert lead_validator.get_stage_count("REVENUE_READY") == 0

    def test_get_stage_count_after_transitions(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_2", "REVENUE_READY")
        assert lead_validator.get_stage_count("REVENUE_READY") == 2


class TestLeadValidatorGetCompanyStage:
    def test_get_company_stage_empty(self, lead_validator: LeadValidator) -> None:
        assert lead_validator.get_company_stage("nonexistent") is None

    def test_get_company_stage_latest(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        assert lead_validator.get_company_stage("company_1") == "CONTACTED"


class TestLeadValidatorGetCompaniesInStage:
    def test_get_companies_in_stage_empty(self, lead_validator: LeadValidator) -> None:
        companies = lead_validator.get_companies_in_stage("REVENUE_READY")
        assert companies == []

    def test_get_companies_in_stage(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        lead_validator.record_transition("company_2", "REVENUE_READY")
        companies = lead_validator.get_companies_in_stage("REVENUE_READY")
        assert companies == ["company_2"]


class TestLeadValidatorCalculateConversionRate:
    def test_conversion_rate_zero(self, lead_validator: LeadValidator) -> None:
        rate = lead_validator.calculate_conversion_rate("REVENUE_READY", "CONTACTED")
        assert rate == 0.0

    def test_conversion_rate_calculated(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_2", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        rate = lead_validator.calculate_conversion_rate("REVENUE_READY", "CONTACTED")
        assert rate == 50.0


class TestLeadValidatorCalculateAvgTimeBetweenStages:
    def test_avg_time_none_when_no_data(self, lead_validator: LeadValidator) -> None:
        avg = lead_validator.calculate_avg_time_between_stages(
            "company_1", "REVENUE_READY", "CONTACTED"
        )
        assert avg is None

    def test_avg_time_none_when_missing_stages(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        avg = lead_validator.calculate_avg_time_between_stages(
            "company_1", "REVENUE_READY", "CONTACTED"
        )
        assert avg is None


class TestLeadValidatorGetFunnel:
    def test_empty_funnel(self, lead_validator: LeadValidator) -> None:
        funnel = lead_validator.get_funnel()
        assert len(funnel) == len(VALIDATION_STAGES)
        assert all(f["count"] == 0 for f in funnel)

    def test_funnel_with_data(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        lead_validator.record_transition("company_1", "REPLIED")
        funnel = lead_validator.get_funnel()
        rr_stage = next(f for f in funnel if f["stage"] == "REVENUE_READY")
        contacted_stage = next(f for f in funnel if f["stage"] == "CONTACTED")
        replied_stage = next(f for f in funnel if f["stage"] == "REPLIED")
        assert rr_stage["count"] == 1
        assert contacted_stage["count"] == 1
        assert replied_stage["count"] == 1
        assert contacted_stage["conversion_from_previous"] == 100.0

    def test_funnel_conversion_calculation(self, lead_validator: LeadValidator) -> None:
        lead_validator.record_transition("company_1", "REVENUE_READY")
        lead_validator.record_transition("company_2", "REVENUE_READY")
        lead_validator.record_transition("company_3", "REVENUE_READY")
        lead_validator.record_transition("company_1", "CONTACTED")
        lead_validator.record_transition("company_2", "CONTACTED")
        funnel = lead_validator.get_funnel()
        contacted_stage = next(f for f in funnel if f["stage"] == "CONTACTED")
        assert contacted_stage["conversion_from_previous"] == pytest.approx(66.67, rel=0.01)
        assert contacted_stage["drop_off"] == pytest.approx(33.33, rel=0.01)
