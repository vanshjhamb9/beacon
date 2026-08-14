"""Validation reports — generates daily, weekly, and monthly reports."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from validation_engine.connector_roi import ConnectorRoiEngine
from validation_engine.deal_tracker import DealTracker
from validation_engine.industry_roi import IndustryRoiEngine
from validation_engine.lead_validator import LeadValidator
from validation_engine.meeting_tracker import MeetingTracker
from validation_engine.models import DailyReport, MonthlyReport, WeeklyReport
from validation_engine.objection_engine import ObjectionEngine
from validation_engine.proposal_tracker import ProposalTracker
from validation_engine.reply_tracker import ReplyTracker
from validation_engine.service_roi import ServiceRoiEngine


class ValidationReportService:
    """Generates deterministic validation reports."""

    def __init__(
        self,
        *,
        lead_validator: LeadValidator | None = None,
        reply_tracker: ReplyTracker | None = None,
        meeting_tracker: MeetingTracker | None = None,
        proposal_tracker: ProposalTracker | None = None,
        deal_tracker: DealTracker | None = None,
        connector_roi: ConnectorRoiEngine | None = None,
        industry_roi: IndustryRoiEngine | None = None,
        service_roi: ServiceRoiEngine | None = None,
        objection_engine: ObjectionEngine | None = None,
    ) -> None:
        self.lead_validator = lead_validator or LeadValidator()
        self.reply_tracker = reply_tracker or ReplyTracker()
        self.meeting_tracker = meeting_tracker or MeetingTracker()
        self.proposal_tracker = proposal_tracker or ProposalTracker()
        self.deal_tracker = deal_tracker or DealTracker()
        self.connector_roi = connector_roi or ConnectorRoiEngine()
        self.industry_roi = industry_roi or IndustryRoiEngine()
        self.service_roi = service_roi or ServiceRoiEngine()
        self.objection_engine = objection_engine or ObjectionEngine()

    def generate_daily_report(self) -> DailyReport:
        now = datetime.now(UTC)
        report_date = now.strftime("%Y-%m-%d")
        best_connector = self.connector_roi.get_best_connector()
        worst_connector = self.connector_roi.get_worst_connector()
        best_industry = self.industry_roi.get_best_industry()
        top_objections = self.objection_engine.get_top_objections(limit=3)
        bottleneck = self.lead_validator.get_funnel()

        biggest_bottleneck = ""
        if bottleneck:
            worst = max(bottleneck, key=lambda x: x.get("drop_off", 0))
            biggest_bottleneck = worst.get("stage", "")

        return DailyReport(
            report_date=report_date,
            signals=0,
            companies=0,
            revenue_ready=self.lead_validator.get_stage_count("REVENUE_READY"),
            emails_sent=self.lead_validator.get_stage_count("CONTACTED"),
            replies=len(self.reply_tracker.get_all_replies()),
            meetings=len(self.meeting_tracker.get_all_meetings()),
            proposals=len(self.proposal_tracker.get_all_proposals()),
            won=len(self.deal_tracker.get_won_deals()),
            lost=len(self.deal_tracker.get_lost_deals()),
            revenue=self.deal_tracker.get_total_revenue(),
            best_connector=best_connector.connector if best_connector else "",
            worst_connector=worst_connector.connector if worst_connector else "",
            best_industry=best_industry.industry if best_industry else "",
            worst_industry="",
            top_objections=[o["category"] for o in top_objections],
            biggest_bottleneck=biggest_bottleneck,
        )

    def generate_weekly_report(self) -> WeeklyReport:
        now = datetime.now(UTC)
        week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        week_end = now.strftime("%Y-%m-%d")
        return WeeklyReport(
            week_start=week_start,
            week_end=week_end,
            revenue=self.deal_tracker.get_total_revenue(),
            meetings=len(self.meeting_tracker.get_all_meetings()),
            deals=len(self.deal_tracker.get_all_deals()),
            connector_ranking=self.connector_roi.rank_by_revenue(),
            industry_ranking=self.industry_roi.rank_by_revenue(),
            service_ranking=self.service_roi.rank_by_revenue(),
            persona_ranking=[],
            trigger_ranking=[],
        )

    def generate_monthly_report(self) -> MonthlyReport:
        now = datetime.now(UTC)
        month = now.strftime("%Y-%m")
        self.deal_tracker.get_won_deals()
        avg_deal = self.deal_tracker.get_avg_deal_size()
        total_revenue = self.deal_tracker.get_total_revenue()
        self.deal_tracker.get_all_deals()
        win_rate = self.deal_tracker.get_win_rate()
        reply_rate = self.reply_tracker.get_reply_rate()
        meeting_rate = self.meeting_tracker.get_meeting_rate()
        proposal_rate = self.proposal_tracker.get_proposal_rate()

        revenue_per_connector: dict[str, float] = {}
        for c in self.connector_roi.calculate_all():
            if c.revenue > 0:
                revenue_per_connector[c.connector] = c.revenue

        revenue_per_industry: dict[str, float] = {}
        for i in self.industry_roi.calculate_all():
            if i.revenue > 0:
                revenue_per_industry[i.industry] = i.revenue

        revenue_per_service: dict[str, float] = {}
        for s in self.service_roi.calculate_all():
            if s.revenue > 0:
                revenue_per_service[s.service] = s.revenue

        return MonthlyReport(
            month=month,
            revenue=total_revenue,
            avg_deal_size=avg_deal,
            avg_sales_cycle_days=0.0,
            reply_rate=reply_rate,
            meeting_rate=meeting_rate,
            proposal_rate=proposal_rate,
            win_rate=win_rate,
            revenue_per_connector=revenue_per_connector,
            revenue_per_industry=revenue_per_industry,
            revenue_per_service=revenue_per_service,
        )
