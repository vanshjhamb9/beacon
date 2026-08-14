"""Tests for connector scheduler."""

from __future__ import annotations

import pytest

from opportunity_connector_platform.scheduler import ConnectorScheduler, RetryPolicy, ScheduleDeclaration


class TestRetryPolicy:
    def test_default(self):
        rp = RetryPolicy()
        assert rp.attempts == 3
        assert rp.backoff_seconds == 60

    def test_custom(self):
        rp = RetryPolicy(attempts=5, backoff_seconds=120)
        assert rp.attempts == 5
        assert rp.backoff_seconds == 120

    def test_frozen(self):
        rp = RetryPolicy()
        with pytest.raises(AttributeError):
            rp.attempts = 10  # type: ignore[misc]


class TestScheduleDeclaration:
    def test_create(self):
        decl = ScheduleDeclaration(connector_id="c1", interval=300, priority="high")
        assert decl.connector_id == "c1"
        assert decl.interval == 300
        assert decl.priority == "high"
        assert decl.dependencies == ()
        assert decl.max_concurrency == 1
        assert decl.timeout == 30

    def test_frozen(self):
        decl = ScheduleDeclaration(connector_id="c1", interval=300, priority="high")
        with pytest.raises(AttributeError):
            decl.interval = 600  # type: ignore[misc]

    def test_dependencies(self):
        decl = ScheduleDeclaration(
            connector_id="c1", interval=300, priority="high",
            dependencies=("auth", "lookup"),
        )
        assert decl.dependencies == ("auth", "lookup")


class TestConnectorScheduler:
    def test_declare(self):
        s = ConnectorScheduler()
        decl = s.declare(connector_id="c1", interval=300, priority="high")
        assert decl.connector_id == "c1"
        assert decl.interval == 300

    def test_declare_with_retry(self):
        s = ConnectorScheduler()
        rp = RetryPolicy(attempts=5, backoff_seconds=120)
        decl = s.declare(connector_id="c1", interval=300, priority="high", retry_policy=rp)
        assert decl.retry_policy.attempts == 5

    def test_order_by_priority(self):
        s = ConnectorScheduler()
        decls = [
            s.declare(connector_id="c1", interval=300, priority="low"),
            s.declare(connector_id="c2", interval=300, priority="high"),
            s.declare(connector_id="c3", interval=300, priority="normal"),
        ]
        ordered = s.order(decls)
        assert ordered[0].connector_id == "c2"
        assert ordered[1].connector_id == "c3"
        assert ordered[2].connector_id == "c1"

    def test_order_by_interval_same_priority(self):
        s = ConnectorScheduler()
        decls = [
            s.declare(connector_id="c1", interval=900, priority="high"),
            s.declare(connector_id="c2", interval=300, priority="high"),
        ]
        ordered = s.order(decls)
        assert ordered[0].connector_id == "c2"
        assert ordered[1].connector_id == "c1"

    def test_ready_jobs_no_deps(self):
        s = ConnectorScheduler()
        decls = [
            s.declare(connector_id="c1", interval=300, priority="high"),
            s.declare(connector_id="c2", interval=300, priority="high"),
        ]
        ready = s.ready_jobs(decls, set())
        assert len(ready) == 2

    def test_ready_jobs_with_deps_met(self):
        s = ConnectorScheduler()
        decls = [
            s.declare(connector_id="c1", interval=300, priority="high"),
            s.declare(connector_id="c2", interval=300, priority="high", dependencies=("c1",)),
        ]
        ready = s.ready_jobs(decls, {"c1"})
        ids = [d.connector_id for d in ready]
        assert "c2" in ids

    def test_ready_jobs_with_deps_not_met(self):
        s = ConnectorScheduler()
        decls = [
            s.declare(connector_id="c1", interval=300, priority="high"),
            s.declare(connector_id="c2", interval=300, priority="high", dependencies=("c1",)),
        ]
        ready = s.ready_jobs(decls, set())
        assert len(ready) == 1
        assert ready[0].connector_id == "c1"

    def test_blocked_jobs(self):
        s = ConnectorScheduler()
        decls = [
            s.declare(connector_id="c1", interval=300, priority="high"),
            s.declare(connector_id="c2", interval=300, priority="high", dependencies=("c1",)),
        ]
        blocked = s.blocked_jobs(decls, set())
        assert len(blocked) == 1
        assert blocked[0].connector_id == "c2"

    def test_schedule_graph(self):
        s = ConnectorScheduler()
        decls = [
            s.declare(connector_id="c1", interval=300, priority="high"),
            s.declare(connector_id="c2", interval=300, priority="high", dependencies=("c1",)),
            s.declare(connector_id="c3", interval=300, priority="high", dependencies=("c2",)),
        ]
        graph = s.schedule_graph(decls)
        assert len(graph) == 3
        assert graph[0][0].connector_id == "c1"
        assert graph[1][0].connector_id == "c2"
        assert graph[2][0].connector_id == "c3"

    def test_schedule_graph_parallel(self):
        s = ConnectorScheduler()
        decls = [
            s.declare(connector_id="c1", interval=300, priority="high"),
            s.declare(connector_id="c2", interval=300, priority="high"),
            s.declare(connector_id="c3", interval=300, priority="high", dependencies=("c1", "c2")),
        ]
        graph = s.schedule_graph(decls)
        assert len(graph) == 2
        assert len(graph[0]) == 2
        assert len(graph[1]) == 1

    def test_empty_declarations(self):
        s = ConnectorScheduler()
        assert s.order([]) == []
        assert s.ready_jobs([], set()) == []
        assert s.blocked_jobs([], set()) == []
        assert s.schedule_graph([]) == []

    def test_declare_with_all_params(self):
        s = ConnectorScheduler()
        decl = s.declare(
            connector_id="c1",
            interval=60,
            priority="normal",
            dependencies=("auth",),
            max_concurrency=4,
            timeout=120,
            retry_policy=RetryPolicy(attempts=5, backoff_seconds=30),
        )
        assert decl.max_concurrency == 4
        assert decl.timeout == 120
        assert decl.retry_policy.attempts == 5
