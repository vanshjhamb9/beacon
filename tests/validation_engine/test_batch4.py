"""Additional comprehensive tests for validation engine — batch 4."""

from __future__ import annotations

import pytest

from validation_engine.calibration_engine import CalibrationEngine
from validation_engine.connector_roi import ConnectorRoiEngine
from validation_engine.funnel_engine import FunnelEngine
from validation_engine.industry_roi import IndustryRoiEngine
from validation_engine.lead_validator import LeadValidator
from validation_engine.objection_engine import ObjectionEngine
from validation_engine.persona_roi import PersonaRoiEngine
from validation_engine.service_roi import ServiceRoiEngine
from validation_engine.timeline_engine import TimelineEngine
from validation_engine.trigger_roi import TriggerRoiEngine
from validation_engine.validation_dashboard import ValidationDashboardService
from validation_engine.validation_engine import ValidationEngine
from validation_engine.validation_metrics import ValidationMetrics
from validation_engine.validation_reports import ValidationReportService

# --- ValidationDashboardService Batch 4 ---

class TestValidationDashboardServiceBatch4:
    def test_dashboard_with_reply_data(self) -> None:
        service = ValidationDashboardService()
        service.reply_tracker.record_reply("company_1", "positive")
        service.reply_tracker.record_reply("company_2", "negative")
        dashboard = service.build()
        assert dashboard.today_replies == 2

    def test_dashboard_with_meeting_data(self) -> None:
        service = ValidationDashboardService()
        service.meeting_tracker.record_meeting("company_1", "completed")
        service.meeting_tracker.record_meeting("company_2", "cancelled")
        dashboard = service.build()
        assert dashboard.today_meetings == 2

    def test_dashboard_with_proposal_data(self) -> None:
        service = ValidationDashboardService()
        service.proposal_tracker.record_proposal("company_1", "sent")
        service.proposal_tracker.record_proposal("company_2", "accepted")
        dashboard = service.build()
        assert dashboard.today_proposals == 2

    def test_dashboard_with_deal_data(self) -> None:
        service = ValidationDashboardService()
        service.deal_tracker.record_deal("company_1", "won", revenue=50000.0)
        service.deal_tracker.record_deal("company_2", "won", revenue=75000.0)
        dashboard = service.build()
        assert dashboard.today_wins == 2
        assert dashboard.today_revenue == 125000.0

    def test_dashboard_funnel(self) -> None:
        service = ValidationDashboardService()
        dashboard = service.build()
        assert len(dashboard.funnel) > 0
        assert dashboard.funnel[0].stage == "REVENUE_READY"

    def test_dashboard_connector_roi(self) -> None:
        service = ValidationDashboardService()
        service.connector_roi_engine.record_deal("linkedin", revenue=50000.0)
        dashboard = service.build()
        assert len(dashboard.connector_roi) == 1
        assert dashboard.connector_roi[0].connector == "linkedin"

    def test_dashboard_to_dict(self) -> None:
        service = ValidationDashboardService()
        dashboard = service.build()
        payload = service.to_dict(dashboard)
        assert isinstance(payload, dict)
        assert "generated_at" in payload
        assert "today_replies" in payload
        assert "today_meetings" in payload
        assert "today_proposals" in payload
        assert "today_wins" in payload
        assert "today_revenue" in payload
        assert "reply_rate" in payload
        assert "meeting_rate" in payload
        assert "proposal_rate" in payload
        assert "win_rate" in payload
        assert "funnel" in payload
        assert "connector_roi" in payload


# --- ValidationReportService Batch 4 ---

