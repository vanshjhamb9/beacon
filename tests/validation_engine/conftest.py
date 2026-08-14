"""Test fixtures for validation engine tests."""

from __future__ import annotations

import pytest

from validation_engine.calibration_engine import CalibrationEngine
from validation_engine.connector_roi import ConnectorRoiEngine
from validation_engine.deal_tracker import DealTracker
from validation_engine.funnel_engine import FunnelEngine
from validation_engine.industry_roi import IndustryRoiEngine
from validation_engine.lead_validator import LeadValidator
from validation_engine.meeting_tracker import MeetingTracker
from validation_engine.objection_engine import ObjectionEngine
from validation_engine.outcome_tracker import OutcomeTracker
from validation_engine.persona_roi import PersonaRoiEngine
from validation_engine.proposal_tracker import ProposalTracker
from validation_engine.reply_tracker import ReplyTracker
from validation_engine.service_roi import ServiceRoiEngine
from validation_engine.timeline_engine import TimelineEngine
from validation_engine.trigger_roi import TriggerRoiEngine
from validation_engine.validation_engine import ValidationEngine


@pytest.fixture
def lead_validator() -> LeadValidator:
    return LeadValidator()


@pytest.fixture
def outcome_tracker() -> OutcomeTracker:
    return OutcomeTracker()


@pytest.fixture
def reply_tracker() -> ReplyTracker:
    return ReplyTracker()


@pytest.fixture
def meeting_tracker() -> MeetingTracker:
    return MeetingTracker()


@pytest.fixture
def proposal_tracker() -> ProposalTracker:
    return ProposalTracker()


@pytest.fixture
def deal_tracker() -> DealTracker:
    return DealTracker()


@pytest.fixture
def timeline_engine() -> TimelineEngine:
    return TimelineEngine()


@pytest.fixture
def connector_roi() -> ConnectorRoiEngine:
    return ConnectorRoiEngine()


@pytest.fixture
def industry_roi() -> IndustryRoiEngine:
    return IndustryRoiEngine()


@pytest.fixture
def service_roi() -> ServiceRoiEngine:
    return ServiceRoiEngine()


@pytest.fixture
def persona_roi() -> PersonaRoiEngine:
    return PersonaRoiEngine()


@pytest.fixture
def trigger_roi() -> TriggerRoiEngine:
    return TriggerRoiEngine()


@pytest.fixture
def objection_engine() -> ObjectionEngine:
    return ObjectionEngine()


@pytest.fixture
def funnel_engine(lead_validator: LeadValidator) -> FunnelEngine:
    return FunnelEngine(lead_validator)


@pytest.fixture
def calibration_engine() -> CalibrationEngine:
    return CalibrationEngine()


@pytest.fixture
def validation_engine() -> ValidationEngine:
    return ValidationEngine()
