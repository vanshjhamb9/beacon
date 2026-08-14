"""API route registration tests."""

from __future__ import annotations


class TestValidationEngineRoutes:
    def test_validation_engine_package_importable(self) -> None:
        import validation_engine
        assert validation_engine.SCORING_VERSION == "bvcl-v1"

    def test_validation_engine_constants(self) -> None:
        from validation_engine import MEETING_TYPES, REPLY_TYPES, VALIDATION_STAGES
        assert len(VALIDATION_STAGES) == 13
        assert len(REPLY_TYPES) == 7
        assert len(MEETING_TYPES) == 5

    def test_validation_engine_models_importable(self) -> None:
        from validation_engine.models import (
            ConnectorRoi,
            DailyReport,
            DealEvent,
            FunnelStage,
            IndustryRoi,
            MeetingEvent,
            MonthlyReport,
            ObjectionEvent,
            PersonaRoi,
            ProposalEvent,
            ReplyEvent,
            ServiceRoi,
            TimelineEntry,
            TriggerRoi,
            ValidationDashboard,
            ValidationEvent,
            WeeklyReport,
        )
        assert all([
            ValidationEvent, TimelineEntry, ReplyEvent, MeetingEvent,
            ProposalEvent, DealEvent, ObjectionEvent, ConnectorRoi,
            IndustryRoi, ServiceRoi, PersonaRoi, TriggerRoi, FunnelStage,
            ValidationDashboard, DailyReport, WeeklyReport, MonthlyReport,
        ])

    def test_validation_engine_modules_importable(self) -> None:
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
        from validation_engine.validation_dashboard import ValidationDashboardService
        from validation_engine.validation_engine import ValidationEngine
        from validation_engine.validation_metrics import ValidationMetrics
        from validation_engine.validation_reports import ValidationReportService
        from validation_engine.validation_scheduler import ValidationScheduler
        assert all([
            LeadValidator, ReplyTracker, MeetingTracker, ProposalTracker,
            DealTracker, TimelineEngine, ConnectorRoiEngine, IndustryRoiEngine,
            ServiceRoiEngine, PersonaRoiEngine, TriggerRoiEngine, ObjectionEngine,
            OutcomeTracker, FunnelEngine, CalibrationEngine, ValidationEngine,
            ValidationDashboardService, ValidationReportService, ValidationScheduler,
            ValidationMetrics,
        ])

    def test_validation_engine_version(self) -> None:
        from validation_engine import SCORING_VERSION
        assert SCORING_VERSION == "bvcl-v1"

    def test_validation_stages_complete(self) -> None:
        from validation_engine import VALIDATION_STAGES
        expected = [
            "REVENUE_READY", "CONTACTED", "EMAIL_OPENED", "EMAIL_CLICKED",
            "REPLIED", "MEETING_BOOKED", "DISCOVERY_CALL", "PROPOSAL_SENT",
            "NEGOTIATION", "WON", "LOST", "NO_RESPONSE", "PAUSED",
        ]
        assert VALIDATION_STAGES == tuple(expected)

    def test_reply_types_complete(self) -> None:
        from validation_engine import REPLY_TYPES
        expected = [
            "positive", "negative", "auto_reply", "out_of_office",
            "bounce", "spam", "no_response",
        ]
        assert REPLY_TYPES == tuple(expected)

    def test_meeting_types_complete(self) -> None:
        from validation_engine import MEETING_TYPES
        expected = ["scheduled", "completed", "cancelled", "no_show", "rescheduled"]
        assert MEETING_TYPES == tuple(expected)

    def test_proposal_statuses_complete(self) -> None:
        from validation_engine import PROPOSAL_STATUSES
        expected = ["created", "sent", "viewed", "accepted", "rejected", "expired"]
        assert PROPOSAL_STATUSES == tuple(expected)

    def test_deal_statuses_complete(self) -> None:
        from validation_engine import DEAL_STATUSES
        expected = ["won", "lost", "paused"]
        assert DEAL_STATUSES == tuple(expected)

    def test_objection_categories_complete(self) -> None:
        from validation_engine import OBJECTION_CATEGORIES
        expected = [
            "no_budget", "wrong_timing", "already_have_vendor", "no_need",
            "too_expensive", "internal_team", "not_priority", "no_response", "other",
        ]
        assert OBJECTION_CATEGORIES == tuple(expected)