class TestValidationReportServiceBatch4:
    def test_daily_report_empty(self) -> None:
        service = ValidationReportService()
        report = service.generate_daily_report()
        assert report.signals == 0
        assert report.companies == 0
        assert report.revenue_ready == 0
        assert report.emails_sent == 0
        assert report.replies == 0
        assert report.meetings == 0
        assert report.proposals == 0
        assert report.won == 0
        assert report.lost == 0
        assert report.revenue == 0.0

    def test_daily_report_with_replies(self) -> None:
        service = ValidationReportService()
        service.reply_tracker.record_reply("company_1", "positive")
        service.reply_tracker.record_reply("company_2", "negative")
        report = service.generate_daily_report()
        assert report.replies == 2

    def test_daily_report_with_meetings(self) -> None:
        service = ValidationReportService()
        service.meeting_tracker.record_meeting("company_1", "completed")
        report = service.generate_daily_report()
        assert report.meetings == 1

    def test_daily_report_with_deals(self) -> None:
        service = ValidationReportService()
        service.deal_tracker.record_deal("company_1", "won", revenue=100000.0)
        service.deal_tracker.record_deal("company_2", "lost")
        report = service.generate_daily_report()
        assert report.won == 1
        assert report.lost == 1
        assert report.revenue == 100000.0

    def test_weekly_report_empty(self) -> None:
        service = ValidationReportService()
        report = service.generate_weekly_report()
        assert report.revenue == 0.0
        assert report.meetings == 0
        assert report.deals == 0

    def test_weekly_report_with_data(self) -> None:
        service = ValidationReportService()
        service.deal_tracker.record_deal("company_1", "won", revenue=50000.0)
        service.meeting_tracker.record_meeting("company_1", "completed")
        report = service.generate_weekly_report()
        assert report.revenue == 50000.0
        assert report.meetings == 1

    def test_monthly_report_empty(self) -> None:
        service = ValidationReportService()
        report = service.generate_monthly_report()
        assert report.revenue == 0.0
        assert report.avg_deal_size == 0.0
        assert report.win_rate == 0.0

    def test_monthly_report_with_data(self) -> None:
        service = ValidationReportService()
        service.deal_tracker.record_deal("company_1", "won", revenue=100000.0)
        service.deal_tracker.record_deal("company_2", "won", revenue=50000.0)
        service.deal_tracker.record_deal("company_3", "lost")
        report = service.generate_monthly_report()
        assert report.revenue == 150000.0
        assert report.avg_deal_size == 75000.0
        assert report.win_rate == pytest.approx(66.67, rel=0.01)

    def test_monthly_report_revenue_per_connector(self) -> None:
        service = ValidationReportService()
        service.connector_roi.record_deal("linkedin", revenue=50000.0)
        service.connector_roi.record_deal("github", revenue=10000.0)
        report = service.generate_monthly_report()
        assert "linkedin" in report.revenue_per_connector
        assert "github" in report.revenue_per_connector

    def test_monthly_report_revenue_per_industry(self) -> None:
        service = ValidationReportService()
        service.industry_roi.record_deal("healthcare", revenue=100000.0)
        report = service.generate_monthly_report()
        assert "healthcare" in report.revenue_per_industry

    def test_monthly_report_revenue_per_service(self) -> None:
        service = ValidationReportService()
        service.service_roi.record_deal("ai_automation", revenue=75000.0)
        report = service.generate_monthly_report()
        assert "ai_automation" in report.revenue_per_service


# --- ValidationScheduler Batch 4 ---

