"""Validation engine — orchestrates all validation components.

Compose-only. Never modifies existing intelligence engines.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from validation_engine.deal_tracker import DealTracker
from validation_engine.lead_validator import LeadValidator
from validation_engine.meeting_tracker import MeetingTracker
from validation_engine.outcome_tracker import OutcomeTracker
from validation_engine.proposal_tracker import ProposalTracker
from validation_engine.reply_tracker import ReplyTracker
from validation_engine.timeline_engine import TimelineEngine


class ValidationEngine:
    """Main orchestrator for the validation platform."""

    def __init__(self) -> None:
        self.lead_validator = LeadValidator()
        self.outcome_tracker = OutcomeTracker()
        self.reply_tracker = ReplyTracker()
        self.meeting_tracker = MeetingTracker()
        self.proposal_tracker = ProposalTracker()
        self.deal_tracker = DealTracker()
        self.timeline_engine = TimelineEngine()

    def record_email_sent(
        self,
        company_id: str,
        *,
        evidence: dict[str, Any] | None = None,
        source: str = "",
    ) -> dict[str, Any]:
        event = self.lead_validator.record_transition(
            company_id, "CONTACTED", evidence=evidence, source=source
        )
        self.timeline_engine.add_event(company_id, "CONTACTED", evidence=evidence, source=source)
        return {"ok": True, "event_id": event.event_id, "stage": "CONTACTED"}

    def record_email_opened(
        self,
        company_id: str,
        *,
        evidence: dict[str, Any] | None = None,
        source: str = "",
    ) -> dict[str, Any]:
        event = self.lead_validator.record_transition(
            company_id, "EMAIL_OPENED", evidence=evidence, source=source
        )
        self.timeline_engine.add_event(company_id, "EMAIL_OPENED", evidence=evidence, source=source)
        return {"ok": True, "event_id": event.event_id, "stage": "EMAIL_OPENED"}

    def record_email_clicked(
        self,
        company_id: str,
        *,
        evidence: dict[str, Any] | None = None,
        source: str = "",
    ) -> dict[str, Any]:
        event = self.lead_validator.record_transition(
            company_id, "EMAIL_CLICKED", evidence=evidence, source=source
        )
        self.timeline_engine.add_event(
            company_id, "EMAIL_CLICKED",
            evidence=evidence, source=source
        )
        return {"ok": True, "event_id": event.event_id, "stage": "EMAIL_CLICKED"}

    def record_reply(
        self,
        company_id: str,
        reply_type: str,
        *,
        evidence: dict[str, Any] | None = None,
        source: str = "",
        reply_time_seconds: float | None = None,
    ) -> dict[str, Any]:
        self.reply_tracker.record_reply(
            company_id, reply_type,
            evidence=evidence, source=source,
            reply_time_seconds=reply_time_seconds
        )
        if reply_type == "positive":
            self.lead_validator.record_transition(
                company_id, "REPLIED", evidence=evidence, source=source
            )
            self.timeline_engine.add_event(company_id, "REPLIED", evidence=evidence, source=source)
        return {"ok": True, "reply_type": reply_type}

    def record_meeting(
        self,
        company_id: str,
        meeting_type: str,
        *,
        duration_minutes: float | None = None,
        notes: str = "",
        next_action: str = "",
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.meeting_tracker.record_meeting(
            company_id, meeting_type, duration_minutes=duration_minutes,
            notes=notes, next_action=next_action, evidence=evidence,
        )
        if meeting_type in ("scheduled", "completed"):
            stage = "DISCOVERY_CALL" if meeting_type == "completed" else "MEETING_BOOKED"
            self.lead_validator.record_transition(company_id, stage, evidence=evidence)
            self.timeline_engine.add_event(company_id, stage, evidence=evidence)
        return {"ok": True, "meeting_type": meeting_type}

    def record_proposal(
        self,
        company_id: str,
        status: str,
        *,
        value: float | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.proposal_tracker.record_proposal(
            company_id, status, value=value, evidence=evidence,
        )
        if status == "sent":
            self.lead_validator.record_transition(company_id, "PROPOSAL_SENT", evidence=evidence)
            self.timeline_engine.add_event(company_id, "PROPOSAL_SENT", evidence=evidence)
        return {"ok": True, "status": status}

    def record_deal(
        self,
        company_id: str,
        status: str,
        *,
        revenue: float = 0.0,
        expected_revenue: float = 0.0,
        service_sold: str = "",
        reason: str = "",
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.deal_tracker.record_deal(
            company_id, status, revenue=revenue, expected_revenue=expected_revenue,
            service_sold=service_sold, reason=reason, evidence=evidence,
        )
        self.outcome_tracker.record_outcome(
            company_id, status, revenue=revenue, expected_revenue=expected_revenue,
            service_sold=service_sold, reason=reason, evidence=evidence,
        )
        stage = "WON" if status == "won" else "LOST" if status == "lost" else "PAUSED"
        self.lead_validator.record_transition(company_id, stage, evidence=evidence)
        self.timeline_engine.add_event(company_id, stage, evidence=evidence)
        return {"ok": True, "status": status, "revenue": revenue}

    def record_objection(
        self,
        company_id: str,
        category: str,
        *,
        evidence: dict[str, Any] | None = None,
        industry: str = "",
        service: str = "",
        connector: str = "",
        persona: str = "",
    ) -> dict[str, Any]:
        from validation_engine.objection_engine import ObjectionEngine
        engine = ObjectionEngine()
        engine.record_objection(
            company_id, category, evidence=evidence,
            industry=industry, service=service, connector=connector, persona=persona,
        )
        return {"ok": True, "category": category}

    def get_company_timeline(self, company_id: str) -> list[dict[str, Any]]:
        timeline = self.timeline_engine.get_timeline(company_id)
        return [
            {
                "stage": entry.stage,
                "timestamp": entry.timestamp.isoformat(),
                "evidence": entry.evidence,
                "source": entry.source,
                "duration_seconds": entry.duration_seconds,
            }
            for entry in timeline
        ]

    def get_funnel(self) -> list[dict[str, Any]]:
        return self.lead_validator.get_funnel()

    def get_dashboard_data(self) -> dict[str, Any]:
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "today_replies": len(self.reply_tracker.get_all_replies()),
            "today_meetings": len(self.meeting_tracker.get_todays_meetings()),
            "today_proposals": len(self.proposal_tracker.get_todays_proposals()),
            "today_wins": len(self.deal_tracker.get_todays_deals()),
            "today_revenue": sum(d.revenue for d in self.deal_tracker.get_todays_deals()),
            "reply_rate": self.reply_tracker.get_reply_rate(),
            "meeting_rate": self.meeting_tracker.get_meeting_rate(),
            "proposal_rate": self.proposal_tracker.get_proposal_rate(),
            "win_rate": self.deal_tracker.get_win_rate(),
            "total_revenue": self.deal_tracker.get_total_revenue(),
            "avg_deal_size": self.deal_tracker.get_avg_deal_size(),
            "funnel": self.get_funnel(),
        }
