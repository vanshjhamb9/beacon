"""Validation metrics — computes aggregate validation metrics."""

from __future__ import annotations

from typing import Any

from validation_engine.connector_roi import ConnectorRoiEngine
from validation_engine.deal_tracker import DealTracker
from validation_engine.funnel_engine import FunnelEngine
from validation_engine.lead_validator import LeadValidator
from validation_engine.meeting_tracker import MeetingTracker
from validation_engine.objection_engine import ObjectionEngine
from validation_engine.proposal_tracker import ProposalTracker
from validation_engine.reply_tracker import ReplyTracker


class ValidationMetrics:
    """Computes aggregate validation metrics from all trackers."""

    def __init__(
        self,
        *,
        lead_validator: LeadValidator | None = None,
        reply_tracker: ReplyTracker | None = None,
        meeting_tracker: MeetingTracker | None = None,
        proposal_tracker: ProposalTracker | None = None,
        deal_tracker: DealTracker | None = None,
        connector_roi: ConnectorRoiEngine | None = None,
        objection_engine: ObjectionEngine | None = None,
    ) -> None:
        self.lead_validator = lead_validator or LeadValidator()
        self.reply_tracker = reply_tracker or ReplyTracker()
        self.meeting_tracker = meeting_tracker or MeetingTracker()
        self.proposal_tracker = proposal_tracker or ProposalTracker()
        self.deal_tracker = deal_tracker or DealTracker()
        self.connector_roi = connector_roi or ConnectorRoiEngine()
        self.objection_engine = objection_engine or ObjectionEngine()

    def get_all_metrics(self) -> dict[str, Any]:
        funnel_engine = FunnelEngine(self.lead_validator)
        return {
            "total_revenue": self.deal_tracker.get_total_revenue(),
            "win_rate": self.deal_tracker.get_win_rate(),
            "avg_deal_size": self.deal_tracker.get_avg_deal_size(),
            "reply_rate": self.reply_tracker.get_reply_rate(),
            "positive_reply_rate": self.reply_tracker.get_positive_reply_rate(),
            "avg_reply_time": self.reply_tracker.get_avg_reply_time(),
            "meeting_rate": self.meeting_tracker.get_meeting_rate(),
            "no_show_rate": self.meeting_tracker.get_no_show_rate(),
            "avg_meeting_duration": self.meeting_tracker.get_avg_duration(),
            "proposal_rate": self.proposal_tracker.get_proposal_rate(),
            "proposal_acceptance_rate": self.proposal_tracker.get_acceptance_rate(),
            "total_proposals_sent": len(self.proposal_tracker.get_sent_proposals()),
            "total_meetings_completed": len(self.meeting_tracker.get_completed_meetings()),
            "total_replies": len(self.reply_tracker.get_all_replies()),
            "total_won": len(self.deal_tracker.get_won_deals()),
            "total_lost": len(self.deal_tracker.get_lost_deals()),
            "reply_type_distribution": self.reply_tracker.get_reply_type_counts(),
            "meeting_type_distribution": self.meeting_tracker.get_meeting_type_counts(),
            "proposal_status_distribution": self.proposal_tracker.get_status_counts(),
            "deal_status_distribution": self.deal_tracker.get_deals_by_status(),
            "top_objections": self.objection_engine.get_top_objections(limit=10),
            "funnel_summary": funnel_engine.get_conversion_summary(),
            "best_connector": (
                self.connector_roi.get_best_connector().connector
                if self.connector_roi.get_best_connector()
                else None
            ),
        }