class TestValidationSchedulerBatch4:
    def test_daily_report_cache_invalidation(self) -> None:
        from validation_engine.validation_scheduler import ValidationScheduler
        scheduler = ValidationScheduler()
        r1 = scheduler.get_daily_report()
        r2 = scheduler.get_daily_report(force=True)
        assert r1 is not r2

    def test_weekly_report_cache_invalidation(self) -> None:
        from validation_engine.validation_scheduler import ValidationScheduler
        scheduler = ValidationScheduler()
        r1 = scheduler.get_weekly_report()
        r2 = scheduler.get_weekly_report(force=True)
        assert r1 is not r2

    def test_monthly_report_cache_invalidation(self) -> None:
        from validation_engine.validation_scheduler import ValidationScheduler
        scheduler = ValidationScheduler()
        r1 = scheduler.get_monthly_report()
        r2 = scheduler.get_monthly_report(force=True)
        assert r1 is not r2

    def test_daily_report_structure(self) -> None:
        from validation_engine.validation_scheduler import ValidationScheduler
        scheduler = ValidationScheduler()
        report = scheduler.get_daily_report()
        assert "report_date" in report
        assert "signals" in report
        assert "companies" in report
        assert "revenue_ready" in report
        assert "emails_sent" in report
        assert "replies" in report
        assert "meetings" in report
        assert "proposals" in report
        assert "won" in report
        assert "lost" in report
        assert "revenue" in report

    def test_weekly_report_structure(self) -> None:
        from validation_engine.validation_scheduler import ValidationScheduler
        scheduler = ValidationScheduler()
        report = scheduler.get_weekly_report()
        assert "week_start" in report
        assert "week_end" in report
        assert "revenue" in report
        assert "meetings" in report
        assert "deals" in report

    def test_monthly_report_structure(self) -> None:
        from validation_engine.validation_scheduler import ValidationScheduler
        scheduler = ValidationScheduler()
        report = scheduler.get_monthly_report()
        assert "month" in report
        assert "revenue" in report
        assert "avg_deal_size" in report
        assert "win_rate" in report


# --- Cross-Module Integration Batch 4 ---

