"""BOLR v1 tests — comprehensive tests for all observatory components."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone, timedelta

from packages.beacon_observatory import (
    CollectorStatus,
    PipelineStage,
    AlertSeverity,
    DataType,
    REJECTION_CATEGORIES,
    DEMO_KEYWORDS,
    BOLR_VERSION,
)
from packages.beacon_observatory.runtime_engine import RuntimeEngine, CollectorRuntimeInfo
from packages.beacon_observatory.collector_runtime import CollectorRuntime
from packages.beacon_observatory.scheduler_monitor import SchedulerMonitor
from packages.beacon_observatory.worker_runtime import WorkerRuntime
from packages.beacon_observatory.event_stream import EventStream
from packages.beacon_observatory.pipeline_trace import PipelineTrace
from packages.beacon_observatory.evidence_explorer import EvidenceExplorer
from packages.beacon_observatory.rejection_explorer import RejectionExplorer
from packages.beacon_observatory.connector_runtime import ConnectorRuntime
from packages.beacon_observatory.runtime_metrics import RuntimeMetrics
from packages.beacon_observatory.latency_engine import LatencyEngine
from packages.beacon_observatory.bottleneck_engine import BottleneckEngine
from packages.beacon_observatory.replay_engine import ReplayEngine
from packages.beacon_observatory.timeline_engine import TimelineEngine
from packages.beacon_observatory.verification_engine import VerificationEngine
from packages.beacon_observatory.dashboard_service import DashboardService
from packages.beacon_observatory.reports import Reports
from packages.beacon_observatory.alerts import Alerting


class TestEnums(unittest.TestCase):
    def test_collector_status(self):
        self.assertEqual(CollectorStatus.RUNNING.value, "running")
        self.assertEqual(CollectorStatus.FAILED.value, "failed")

    def test_pipeline_stage(self):
        self.assertEqual(PipelineStage.COLLECTED.value, "collected")
        self.assertEqual(PipelineStage.WON.value, "won")

    def test_alert_severity(self):
        self.assertEqual(AlertSeverity.CRITICAL.value, "critical")

    def test_data_type(self):
        self.assertEqual(DataType.LIVE.value, "live")
        self.assertEqual(DataType.CACHED.value, "cached")

    def test_rejection_categories(self):
        self.assertEqual(len(REJECTION_CATEGORIES), 10)
        self.assertIn("old_signal", REJECTION_CATEGORIES)
        self.assertIn("ai_company", REJECTION_CATEGORIES)

    def test_bolr_version(self):
        self.assertEqual(BOLR_VERSION, "bolr-v1")


class TestRuntimeEngine(unittest.TestCase):
    def test_record_collector(self):
        engine = RuntimeEngine()
        info = engine.register_collector("web_search", CollectorStatus.RUNNING.value)
        self.assertEqual(info.name, "web_search")
        self.assertEqual(info.status, CollectorStatus.RUNNING.value)

    def test_get_snapshot(self):
        engine = RuntimeEngine()
        engine.register_collector("a", CollectorStatus.RUNNING.value)
        engine.register_collector("b", CollectorStatus.RUNNING.value)
        engine.record_run("a", 60.0, 5, 4, 1, 2)
        engine.record_run("b", 90.0, 8, 6, 2, 3)
        stats = engine.get_statistics()
        self.assertEqual(stats["total_collectors"], 2)

    def test_to_dict(self):
        engine = RuntimeEngine()
        engine.register_collector("c", CollectorStatus.IDLE.value)
        collectors = engine.get_all_collectors()
        self.assertEqual(len(collectors), 1)
        self.assertEqual(collectors[0].name, "c")


class TestCollectorRuntime(unittest.TestCase):
    def test_record_run(self):
        rt = CollectorRuntime()
        run = rt.record_run("hackernews", 20, 18, 15, 5, 13, 10, 120.0)
        self.assertEqual(run.collector_name, "hackernews")
        self.assertEqual(run.signals_fetched, 20)

    def test_get_runs(self):
        rt = CollectorRuntime()
        rt.record_run("a", 10, 9, 8, 2, 7, 5, 60.0)
        rt.record_run("a", 15, 14, 12, 3, 10, 8, 90.0)
        runs = rt.get_runs("a")
        self.assertEqual(len(runs), 2)


class TestSchedulerMonitor(unittest.TestCase):
    def test_record_execution(self):
        sm = SchedulerMonitor()
        sm.register_worker("worker-github", "github", "hourly")
        sm.record_execution("worker-github", 30.0, True)
        entry = sm.get_entry("worker-github")
        self.assertEqual(entry.collector, "github")
        self.assertEqual(entry.status, "idle")

    def test_get_history(self):
        sm = SchedulerMonitor()
        sm.register_worker("w1", "a", "hourly")
        sm.record_execution("w1", 10.0, True)
        sm.record_execution("w1", 5.0, False)
        stats = sm.get_statistics()
        self.assertEqual(stats["total_executions"], 2)


class TestWorkerRuntime(unittest.TestCase):
    def test_record_worker(self):
        wr = WorkerRuntime()
        info = wr.register_worker("worker-1")
        self.assertEqual(info.name, "worker-1")
        wr.record_task("worker-1", 0.5, True)
        self.assertEqual(info.tasks_completed, 1)

    def test_get_workers(self):
        wr = WorkerRuntime()
        wr.register_worker("w1")
        wr.register_worker("w2")
        wr.record_task("w1", 0.3, True)
        wr.record_task("w2", 0.9, False)
        workers = wr.get_all_workers()
        self.assertEqual(len(workers), 2)


class TestEventStream(unittest.TestCase):
    def test_record_event(self):
        es = EventStream()
        event = es.add_event("hackernews", "new_signal", "New signal found")
        self.assertEqual(event.event_type, "new_signal")
        self.assertEqual(event.source, "hackernews")

    def test_get_events(self):
        es = EventStream()
        es.add_event("c1", "a", "desc1")
        es.add_event("c2", "b", "desc2")
        events = es.get_events()
        self.assertEqual(len(events), 2)

    def test_get_events_by_connector(self):
        es = EventStream()
        es.add_event("c1", "a", "desc1")
        es.add_event("c1", "b", "desc2")
        es.add_event("c2", "c", "desc3")
        events = es.get_events(source="c1")
        self.assertEqual(len(events), 2)


class TestPipelineTrace(unittest.TestCase):
    def test_record_step(self):
        pt = PipelineTrace()
        step = pt.add_step("opp-1", "collected", "entering collected stage")
        self.assertEqual(step.stage, "collected")

    def test_get_trace(self):
        pt = PipelineTrace()
        pt.add_step("opp-1", "collected", "entering")
        pt.add_step("opp-1", "validated", "entering")
        trace = pt.get_trace("opp-1")
        self.assertEqual(len(trace), 2)


class TestEvidenceExplorer(unittest.TestCase):
    def test_record_evidence(self):
        ee = EvidenceExplorer()
        rec = ee.add_evidence(
            "opp-1", "Acme Corp", "https://acme.com", "hackernews",
            "https://example.com/post/123", "hiring", 85, "accepted", "revenue_ready"
        )
        self.assertEqual(rec.opportunity_id, "opp-1")
        self.assertEqual(rec.company_name, "Acme Corp")

    def test_get_evidence(self):
        ee = EvidenceExplorer()
        ee.add_evidence("opp-1", "A", "https://a.com", "s", "https://e.com", "hiring", 80, "accepted", "revenue_ready")
        rec = ee.get_evidence("opp-1")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.opportunity_id, "opp-1")


class TestRejectionExplorer(unittest.TestCase):
    def test_record_rejection(self):
        re_ = RejectionExplorer()
        rec = re_.add_rejection("opp-1", "Acme Corp", "old_signal", "Signal is 200 days old", "hackernews", 200, 30)
        self.assertEqual(rec.opportunity_id, "opp-1")
        self.assertEqual(rec.rejection_category, "old_signal")

    def test_get_rejections(self):
        re_ = RejectionExplorer()
        re_.add_rejection("opp-1", "A", "a", "r", "s", 100, 30)
        re_.add_rejection("opp-2", "B", "b", "r", "s", 50, 40)
        rejections = re_.get_all_rejections()
        self.assertEqual(len(rejections), 2)

    def test_get_by_category(self):
        re_ = RejectionExplorer()
        re_.add_rejection("opp-1", "A", "old_signal", "r", "s", 100, 30)
        re_.add_rejection("opp-2", "B", "old_signal", "r", "s", 100, 30)
        re_.add_rejection("opp-3", "C", "ai_company", "r", "s", 10, 10)
        old = re_.get_by_category("old_signal")
        self.assertEqual(len(old), 2)


class TestConnectorRuntime(unittest.TestCase):
    def test_record_execution(self):
        cr = ConnectorRuntime()
        exec_ = cr.record_execution("github", 10, 8, 2, 1, 60.0)
        self.assertEqual(exec_.connector_name, "github")
        self.assertEqual(exec_.signals_fetched, 10)

    def test_get_executions(self):
        cr = ConnectorRuntime()
        cr.record_execution("a", 5, 4, 1, 0, 30.0)
        cr.record_execution("a", 8, 6, 2, 1, 45.0)
        execs = cr.get_executions("a")
        self.assertEqual(len(execs), 2)

    def test_get_statistics(self):
        cr = ConnectorRuntime()
        cr.record_execution("a", 10, 8, 2, 1, 60.0)
        stats = cr.get_statistics("a")
        self.assertEqual(stats["total_executions"], 1)
        self.assertEqual(stats["total_signals"], 10)


class TestRuntimeMetrics(unittest.TestCase):
    def test_record_metric(self):
        rm = RuntimeMetrics()
        rm.record_metric("cpu_usage", 0.75)
        rm.record_metric("cpu_usage", 0.80)
        values = rm.get_metric("cpu_usage")
        self.assertEqual(len(values), 2)

    def test_increment_counter(self):
        rm = RuntimeMetrics()
        rm.increment_counter("total_signals", 5)
        rm.increment_counter("total_signals", 3)
        self.assertEqual(rm.get_counter("total_signals"), 8)

    def test_set_gauge(self):
        rm = RuntimeMetrics()
        rm.set_gauge("queue_depth", 42)
        self.assertEqual(rm.get_gauge("queue_depth"), 42)


class TestLatencyEngine(unittest.TestCase):
    def test_record_latency(self):
        le = LatencyEngine()
        le.record_latency("collector", 150.0)
        le.record_latency("collector", 200.0)
        stats = le.get_latency("collector")
        self.assertEqual(stats["count"], 2)
        self.assertEqual(stats["avg_ms"], 175.0)

    def test_get_all_latencies(self):
        le = LatencyEngine()
        le.record_latency("a", 100.0)
        le.record_latency("b", 200.0)
        all_lat = le.get_all_latencies()
        self.assertEqual(len(all_lat), 2)


class TestBottleneckEngine(unittest.TestCase):
    def test_analyze_bottlenecks(self):
        be = BottleneckEngine()
        for _ in range(80):
            be.record_stage("collector", 1)
        for _ in range(15):
            be.record_stage("validated", 1)
        for _ in range(5):
            be.record_stage("revenue_ready", 1)
        bottlenecks = be.analyze_bottlenecks()
        self.assertGreater(len(bottlenecks), 0)
        self.assertEqual(bottlenecks[0]["stage"], "collector")

    def test_get_conversion_rates(self):
        be = BottleneckEngine()
        be.record_stage("a", 10)
        be.record_stage("b", 8)
        rates = be.get_conversion_rates()
        self.assertIn("a_to_b", rates)
        self.assertEqual(rates["a_to_b"], 0.8)


class TestReplayEngine(unittest.TestCase):
    def test_replay_run(self):
        re_ = ReplayEngine()
        result = re_.replay_run("run-1", "github", [{"stage": "collected", "count": 10}])
        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.connector, "github")

    def test_get_replay(self):
        re_ = ReplayEngine()
        re_.replay_run("run-1", "github", [])
        replay = re_.get_replay("run-1")
        self.assertIsNotNone(replay)


class TestTimelineEngine(unittest.TestCase):
    def test_add_event(self):
        te = TimelineEngine()
        event = te.add_event("opp-1", "collected", "entered", "Entered collected stage")
        self.assertEqual(event.opportunity_id, "opp-1")
        self.assertEqual(event.stage, "collected")

    def test_get_timeline(self):
        te = TimelineEngine()
        te.add_event("opp-1", "collected", "entered", "desc1")
        te.add_event("opp-1", "validated", "entered", "desc2")
        timeline = te.get_timeline("opp-1")
        self.assertEqual(len(timeline), 2)


class TestVerificationEngine(unittest.TestCase):
    def test_verify_widget(self):
        ve = VerificationEngine()
        rec = ve.verify_widget("signals_today", "SELECT COUNT(*) FROM signals", 150, "live")
        self.assertEqual(rec.widget_name, "signals_today")
        self.assertTrue(rec.is_live)

    def test_get_live_widgets(self):
        ve = VerificationEngine()
        ve.verify_widget("a", "q", 10, "live")
        ve.verify_widget("b", "q", 0, "cached")
        live = ve.get_live_widgets()
        self.assertEqual(live, ["a"])


class TestDashboardService(unittest.TestCase):
    def test_detect_demo_data(self):
        ds = DashboardService()
        demo = ds.detect_demo_data([
            {"id": "1", "company_name": "TechFlow Inc", "website": "https://techflow.com"},
            {"id": "2", "company_name": "Acme Corp", "website": "https://acme.com"},
        ])
        self.assertEqual(len(demo), 1)
        self.assertEqual(demo[0]["keyword_matched"], "techflow")


class TestReports(unittest.TestCase):
    def test_generate_report(self):
        rp = Reports()
        report = rp.generate_report("daily", "Daily Report", {"signals": 100})
        self.assertEqual(report["report_type"], "daily")
        self.assertEqual(report["data"]["signals"], 100)

    def test_get_reports(self):
        rp = Reports()
        rp.generate_report("a", "R1", {})
        rp.generate_report("b", "R2", {})
        reports = rp.get_reports()
        self.assertEqual(len(reports), 2)


class TestAlerting(unittest.TestCase):
    def test_create_alert(self):
        al = Alerting()
        alert = al.create_alert("critical", "Test Alert", "Something went wrong")
        self.assertEqual(alert.severity, "critical")
        self.assertFalse(alert.resolved)

    def test_resolve_alert(self):
        al = Alerting()
        alert = al.create_alert("warning", "W1", "msg")
        result = al.resolve_alert(alert.id)
        self.assertTrue(result)
        self.assertEqual(len(al.get_active_alerts()), 0)

    def test_get_statistics(self):
        al = Alerting()
        al.create_alert("critical", "A1", "m")
        al.create_alert("warning", "A2", "m")
        al.create_alert("info", "A3", "m")
        stats = al.get_statistics()
        self.assertEqual(stats["total_alerts"], 3)
        self.assertEqual(stats["active"], 3)


if __name__ == "__main__":
    unittest.main()
