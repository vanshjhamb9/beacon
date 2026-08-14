"""Validation dashboard — assembles the live validation dashboard payload."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from validation_engine import SCORING_VERSION
from validation_engine.connector_roi import ConnectorRoiEngine
from validation_engine.deal_tracker import DealTracker
from validation_engine.lead_validator import LeadValidator
from validation_engine.meeting_tracker import MeetingTracker
from validation_engine.models import FunnelStage, ValidationDashboard
from validation_engine.proposal_tracker import ProposalTracker
from validation_engine.reply_tracker import ReplyTracker


class ValidationDashboardService:
    """Assembles the validation dashboard from tracker data."""

    def __init__(
        self,
        *,
        lead_validator: LeadValidator | None = None,
        reply_tracker: ReplyTracker | None = None,
        meeting_tracker: MeetingTracker | None = None,
        proposal_tracker: ProposalTracker | None = None,
        deal_tracker: DealTracker | None = None,
        connector_roi_engine: ConnectorRoiEngine | None = None,
    ) -> None:
        self.lead_validator = lead_validator or LeadValidator()
        self.reply_tracker = reply_tracker or ReplyTracker()
        self.meeting_tracker = meeting_tracker or MeetingTracker()
        self.proposal_tracker = proposal_tracker or ProposalTracker()
        self.deal_tracker = deal_tracker or DealTracker()
        self.connector_roi_engine = connector_roi_engine or ConnectorRoiEngine()

    def build(self) -> ValidationDashboard:
        funnel_stages = [
            FunnelStage(
                stage=f["stage"],
                count=f["count"],
                conversion_from_previous=f["conversion_from_previous"],
                drop_off=f["drop_off"],
            )
            for f in self.lead_validator.get_funnel()
        ]

        return ValidationDashboard(
            generated_at=datetime.now(UTC),
            today_replies=len(self.reply_tracker.get_all_replies()),
            today_meetings=len(self.meeting_tracker.get_all_meetings()),
            today_proposals=len(self.proposal_tracker.get_all_proposals()),
            today_wins=len(self.deal_tracker.get_won_deals()),
            today_revenue=self.deal_tracker.get_total_revenue(),
            reply_rate=self.reply_tracker.get_reply_rate(),
            meeting_rate=self.meeting_tracker.get_meeting_rate(),
            proposal_rate=self.proposal_tracker.get_proposal_rate(),
            win_rate=self.deal_tracker.get_win_rate(),
            avg_sales_cycle_days=0.0,
            funnel=funnel_stages,
            connector_roi=self.connector_roi_engine.calculate_all(),
            scoring_version=SCORING_VERSION,
        )

    def to_dict(self, dashboard: ValidationDashboard) -> dict[str, Any]:
        payload = asdict(dashboard)
        payload["generated_at"] = dashboard.generated_at.isoformat()
        return payload