class TestCrossModuleIntegrationBatch4:
    def test_full_pipeline_flow(self) -> None:
        engine = ValidationEngine()
        for i in range(25):
            engine.record_email_sent(f"company_{i}")
            engine.record_email_opened(f"company_{i}")
            engine.record_email_clicked(f"company_{i}")
            engine.record_reply(f"company_{i}", "positive")
            engine.record_meeting(f"company_{i}", "scheduled")
            engine.record_meeting(f"company_{i}", "completed")
            engine.record_proposal(f"company_{i}", "sent")
            engine.record_proposal(f"company_{i}", "accepted")
            engine.record_deal(f"company_{i}", "won", revenue=float((i + 1) * 10000))
        dashboard = engine.get_dashboard_data()
        assert dashboard["total_revenue"] == sum((i + 1) * 10000 for i in range(25))

    def test_mixed_pipeline_outcomes(self) -> None:
        engine = ValidationEngine()
        for i in range(10):
            engine.record_email_sent(f"won_{i}")
            engine.record_reply(f"won_{i}", "positive")
            engine.record_meeting(f"won_{i}", "completed")
            engine.record_deal(f"won_{i}", "won", revenue=10000.0)
        for i in range(10):
            engine.record_email_sent(f"lost_{i}")
            engine.record_reply(f"lost_{i}", "negative")
            engine.record_deal(f"lost_{i}", "lost")
        dashboard = engine.get_dashboard_data()
        assert dashboard["total_revenue"] == 100000.0
        assert dashboard["win_rate"] == 50.0

    def test_connector_roi_integration(self) -> None:
        connector_roi = ConnectorRoiEngine()
        for i in range(5):
            connector_roi.record_signal(f"connector_{i}", companies=10, revenue_ready=5)
            connector_roi.record_reply(f"connector_{i}")
            connector_roi.record_meeting(f"connector_{i}")
            connector_roi.record_deal(f"connector_{i}", revenue=float(i * 10000))
        all_roi = connector_roi.calculate_all()
        assert len(all_roi) == 5
        ranked = connector_roi.rank_by_revenue()
        assert ranked[0].connector == "connector_4"
        assert ranked[-1].connector == "connector_0"

    def test_industry_roi_integration(self) -> None:
        industry_roi = IndustryRoiEngine()
        for i in range(5):
            industry_roi.record_company(f"industry_{i}")
            industry_roi.record_revenue_ready(f"industry_{i}")
            industry_roi.record_reply(f"industry_{i}")
            industry_roi.record_meeting(f"industry_{i}")
            industry_roi.record_deal(f"industry_{i}", revenue=float(i * 10000))
        all_roi = industry_roi.calculate_all()
        assert len(all_roi) == 5
        ranked = industry_roi.rank_by_revenue()
        assert ranked[0].industry == "industry_4"

    def test_service_roi_integration(self) -> None:
        service_roi = ServiceRoiEngine()
        for i in range(5):
            service_roi.record_company(f"service_{i}")
            service_roi.record_reply(f"service_{i}")
            service_roi.record_meeting(f"service_{i}")
            service_roi.record_proposal(f"service_{i}")
            service_roi.record_deal(f"service_{i}", revenue=float(i * 10000))
        all_roi = service_roi.calculate_all()
        assert len(all_roi) == 5

    def test_persona_roi_integration(self) -> None:
        persona_roi = PersonaRoiEngine()
        for i in range(5):
            persona_roi.record_contacted(f"persona_{i}")
            persona_roi.record_reply(f"persona_{i}")
            persona_roi.record_meeting(f"persona_{i}")
            persona_roi.record_deal(f"persona_{i}", revenue=float(i * 10000))
        all_roi = persona_roi.calculate_all()
        assert len(all_roi) == 5

    def test_trigger_roi_integration(self) -> None:
        trigger_roi = TriggerRoiEngine()
        for i in range(5):
            trigger_roi.record_company(f"trigger_{i}")
            trigger_roi.record_reply(f"trigger_{i}")
            trigger_roi.record_meeting(f"trigger_{i}")
            trigger_roi.record_deal(f"trigger_{i}", revenue=float(i * 10000))
        all_roi = trigger_roi.calculate_all()
        assert len(all_roi) == 5

    def test_objection_engine_integration(self) -> None:
        objection_engine = ObjectionEngine()
        for i in range(10):
            objection_engine.record_objection(
                f"company_{i}", "no_budget",
                industry="healthcare", service="ai_automation",
                connector="linkedin", persona="founder",
            )
        assert len(objection_engine.get_all_objections()) == 10
        assert len(objection_engine.get_by_industry("healthcare")) == 10
        assert len(objection_engine.get_by_service("ai_automation")) == 10
        assert len(objection_engine.get_by_connector("linkedin")) == 10
        assert len(objection_engine.get_by_persona("founder")) == 10

    def test_timeline_engine_integration(self) -> None:
        timeline_engine = TimelineEngine()
        stages = [
            "REVENUE_READY", "CONTACTED", "EMAIL_OPENED",
            "EMAIL_CLICKED", "REPLIED", "MEETING_BOOKED",
            "DISCOVERY_CALL", "PROPOSAL_SENT",
            "NEGOTIATION", "WON",
        ]
        for stage in stages:
            timeline_engine.add_event("company_1", stage)
        assert timeline_engine.get_latest_stage("company_1") == "WON"
        assert len(timeline_engine.get_timeline("company_1")) == 10
        assert timeline_engine.get_stage_history("company_1") == stages

    def test_funnel_engine_integration(self) -> None:
        lead_validator = LeadValidator()
        for i in range(20):
            lead_validator.record_transition(f"company_{i}", "REVENUE_READY")
        for i in range(15):
            lead_validator.record_transition(f"company_{i}", "CONTACTED")
        for i in range(10):
            lead_validator.record_transition(f"company_{i}", "REPLIED")
        for i in range(5):
            lead_validator.record_transition(f"company_{i}", "MEETING_BOOKED")
        for i in range(3):
            lead_validator.record_transition(f"company_{i}", "PROPOSAL_SENT")
        lead_validator.record_transition("company_0", "WON")
        funnel_engine = FunnelEngine(lead_validator)
        summary = funnel_engine.get_conversion_summary()
        assert summary["total_companies"] == 20
        assert summary["total_won"] == 1
        assert summary["overall_conversion_rate"] == 5.0

    def test_calibration_engine_integration(self) -> None:
        calibration_engine = CalibrationEngine()
        calibration_engine.connector_roi.record_deal("linkedin", revenue=100000.0)
        calibration_engine.connector_roi.record_deal("github", revenue=50000.0)
        calibration_engine.industry_roi.record_deal("healthcare", revenue=200000.0)
        calibration_engine.service_roi.record_deal("ai_automation", revenue=150000.0)
        calibration_engine.persona_roi.record_deal("founder", revenue=100000.0)
        calibration_engine.trigger_roi.record_deal("funding", revenue=100000.0)
        calibration_engine.deal_tracker.record_deal("c1", "won", revenue=100000.0)
        calibration_engine.deal_tracker.record_deal("c2", "won", revenue=75000.0)
        calibration_engine.deal_tracker.record_deal("c3", "lost")
        summary = calibration_engine.get_calibration_summary()
        assert summary["total_revenue"] == 175000.0
        assert summary["win_rate"] == pytest.approx(66.67, rel=0.01)
        assert len(summary["connector_ranking"]) == 2
        assert len(summary["industry_ranking"]) == 1
        assert len(summary["service_ranking"]) == 1
        assert len(summary["persona_ranking"]) == 1
        assert len(summary["trigger_ranking"]) == 1

    def test_validation_metrics_integration(self) -> None:
        metrics = ValidationMetrics()
        for i in range(20):
            metrics.reply_tracker.record_reply(f"company_{i}", "positive")
        for i in range(15):
            metrics.meeting_tracker.record_meeting(f"company_{i}", "completed")
        for i in range(10):
            metrics.proposal_tracker.record_proposal(f"company_{i}", "sent")
        for i in range(5):
            metrics.deal_tracker.record_deal(f"company_{i}", "won", revenue=float(i * 10000))
        for i in range(3):
            metrics.objection_engine.record_objection(f"company_{i}", "no_budget")
        result = metrics.get_all_metrics()
        assert result["total_replies"] == 20
        assert result["total_meetings_completed"] == 15
        assert result["total_proposals_sent"] == 10
        assert result["total_won"] == 5
        assert result["total_revenue"] == 100000.0
        assert result["reply_rate"] == 100.0
        assert result["meeting_rate"] == 100.0
        assert result["proposal_rate"] == 100.0

    def test_validation_dashboard_service_integration(self) -> None:
        service = ValidationDashboardService()
        service.reply_tracker.record_reply("company_1", "positive")
        service.meeting_tracker.record_meeting("company_1", "completed")
        service.proposal_tracker.record_proposal("company_1", "sent")
        service.deal_tracker.record_deal("company_1", "won", revenue=100000.0)
        service.connector_roi_engine.record_deal("linkedin", revenue=100000.0)
        dashboard = service.build()
        assert dashboard.today_replies == 1
        assert dashboard.today_meetings == 1
        assert dashboard.today_proposals == 1
        assert dashboard.today_wins == 1
        assert dashboard.today_revenue == 100000.0
        assert len(dashboard.connector_roi) == 1

    def test_validation_report_service_integration(self) -> None:
        service = ValidationReportService()
        service.reply_tracker.record_reply("company_1", "positive")
        service.meeting_tracker.record_meeting("company_1", "completed")
        service.proposal_tracker.record_proposal("company_1", "sent")
        service.deal_tracker.record_deal("company_1", "won", revenue=100000.0)
        service.connector_roi.record_deal("linkedin", revenue=100000.0)
        service.industry_roi.record_deal("healthcare", revenue=100000.0)
        service.service_roi.record_deal("ai_automation", revenue=100000.0)
        daily = service.generate_daily_report()
        weekly = service.generate_weekly_report()
        monthly = service.generate_monthly_report()
        assert daily.replies == 1
        assert daily.meetings == 1
        assert daily.won == 1
        assert daily.revenue == 100000.0
        assert weekly.revenue == 100000.0
        assert monthly.revenue == 100000.0
        assert "linkedin" in monthly.revenue_per_connector
        assert "healthcare" in monthly.revenue_per_industry
        assert "ai_automation" in monthly.revenue_per_service
