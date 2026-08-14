"""LROP v1 tests — comprehensive tests for all revenue operations components."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone, timedelta

from packages.live_revenue_operations import (
    OpportunityStage,
    InboxAction,
    AgingColor,
    FeedbackType,
    FilterPeriod,
    HealthStatus,
    EXPIRATION_RULES,
    AGING_THRESHOLDS,
    LROP_VERSION,
)
from packages.live_revenue_operations.inbox_engine import InboxEngine, InboxRecord
from packages.live_revenue_operations.opportunity_lifecycle import LifecycleManager, StageTransition
from packages.live_revenue_operations.pipeline_engine import PipelineEngine, PipelineCard
from packages.live_revenue_operations.pipeline_metrics import PipelineMetrics
from packages.live_revenue_operations.aging_engine import AgingEngine, AgingInfo
from packages.live_revenue_operations.expiration_engine import ExpirationEngine, ExpirationRule
from packages.live_revenue_operations.founder_workspace import FounderWorkspace
from packages.live_revenue_operations.review_engine import ReviewEngine, ReviewSession
from packages.live_revenue_operations.queue_engine import QueueEngine, QueueItem
from packages.live_revenue_operations.feed_engine import FeedEngine, FeedEvent
from packages.live_revenue_operations.connector_roi import ConnectorROI, ConnectorROITracker
from packages.live_revenue_operations.outreach_tracker import OutreachTracker, OutreachRecord
from packages.live_revenue_operations.reply_tracker import ReplyTracker, ReplyRecord
from packages.live_revenue_operations.meeting_tracker import MeetingTracker, MeetingRecord
from packages.live_revenue_operations.proposal_tracker import ProposalTracker, ProposalRecord
from packages.live_revenue_operations.revenue_tracker import RevenueTracker, RevenueRecord
from packages.live_revenue_operations.dashboard_service import DashboardService
from packages.live_revenue_operations.scheduler import Scheduler, ScheduledTask
from packages.live_revenue_operations.reports import ReportGenerator, Report
from packages.live_revenue_operations.analytics import Analytics


class TestEnums(unittest.TestCase):
    """Test enums and constants."""

    def test_opportunity_stages(self):
        self.assertEqual(OpportunityStage.NEW.value, "new")
        self.assertEqual(OpportunityStage.WON.value, "won")
        self.assertEqual(OpportunityStage.LOST.value, "lost")

    def test_expiration_rules(self):
        self.assertEqual(EXPIRATION_RULES["Hiring"], 30)
        self.assertEqual(EXPIRATION_RULES["Funding"], 90)

    def test_aging_thresholds(self):
        self.assertEqual(AGING_THRESHOLDS[AgingColor.GREEN], 7)
        self.assertEqual(AGING_THRESHOLDS[AgingColor.RED], 60)

    def test_version(self):
        self.assertEqual(LROP_VERSION, "lrop-v1")


class TestInboxEngine(unittest.TestCase):
    """Test InboxEngine."""

    def setUp(self):
        self.engine = InboxEngine()

    def test_add_opportunity(self):
        record = self.engine.add_opportunity(
            company_name="TestCo",
            website="https://testco.com",
            buying_signal="Hiring",
            evidence={"source": "LinkedIn"},
            connector="linkedin_jobs",
            quality_score=85,
            signal_age_days=5,
            why_now="Actively hiring",
        )
        self.assertEqual(record.company_name, "TestCo")
        self.assertEqual(record.status, "new")

    def test_approve(self):
        record = self.engine.add_opportunity(
            company_name="TestCo",
            website="https://testco.com",
            buying_signal="Hiring",
            evidence={},
            connector="linkedin_jobs",
            quality_score=85,
            signal_age_days=5,
            why_now="Hiring",
        )
        approved = self.engine.approve(record.id)
        self.assertIsNotNone(approved)
        self.assertEqual(approved.status, "approved")

    def test_reject(self):
        record = self.engine.add_opportunity(
            company_name="BadCo",
            website="https://badco.com",
            buying_signal="Blog posts",
            evidence={},
            connector="reddit",
            quality_score=40,
            signal_age_days=100,
            why_now="Blog post",
        )
        rejected = self.engine.reject(record.id)
        self.assertIsNotNone(rejected)
        self.assertEqual(rejected.status, "archived")

    def test_get_statistics(self):
        self.engine.add_opportunity(
            company_name="TestCo",
            website="https://testco.com",
            buying_signal="Hiring",
            evidence={},
            connector="linkedin_jobs",
            quality_score=85,
            signal_age_days=5,
            why_now="Hiring",
        )
        stats = self.engine.get_statistics()
        self.assertEqual(stats["total"], 1)


class TestLifecycleManager(unittest.TestCase):
    """Test LifecycleManager."""

    def setUp(self):
        self.manager = LifecycleManager()

    def test_transition(self):
        transition = self.manager.transition(
            opportunity_id="opp-1",
            to_stage=OpportunityStage.REVIEW.value,
        )
        self.assertIsNotNone(transition)
        self.assertEqual(transition.to_stage, "review")

    def test_invalid_transition(self):
        transition = self.manager.transition(
            opportunity_id="opp-1",
            to_stage=OpportunityStage.WON.value,  # Can't go directly to WON
        )
        self.assertIsNone(transition)

    def test_valid_next_stages(self):
        stages = self.manager.get_valid_next_stages("opp-1")
        self.assertIn(OpportunityStage.REVIEW.value, stages)
        self.assertIn(OpportunityStage.APPROVED.value, stages)


class TestPipelineEngine(unittest.TestCase):
    """Test PipelineEngine."""

    def setUp(self):
        self.engine = PipelineEngine()

    def test_add_card(self):
        card = self.engine.add_card(
            opportunity_id="opp-1",
            company_name="TestCo",
            website="https://testco.com",
            buying_signal="Hiring",
            connector="linkedin_jobs",
            quality_score=85,
        )
        self.assertEqual(card.company_name, "TestCo")
        self.assertEqual(card.stage, "new")

    def test_move_card(self):
        card = self.engine.add_card(
            opportunity_id="opp-1",
            company_name="TestCo",
            website="https://testco.com",
            buying_signal="Hiring",
            connector="linkedin_jobs",
            quality_score=85,
        )
        moved = self.engine.move_card(card.id, "approved")
        self.assertIsNotNone(moved)
        self.assertEqual(moved.stage, "approved")

    def test_get_stage_column(self):
        self.engine.add_card(
            opportunity_id="opp-1",
            company_name="TestCo",
            website="https://testco.com",
            buying_signal="Hiring",
            connector="linkedin_jobs",
            quality_score=85,
        )
        column = self.engine.get_stage_column("new")
        self.assertEqual(len(column), 1)


class TestPipelineMetrics(unittest.TestCase):
    """Test PipelineMetrics."""

    def setUp(self):
        self.metrics = PipelineMetrics()

    def test_calculate_velocity(self):
        velocity = self.metrics.calculate_velocity([])
        self.assertEqual(velocity["velocity"], 0)

    def test_calculate_pipeline_health(self):
        health = self.metrics.calculate_pipeline_health([])
        self.assertEqual(health["health_score"], 0)


class TestAgingEngine(unittest.TestCase):
    """Test AgingEngine."""

    def setUp(self):
        self.engine = AgingEngine()

    def test_track_opportunity(self):
        info = self.engine.track_opportunity(
            opportunity_id="opp-1",
            created_at=datetime.now(timezone.utc) - timedelta(days=5),
            signal_type="Hiring",
        )
        self.assertIsNotNone(info)

    def test_get_aging(self):
        self.engine.track_opportunity(
            opportunity_id="opp-1",
            created_at=datetime.now(timezone.utc) - timedelta(days=5),
            signal_type="Hiring",
        )
        info = self.engine.get_aging("opp-1")
        self.assertIsNotNone(info)


class TestExpirationEngine(unittest.TestCase):
    """TestExpirationEngine."""

    def setUp(self):
        self.engine = ExpirationEngine()

    def test_is_expired(self):
        expired = self.engine.is_expired(
            created_at=datetime.now(timezone.utc) - timedelta(days=40),
            signal_type="Hiring",
        )
        self.assertTrue(expired)

    def test_not_expired(self):
        expired = self.engine.is_expired(
            created_at=datetime.now(timezone.utc) - timedelta(days=10),
            signal_type="Hiring",
        )
        self.assertFalse(expired)

    def test_get_rule(self):
        rule = self.engine.get_rule("Hiring")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.days, 30)


class TestFounderWorkspace(unittest.TestCase):
    """Test FounderWorkspace."""

    def setUp(self):
        self.workspace = FounderWorkspace()

    def test_get_todays_view(self):
        view = self.workspace.get_todays_view()
        self.assertIn("date", view)
        self.assertIn("opportunities", view)


class TestReviewEngine(unittest.TestCase):
    """Test ReviewEngine."""

    def setUp(self):
        self.engine = ReviewEngine()

    def test_start_review(self):
        session = self.engine.start_review("opp-1")
        self.assertIsNotNone(session)
        self.assertEqual(session.opportunity_id, "opp-1")

    def test_complete_review(self):
        session = self.engine.start_review("opp-1")
        completed = self.engine.complete_review(session.id, "approve", "Good company")
        self.assertIsNotNone(completed)
        self.assertEqual(completed.decision, "approve")


class TestQueueEngine(unittest.TestCase):
    """Test QueueEngine."""

    def setUp(self):
        self.engine = QueueEngine()

    def test_enqueue(self):
        item = self.engine.enqueue(
            opportunity_id="opp-1",
            company_name="TestCo",
            quality_score=85,
            signal_type="Hiring",
            connector="linkedin_jobs",
        )
        self.assertIsNotNone(item)

    def test_dequeue(self):
        self.engine.enqueue(
            opportunity_id="opp-1",
            company_name="TestCo",
            quality_score=85,
            signal_type="Hiring",
            connector="linkedin_jobs",
        )
        item = self.engine.dequeue()
        self.assertIsNotNone(item)


class TestFeedEngine(unittest.TestCase):
    """Test FeedEngine."""

    def setUp(self):
        self.engine = FeedEngine()

    def test_add_event(self):
        event = self.engine.add_event(
            event_type="signal_detected",
            source="linkedin_jobs",
            connector="linkedin_jobs",
            company_name="TestCo",
            buying_signal="Hiring",
            stage="new",
            status="detected",
        )
        self.assertIsNotNone(event)

    def test_get_latest(self):
        self.engine.add_event(
            event_type="signal_detected",
            source="linkedin_jobs",
            connector="linkedin_jobs",
            company_name="TestCo",
            buying_signal="Hiring",
            stage="new",
            status="detected",
        )
        events = self.engine.get_latest(1)
        self.assertEqual(len(events), 1)


class TestConnectorROI(unittest.TestCase):
    """Test ConnectorROI."""

    def test_get_acceptance_rate(self):
        roi = ConnectorROI("linkedin_jobs")
        roi.signals = 100
        roi.accepted = 30
        self.assertEqual(roi.get_acceptance_rate(), 0.3)

    def test_get_recommendation(self):
        roi = ConnectorROI("linkedin_jobs")
        roi.signals = 100
        roi.accepted = 30
        roi.contacted = 20
        roi.meetings = 5
        self.assertEqual(roi.get_recommendation(), "Keep")


class TestConnectorROITracker(unittest.TestCase):
    """Test ConnectorROITracker."""

    def setUp(self):
        self.tracker = ConnectorROITracker()

    def test_record_signal(self):
        self.tracker.record_signal("linkedin_jobs")
        roi = self.tracker.get_connector("linkedin_jobs")
        self.assertIsNotNone(roi)
        self.assertEqual(roi.signals, 1)


class TestOutreachTracker(unittest.TestCase):
    """Test OutreachTracker."""

    def setUp(self):
        self.tracker = OutreachTracker()

    def test_record_outreach(self):
        record = self.tracker.record_outreach(
            opportunity_id="opp-1",
            company_name="TestCo",
            contact_email="test@testco.com",
        )
        self.assertIsNotNone(record)

    def test_mark_replied(self):
        record = self.tracker.record_outreach(
            opportunity_id="opp-1",
            company_name="TestCo",
            contact_email="test@testco.com",
        )
        self.tracker.mark_replied(record.id)
        self.assertEqual(record.status, "replied")


class TestReplyTracker(unittest.TestCase):
    """Test ReplyTracker."""

    def setUp(self):
        self.tracker = ReplyTracker()

    def test_record_reply(self):
        record = self.tracker.record_reply(
            opportunity_id="opp-1",
            outreach_id="out-1",
            company_name="TestCo",
            contact_email="test@testco.com",
            sentiment="positive",
        )
        self.assertIsNotNone(record)


class TestMeetingTracker(unittest.TestCase):
    """Test MeetingTracker."""

    def setUp(self):
        self.tracker = MeetingTracker()

    def test_record_meeting(self):
        record = self.tracker.record_meeting(
            opportunity_id="opp-1",
            company_name="TestCo",
            contact_email="test@testco.com",
        )
        self.assertIsNotNone(record)

    def test_mark_completed(self):
        record = self.tracker.record_meeting(
            opportunity_id="opp-1",
            company_name="TestCo",
            contact_email="test@testco.com",
        )
        self.tracker.mark_completed(record.id, "interested")
        self.assertEqual(record.status, "completed")


class TestProposalTracker(unittest.TestCase):
    """Test ProposalTracker."""

    def setUp(self):
        self.tracker = ProposalTracker()

    def test_record_proposal(self):
        record = self.tracker.record_proposal(
            opportunity_id="opp-1",
            company_name="TestCo",
            amount=5000.0,
        )
        self.assertIsNotNone(record)

    def test_mark_accepted(self):
        record = self.tracker.record_proposal(
            opportunity_id="opp-1",
            company_name="TestCo",
            amount=5000.0,
        )
        self.tracker.mark_accepted(record.id)
        self.assertEqual(record.status, "accepted")


class TestRevenueTracker(unittest.TestCase):
    """Test RevenueTracker."""

    def setUp(self):
        self.tracker = RevenueTracker()

    def test_record_revenue(self):
        record = self.tracker.record_revenue(
            opportunity_id="opp-1",
            company_name="TestCo",
            amount=5000.0,
        )
        self.assertIsNotNone(record)

    def test_mark_closed(self):
        record = self.tracker.record_revenue(
            opportunity_id="opp-1",
            company_name="TestCo",
            amount=5000.0,
        )
        self.tracker.mark_closed(record.id)
        self.assertEqual(record.status, "closed")


class TestDashboardService(unittest.TestCase):
    """Test DashboardService."""

    def setUp(self):
        self.service = DashboardService()

    def test_get_top_cards(self):
        cards = self.service.get_top_cards()
        self.assertIn("signals_today", cards)
        self.assertIn("accepted_today", cards)


class TestScheduler(unittest.TestCase):
    """Test Scheduler."""

    def setUp(self):
        self.scheduler = Scheduler()

    def test_add_task(self):
        task = self.scheduler.add_task("daily_cleanup", "daily")
        self.assertIsNotNone(task)

    def test_run_task(self):
        task = self.scheduler.add_task("test_task", "hourly")
        result = self.scheduler.run_task(task.id)
        self.assertEqual(result["status"], "completed")


class TestReportGenerator(unittest.TestCase):
    """Test ReportGenerator."""

    def setUp(self):
        self.generator = ReportGenerator()

    def test_generate_daily_summary(self):
        report = self.generator.generate_daily_summary({}, {}, {}, {})
        self.assertIsNotNone(report)
        self.assertEqual(report.report_type, "daily_summary")


class TestAnalytics(unittest.TestCase):
    """Test Analytics."""

    def setUp(self):
        self.analytics = Analytics()

    def test_analyze_pipeline(self):
        result = self.analytics.analyze_pipeline([])
        self.assertEqual(result["total"], 0)

    def test_analyze_connectors(self):
        result = self.analytics.analyze_connectors([])
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
