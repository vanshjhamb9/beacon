"""LOVP v1 tests — comprehensive tests for all validation components."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone, timedelta

from packages.opportunity_validation.v1_schemas import (
    OpportunityMetadata,
    TimelineEvent,
    ValidationOutcome,
    AuditEntry,
    ReviewDecision,
    StalenessStatus,
    SignalOrigin,
)
from packages.opportunity_validation.validator import OpportunityValidator
from packages.opportunity_validation.audit_engine import AuditEngine
from packages.opportunity_validation.signal_trace import SignalTrace
from packages.opportunity_validation.company_trace import CompanyTrace
from packages.opportunity_validation.connector_trace import ConnectorTrace
from packages.opportunity_validation.timeline_builder import TimelineBuilder
from packages.opportunity_validation.buying_reason import BuyingReasonEngine
from packages.opportunity_validation.staleness_detector import StalenessDetector
from packages.opportunity_validation.human_review import HumanReviewEngine
from packages.opportunity_validation.validation_dashboard import ValidationDashboard
from packages.opportunity_validation.validation_metrics import ValidationMetrics
from packages.opportunity_validation.validation_reports import ValidationReports
from packages.opportunity_validation.validation_scheduler import ValidationScheduler
from packages.opportunity_validation.opportunity_explainer import OpportunityExplainer
from packages.opportunity_validation.replay_engine import ReplayEngine
from packages.opportunity_validation.root_cause import RootCauseEngine


class TestV1Schemas(unittest.TestCase):
    """Test v1 schemas."""

    def test_opportunity_metadata_defaults(self):
        m = OpportunityMetadata({})
        self.assertEqual(m.opportunity_id, "unknown")
        self.assertEqual(m.company_name, "unknown")
        self.assertEqual(m.website, "unknown")

    def test_opportunity_metadata_to_dict(self):
        m = OpportunityMetadata({"company_name": "TestCo"})
        d = m.to_dict()
        self.assertEqual(d["company_name"], "TestCo")
        self.assertIn("opportunity_id", d)

    def test_timeline_event(self):
        e = TimelineEvent({"event_type": "signal", "description": "Test"})
        d = e.to_dict()
        self.assertEqual(d["event_type"], "signal")

    def test_validation_outcome(self):
        v = ValidationOutcome({"decision": "approve", "reasons": []})
        self.assertEqual(v.decision, "approve")

    def test_audit_entry(self):
        a = AuditEntry({"gate": "test", "decision": "pass"})
        self.assertEqual(a.gate, "test")


class TestOpportunityValidator(unittest.TestCase):
    """Test OpportunityValidator."""

    def setUp(self):
        self.validator = OpportunityValidator()

    def test_approve_valid_opportunity(self):
        m = OpportunityMetadata({
            "opportunity_id": "opp-1",
            "company_name": "GoodCo",
            "website": "https://goodco.com",
            "buying_signal": "Hiring",
            "signal_type": "hiring",
            "signal_age_days": 10,
            "quality_score": 90,
            "confidence": 0.8,
            "icp_match": True,
            "region_match": True,
            "industry_match": True,
        })
        outcome = self.validator.validate(m)
        self.assertEqual(outcome.decision, ReviewDecision.APPROVE.value)

    def test_reject_unknown_company(self):
        m = OpportunityMetadata({"company_name": ""})
        outcome = self.validator.validate(m)
        self.assertEqual(outcome.decision, ReviewDecision.REJECT.value)

    def test_reject_ai_company(self):
        m = OpportunityMetadata({
            "company_name": "OpenAI GPT Corp",
            "website": "https://openai-gpt.com",
            "buying_signal": "Hiring",
            "signal_type": "hiring",
            "signal_age_days": 10,
            "quality_score": 90,
            "confidence": 0.8,
            "icp_match": True,
            "region_match": True,
            "industry_match": True,
        })
        outcome = self.validator.validate(m)
        self.assertEqual(outcome.decision, ReviewDecision.REJECT.value)

    def test_reject_stale_signal(self):
        m = OpportunityMetadata({
            "company_name": "OldCo",
            "website": "https://oldco.com",
            "buying_signal": "Hiring",
            "signal_type": "hiring",
            "signal_age_days": 200,
            "quality_score": 90,
            "confidence": 0.8,
            "icp_match": True,
            "region_match": True,
            "industry_match": True,
        })
        outcome = self.validator.validate(m)
        self.assertEqual(outcome.decision, ReviewDecision.REJECT.value)

    def test_reject_low_quality(self):
        m = OpportunityMetadata({
            "company_name": "LowQCo",
            "website": "https://lowqco.com",
            "buying_signal": "Hiring",
            "signal_type": "hiring",
            "signal_age_days": 10,
            "quality_score": 50,
            "confidence": 0.8,
            "icp_match": True,
            "region_match": True,
            "industry_match": True,
        })
        outcome = self.validator.validate(m)
        self.assertEqual(outcome.decision, ReviewDecision.REJECT.value)

    def test_reject_invalid_buying_signal(self):
        m = OpportunityMetadata({
            "company_name": "BlogCo",
            "website": "https://blogco.com",
            "buying_signal": "Blog posts",
            "signal_type": "blog",
            "signal_age_days": 10,
            "quality_score": 90,
            "confidence": 0.8,
            "icp_match": True,
            "region_match": True,
            "industry_match": True,
        })
        outcome = self.validator.validate(m)
        self.assertEqual(outcome.decision, ReviewDecision.REJECT.value)


class TestAuditEngine(unittest.TestCase):
    """Test AuditEngine."""

    def setUp(self):
        self.engine = AuditEngine()

    def test_record_gate(self):
        entry = self.engine.record_gate(
            opportunity_id="opp-1",
            gate="test_gate",
            decision="pass",
            reasons=[],
            evidence={},
        )
        self.assertEqual(entry.gate, "test_gate")

    def test_get_audit_trail(self):
        self.engine.record_gate("opp-1", "gate1", "pass", [], {})
        self.engine.record_gate("opp-1", "gate2", "fail", ["reason"], {})
        trail = self.engine.get_audit_trail("opp-1")
        self.assertEqual(len(trail), 2)

    def test_get_statistics(self):
        self.engine.record_gate("opp-1", "gate1", "pass", [], {})
        stats = self.engine.get_statistics()
        self.assertEqual(stats["total_entries"], 1)


class TestSignalTrace(unittest.TestCase):
    """Test SignalTrace."""

    def setUp(self):
        self.trace = SignalTrace()

    def test_record_signal(self):
        result = self.trace.record_signal(
            opportunity_id="opp-1",
            signal_type="hiring",
            signal_source="linkedin",
            connector="linkedin_jobs",
            original_url="https://linkedin.com/123",
            original_timestamp=datetime.now(timezone.utc),
            collection_timestamp=datetime.now(timezone.utc),
            evidence={},
        )
        self.assertIn("trace_id", result)

    def test_get_trace(self):
        self.trace.record_signal(
            opportunity_id="opp-1",
            signal_type="hiring",
            signal_source="linkedin",
            connector="linkedin_jobs",
            original_url="https://linkedin.com/123",
            original_timestamp=datetime.now(timezone.utc),
            collection_timestamp=datetime.now(timezone.utc),
            evidence={},
        )
        traces = self.trace.get_trace("opp-1")
        self.assertEqual(len(traces), 1)

    def test_get_statistics(self):
        self.trace.record_signal(
            opportunity_id="opp-1",
            signal_type="hiring",
            signal_source="linkedin",
            connector="linkedin_jobs",
            original_url="https://linkedin.com/123",
            original_timestamp=datetime.now(timezone.utc),
            collection_timestamp=datetime.now(timezone.utc),
            evidence={},
        )
        stats = self.trace.get_statistics()
        self.assertEqual(stats["total_traces"], 1)


class TestCompanyTrace(unittest.TestCase):
    """Test CompanyTrace."""

    def setUp(self):
        self.trace = CompanyTrace()

    def test_record_company(self):
        result = self.trace.record_company(
            company_id="comp-1",
            company_name="TestCo",
            website="https://testco.com",
            industry="Technology",
            country="US",
            discovery_source="linkedin",
            discovery_connector="linkedin_jobs",
            discovery_timestamp=datetime.now(timezone.utc),
            first_evidence_url="https://linkedin.com/123",
        )
        self.assertEqual(result["company_id"], "comp-1")

    def test_add_validation_event(self):
        self.trace.record_company(
            company_id="comp-1",
            company_name="TestCo",
            website="https://testco.com",
            industry="Technology",
            country="US",
            discovery_source="linkedin",
            discovery_connector="linkedin_jobs",
            discovery_timestamp=datetime.now(timezone.utc),
            first_evidence_url="https://linkedin.com/123",
        )
        event = self.trace.add_validation_event(
            company_id="comp-1",
            event_type="validation",
            decision="approve",
            reasons=[],
            evidence={},
        )
        self.assertEqual(event["decision"], "approve")

    def test_get_statistics(self):
        self.trace.record_company(
            company_id="comp-1",
            company_name="TestCo",
            website="https://testco.com",
            industry="Technology",
            country="US",
            discovery_source="linkedin",
            discovery_connector="linkedin_jobs",
            discovery_timestamp=datetime.now(timezone.utc),
            first_evidence_url="https://linkedin.com/123",
        )
        stats = self.trace.get_statistics()
        self.assertEqual(stats["total_companies"], 1)


class TestConnectorTrace(unittest.TestCase):
    """Test ConnectorTrace."""

    def setUp(self):
        self.trace = ConnectorTrace()

    def test_record_connector_event(self):
        result = self.trace.record_connector_event(
            connector_name="linkedin_jobs",
            opportunity_id="opp-1",
            company_name="TestCo",
            signal_type="hiring",
            signal_quality="high",
            validation_decision="approve",
            evidence={},
        )
        self.assertIn("trace_id", result)

    def test_get_connector_stats(self):
        self.trace.record_connector_event(
            connector_name="linkedin_jobs",
            opportunity_id="opp-1",
            company_name="TestCo",
            signal_type="hiring",
            signal_quality="high",
            validation_decision="approve",
            evidence={},
        )
        stats = self.trace.get_connector_stats("linkedin_jobs")
        self.assertEqual(stats["total_signals"], 1)

    def test_get_best_connector(self):
        self.trace.record_connector_event(
            connector_name="linkedin_jobs",
            opportunity_id="opp-1",
            company_name="TestCo",
            signal_type="hiring",
            signal_quality="high",
            validation_decision="approve",
            evidence={},
        )
        self.assertEqual(self.trace.get_best_connector(), "linkedin_jobs")


class TestTimelineBuilder(unittest.TestCase):
    """Test TimelineBuilder."""

    def setUp(self):
        self.builder = TimelineBuilder()

    def test_add_event(self):
        result = self.builder.add_event(
            opportunity_id="opp-1",
            event_type="signal",
            description="Test signal",
            source="linkedin",
            connector="linkedin_jobs",
        )
        self.assertEqual(result["event_type"], "signal")

    def test_get_timeline(self):
        self.builder.add_event(
            opportunity_id="opp-1",
            event_type="signal",
            description="Test signal",
            source="linkedin",
            connector="linkedin_jobs",
        )
        timeline = self.builder.get_timeline("opp-1")
        self.assertEqual(len(timeline), 1)

    def test_get_timeline_length(self):
        self.builder.add_event(
            opportunity_id="opp-1",
            event_type="signal",
            description="Test signal",
            source="linkedin",
            connector="linkedin_jobs",
        )
        self.assertEqual(self.builder.get_timeline_length("opp-1"), 1)

    def test_has_timeline(self):
        self.assertFalse(self.builder.has_timeline("opp-1"))
        self.builder.add_event(
            opportunity_id="opp-1",
            event_type="signal",
            description="Test signal",
            source="linkedin",
            connector="linkedin_jobs",
        )
        self.assertTrue(self.builder.has_timeline("opp-1"))


class TestBuyingReasonEngine(unittest.TestCase):
    """Test BuyingReasonEngine."""

    def setUp(self):
        self.engine = BuyingReasonEngine()

    def test_determine_reason_strong_signal(self):
        result = self.engine.determine_reason(
            signal_type="Hiring",
            signal_age_days=5,
            company_industry="Technology",
            company_country="US",
            evidence={},
        )
        self.assertTrue(result["strong_signal"])
        self.assertGreater(result["confidence"], 0.5)

    def test_determine_reason_weak_signal(self):
        result = self.engine.determine_reason(
            signal_type="Blog posts",
            signal_age_days=5,
            company_industry="Technology",
            company_country="US",
            evidence={},
        )
        self.assertFalse(result["strong_signal"])
        self.assertLess(result["confidence"], 0.5)

    def test_would_sdr_contact_yes(self):
        result = self.engine.would_sdr_contact(
            signal_type="Hiring",
            signal_age_days=5,
            quality_score=90,
            confidence=0.9,
            icp_match=True,
        )
        self.assertTrue(result["would_contact"])
        self.assertEqual(result["verdict"], "YES")

    def test_would_sdr_contact_no(self):
        result = self.engine.would_sdr_contact(
            signal_type="Blog posts",
            signal_age_days=180,
            quality_score=40,
            confidence=0.2,
            icp_match=False,
        )
        self.assertFalse(result["would_contact"])
        self.assertEqual(result["verdict"], "NO")


class TestStalenessDetector(unittest.TestCase):
    """Test StalenessDetector."""

    def setUp(self):
        self.detector = StalenessDetector()

    def test_detect_fresh(self):
        result = self.detector.detect_from_age(10)
        self.assertEqual(result["status"], StalenessStatus.FRESH.value)

    def test_detect_aging(self):
        result = self.detector.detect_from_age(60)
        self.assertEqual(result["status"], StalenessStatus.AGING.value)

    def test_detect_stale(self):
        result = self.detector.detect_from_age(100)
        self.assertEqual(result["status"], StalenessStatus.STALE.value)

    def test_detect_ancient(self):
        result = self.detector.detect_from_age(200)
        self.assertEqual(result["status"], StalenessStatus.ANCIENT.value)

    def test_should_reject(self):
        self.assertFalse(self.detector.should_reject(10))
        self.assertTrue(self.detector.should_reject(150))

    def test_should_hold(self):
        self.assertFalse(self.detector.should_hold(10))
        self.assertTrue(self.detector.should_hold(60))
        self.assertFalse(self.detector.should_hold(150))

    def test_get_score_multiplier(self):
        self.assertEqual(self.detector.get_score_multiplier(10), 1.0)
        self.assertEqual(self.detector.get_score_multiplier(60), 0.8)
        self.assertEqual(self.detector.get_score_multiplier(100), 0.5)
        self.assertEqual(self.detector.get_score_multiplier(200), 0.2)


class TestHumanReviewEngine(unittest.TestCase):
    """Test HumanReviewEngine."""

    def setUp(self):
        self.engine = HumanReviewEngine()

    def test_add_review(self):
        result = self.engine.add_review(
            opportunity_id="opp-1",
            decision="approve",
            reviewer="admin",
            reasons=["Good company"],
        )
        self.assertEqual(result["decision"], "approve")

    def test_approve(self):
        result = self.engine.approve(
            opportunity_id="opp-1",
            reviewer="admin",
            reasons=["Good fit"],
        )
        self.assertEqual(result["decision"], "approve")

    def test_reject(self):
        result = self.engine.reject(
            opportunity_id="opp-1",
            reviewer="admin",
            reasons=["Bad fit"],
        )
        self.assertEqual(result["decision"], "reject")

    def test_get_statistics(self):
        self.engine.approve("opp-1", "admin", ["Good fit"])
        self.engine.reject("opp-2", "admin", ["Bad fit"])
        stats = self.engine.get_statistics()
        self.assertEqual(stats["total_reviews"], 2)


class TestValidationDashboard(unittest.TestCase):
    """Test ValidationDashboard."""

    def setUp(self):
        self.dashboard = ValidationDashboard()

    def test_collect_metrics(self):
        metrics = self.dashboard.collect_metrics(
            opportunities=[
                {"company_name": "TestCo", "signal_age_days": 10, "collection_timestamp": datetime.now(timezone.utc).isoformat()},
            ],
            validation_results=[
                {"decision": "approve", "reasons": []},
            ],
            timeline_stats={"avg_events_per_timeline": 1.0},
            connector_stats={"connector_rates": {}},
        )
        self.assertEqual(metrics["accepted"], 1)
        self.assertEqual(metrics["rejected"], 0)


class TestValidationMetrics(unittest.TestCase):
    """Test ValidationMetrics."""

    def setUp(self):
        self.metrics = ValidationMetrics()

    def test_record_validation(self):
        self.metrics.record_validation(
            opportunity_id="opp-1",
            decision="approve",
            connector="linkedin_jobs",
            signal_type="hiring",
            industry="Technology",
            region="US",
            quality_score=90,
            signal_age_days=10,
            confidence=0.8,
        )
        self.assertEqual(self.metrics.get_metrics()["total_validated"], 1)

    def test_get_acceptance_rate(self):
        self.metrics.record_validation(
            opportunity_id="opp-1",
            decision="approve",
            connector="linkedin_jobs",
            signal_type="hiring",
            industry="Technology",
            region="US",
            quality_score=90,
            signal_age_days=10,
            confidence=0.8,
        )
        self.assertEqual(self.metrics.get_acceptance_rate(), 1.0)

    def test_get_top_connector(self):
        self.metrics.record_validation(
            opportunity_id="opp-1",
            decision="approve",
            connector="linkedin_jobs",
            signal_type="hiring",
            industry="Technology",
            region="US",
            quality_score=90,
            signal_age_days=10,
            confidence=0.8,
        )
        self.assertEqual(self.metrics.get_top_connector(), "linkedin_jobs")


class TestValidationReports(unittest.TestCase):
    """Test ValidationReports."""

    def setUp(self):
        self.reports = ValidationReports()

    def test_generate_report(self):
        report = self.reports.generate_report(
            opportunity_id="opp-1",
            company_name="TestCo",
            validation_outcome={"decision": "approve", "reasons": []},
            timeline=[],
            signal_trace=None,
            company_trace=None,
            connector_trace=None,
            staleness={"status": "fresh"},
            buying_reason={"why_now": "Hiring signal"},
            human_review=None,
        )
        self.assertEqual(report["company_name"], "TestCo")

    def test_get_report(self):
        self.reports.generate_report(
            opportunity_id="opp-1",
            company_name="TestCo",
            validation_outcome={"decision": "approve", "reasons": []},
            timeline=[],
            signal_trace=None,
            company_trace=None,
            connector_trace=None,
            staleness={"status": "fresh"},
            buying_reason={"why_now": "Hiring signal"},
            human_review=None,
        )
        report = self.reports.get_report("opp-1")
        self.assertIsNotNone(report)


class TestValidationScheduler(unittest.TestCase):
    """Test ValidationScheduler."""

    def setUp(self):
        self.scheduler = ValidationScheduler()

    def test_schedule_validation(self):
        result = self.scheduler.schedule_validation(
            schedule_id="sched-1",
            frequency="daily",
            opportunity_ids=["opp-1", "opp-2"],
        )
        self.assertEqual(result["schedule_id"], "sched-1")

    def test_run_schedule(self):
        self.scheduler.schedule_validation(
            schedule_id="sched-1",
            frequency="daily",
            opportunity_ids=["opp-1"],
        )
        result = self.scheduler.run_schedule("sched-1")
        self.assertEqual(result["status"], "completed")

    def test_get_statistics(self):
        self.scheduler.schedule_validation(
            schedule_id="sched-1",
            frequency="daily",
            opportunity_ids=["opp-1"],
        )
        stats = self.scheduler.get_statistics()
        self.assertEqual(stats["total_schedules"], 1)


class TestOpportunityExplainer(unittest.TestCase):
    """Test OpportunityExplainer."""

    def setUp(self):
        self.explainer = OpportunityExplainer()

    def test_explain(self):
        explanation = self.explainer.explain(
            opportunity_id="opp-1",
            company_name="TestCo",
            website="https://testco.com",
            connector="linkedin_jobs",
            evidence={"source": "LinkedIn"},
            detection_timestamp=datetime.now(timezone.utc),
            freshness="fresh",
            buying_signal="Hiring",
            buying_signal_strength="strong",
            icp_match=True,
            icp_score=0.9,
            quality_score=90,
            timeline_events=[],
            why_now="Actively hiring",
            validation_decision="approve",
        )
        self.assertEqual(explanation["company_name"], "TestCo")
        self.assertIn("why_am_i_seeing_this", explanation)

    def test_get_card_data(self):
        card = self.explainer.get_card_data(
            opportunity_id="opp-1",
            company_name="TestCo",
            website="https://testco.com",
            connector="linkedin_jobs",
            evidence={},
            detection_timestamp=datetime.now(timezone.utc),
            freshness="fresh",
            buying_signal="Hiring",
            icp_match=True,
            quality_score=90,
        )
        self.assertEqual(card["title"], "TestCo")


class TestReplayEngine(unittest.TestCase):
    """Test ReplayEngine."""

    def setUp(self):
        self.engine = ReplayEngine()

    def test_replay_opportunity(self):
        replay = self.engine.replay_opportunity(
            opportunity_id="opp-1",
            company_name="TestCo",
            connector_data={"connector": "linkedin_jobs"},
            dqe_data={"quality_score": 90},
            validation_data={"decision": "approve"},
        )
        self.assertEqual(replay["company_name"], "TestCo")
        self.assertIn("stages", replay)

    def test_get_replay(self):
        self.engine.replay_opportunity(
            opportunity_id="opp-1",
            company_name="TestCo",
            connector_data={},
            dqe_data={},
            validation_data={},
        )
        replay = self.engine.get_replay("opp-1")
        self.assertIsNotNone(replay)

    def test_get_statistics(self):
        self.engine.replay_opportunity(
            opportunity_id="opp-1",
            company_name="TestCo",
            connector_data={},
            dqe_data={},
            validation_data={"decision": "approve"},
        )
        stats = self.engine.get_statistics()
        self.assertEqual(stats["total_replays"], 1)


class TestRootCauseEngine(unittest.TestCase):
    """Test RootCauseEngine."""

    def setUp(self):
        self.engine = RootCauseEngine()

    def test_determine_root_cause_approve(self):
        result = self.engine.determine_root_cause(
            validation_decision="approve",
            reasons=[],
            evidence={},
        )
        self.assertEqual(result["root_cause"], "passes_all_gates")

    def test_determine_root_cause_no_buying_signal(self):
        result = self.engine.determine_root_cause(
            validation_decision="reject",
            reasons=["No buying signal"],
            evidence={},
        )
        self.assertEqual(result["root_cause"], "no_buying_signal")

    def test_determine_root_cause_stale(self):
        result = self.engine.determine_root_cause(
            validation_decision="reject",
            reasons=["Signal too old: 200 days"],
            evidence={},
        )
        self.assertEqual(result["root_cause"], "stale_signal")

    def test_determine_root_cause_ai(self):
        result = self.engine.determine_root_cause(
            validation_decision="reject",
            reasons=["AI company detected"],
            evidence={},
        )
        self.assertEqual(result["root_cause"], "ai_company")

    def test_get_all_root_causes(self):
        causes = self.engine.get_all_root_causes()
        self.assertIn("no_buying_signal", causes)
        self.assertIn("stale_signal", causes)

    def test_get_statistics(self):
        stats = self.engine.get_statistics()
        self.assertGreater(stats["total_root_causes"], 0)


if __name__ == "__main__":
    unittest.main()
