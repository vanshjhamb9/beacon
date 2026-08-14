"""Tests for DQE v2 Orchestrator — integration of scoring, grading, and pipeline."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from discovery_quality_engine.activity_engine import ActivityEvidence
from discovery_quality_engine.dqe_orchestrator_v2 import DQEOrchestratorV2, DQEResultV2
from discovery_quality_engine.v2_schemas import QualityGrade


class TestDQEOrchestratorV2:
    def _make(self, **kwargs):
        return DQEOrchestratorV2(**kwargs)

    def test_full_acceptance(self):
        orch = self._make()
        now = datetime(2026, 7, 1, tzinfo=UTC)
        activity = [
            ActivityEvidence(
                activity_type="Hiring",
                timestamp=now - timedelta(days=5),
                source="LinkedIn",
                title="Hired engineer",
            )
        ]
        result = orch.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="Technology",
            country="US",
            signal_type="Hiring",
            signal_source="LinkedIn",
            signal_title="Senior Engineer hired",
            signal_timestamp=now - timedelta(days=10),
            signal_types=["Hiring"],
            domain="acme.com",
            has_https=True,
            content_length=5000,
            company_age_days=1000,
            activity_evidence=activity,
            now=now,
        )
        assert result.decision in ("ACCEPT", "HOLD")
        assert result.grade in (
            QualityGrade.A_PLUS, QualityGrade.A,
            QualityGrade.B, QualityGrade.C,
        )
        assert result.report.quality_score is not None
        assert result.report.quality_score.total_score >= 0
        assert len(result.report.audit_trail) > 0

    def test_reject_empty_company(self):
        orch = self._make()
        now = datetime(2026, 7, 1, tzinfo=UTC)
        result = orch.evaluate(
            company_id=uuid4(),
            company_name="",
            signal_type="Hiring",
            signal_source="LinkedIn",
            signal_title="Hired",
            signal_timestamp=now - timedelta(days=10),
            now=now,
        )
        assert result.decision == "REJECT"
        assert result.grade == QualityGrade.REJECT
        assert len(result.gates_failed) > 0

    def test_reject_stale_signal(self):
        orch = self._make()
        now = datetime(2026, 7, 1, tzinfo=UTC)
        result = orch.evaluate(
            company_id=uuid4(),
            company_name="Old Corp",
            website="https://old.com",
            industry="Technology",
            country="US",
            signal_type="Hiring",
            signal_source="LinkedIn",
            signal_title="Old hiring",
            signal_timestamp=now - timedelta(days=250),
            domain="old.com",
            has_https=True,
            content_length=5000,
            company_age_days=1000,
            now=now,
        )
        assert result.decision == "REJECT"
        assert result.grade == QualityGrade.REJECT
        assert any("borderline" in r.lower() or "expired" in r.lower() or "days old" in r.lower() for r in result.rejection_reasons)

    def test_borderline_signal_gets_hold(self):
        orch = self._make()
        now = datetime(2026, 7, 1, tzinfo=UTC)
        activity = [
            ActivityEvidence(
                activity_type="Hiring",
                timestamp=now - timedelta(days=5),
                source="LinkedIn",
                title="Hired engineer",
            )
        ]
        result = orch.evaluate(
            company_id=uuid4(),
            company_name="Borderline Corp",
            website="https://border.com",
            industry="Technology",
            country="US",
            signal_type="Hiring",
            signal_source="LinkedIn",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=120),
            signal_types=["Hiring"],
            domain="border.com",
            has_https=True,
            content_length=5000,
            company_age_days=1000,
            activity_evidence=activity,
            now=now,
        )
        assert result.decision in ("ACCEPT", "HOLD")
        assert result.grade in (QualityGrade.C, QualityGrade.B, QualityGrade.A, QualityGrade.A_PLUS)

    def test_reject_competitor(self):
        orch = self._make()
        now = datetime(2026, 7, 1, tzinfo=UTC)
        result = orch.evaluate(
            company_id=uuid4(),
            company_name="Microsoft",
            website="https://microsoft.com",
            industry="Technology",
            country="US",
            signal_type="Hiring",
            signal_source="LinkedIn",
            signal_title="Engineer hired",
            signal_timestamp=now - timedelta(days=10),
            domain="microsoft.com",
            has_https=True,
            content_length=5000,
            company_age_days=10000,
            now=now,
        )
        assert result.decision == "REJECT"
        assert result.grade == QualityGrade.REJECT

    def test_not_valid_buying_signal_rejects(self):
        orch = self._make()
        now = datetime(2026, 7, 1, tzinfo=UTC)
        result = orch.evaluate(
            company_id=uuid4(),
            company_name="Blog Corp",
            website="https://blog.com",
            industry="Technology",
            country="US",
            signal_type="Blog posts",
            signal_source="Twitter",
            signal_title="Blog post",
            signal_timestamp=now - timedelta(days=10),
            domain="blog.com",
            has_https=True,
            content_length=5000,
            company_age_days=1000,
            signal_types=["Blog posts"],
            now=now,
        )
        assert result.decision == "REJECT"
        assert result.grade == QualityGrade.REJECT

    def test_report_has_score_components(self):
        orch = self._make()
        now = datetime(2026, 7, 1, tzinfo=UTC)
        result = orch.evaluate(
            company_id=uuid4(),
            company_name="Score Corp",
            website="https://score.com",
            industry="Technology",
            country="US",
            signal_type="Hiring",
            signal_source="LinkedIn",
            signal_title="Hired",
            signal_timestamp=now - timedelta(days=10),
            domain="score.com",
            has_https=True,
            content_length=5000,
            company_age_days=500,
            now=now,
        )
        if result.report.quality_score:
            assert len(result.report.quality_score.components) == 8
            component_names = {c.name for c in result.report.quality_score.components}
            assert "freshness" in component_names
            assert "buying_signal" in component_names
            assert "source_trust" in component_names
            assert "website_quality" in component_names

    def test_audit_trail_populated(self):
        orch = self._make()
        now = datetime(2026, 7, 1, tzinfo=UTC)
        result = orch.evaluate(
            company_id=uuid4(),
            company_name="Audit Corp",
            website="https://audit.com",
            industry="Technology",
            country="US",
            signal_type="Hiring",
            signal_source="LinkedIn",
            signal_title="Hired",
            signal_timestamp=now - timedelta(days=10),
            domain="audit.com",
            has_https=True,
            content_length=5000,
            company_age_days=500,
            now=now,
        )
        assert len(result.report.audit_trail) > 0
        for entry in result.report.audit_trail:
            assert entry.gate
            assert entry.decision in ("PASS", "FAIL", "ACCEPT", "REJECT", "HOLD")
            assert entry.timestamp is not None

    def test_metadata_has_event_id(self):
        orch = self._make()
        now = datetime(2026, 7, 1, tzinfo=UTC)
        result = orch.evaluate(
            company_id=uuid4(),
            company_name="Meta Corp",
            website="https://meta.com",
            industry="Technology",
            country="US",
            signal_type="Hiring",
            signal_source="LinkedIn",
            signal_title="Hired",
            signal_timestamp=now - timedelta(days=10),
            domain="meta.com",
            has_https=True,
            content_length=5000,
            company_age_days=500,
            now=now,
        )
        assert "event_id" in result.metadata

    def test_dashboard_records_events(self):
        orch = self._make()
        now = datetime(2026, 7, 1, tzinfo=UTC)
        orch.evaluate(
            company_id=uuid4(),
            company_name="Dash Corp",
            website="https://dash.com",
            industry="Technology",
            country="US",
            signal_type="Hiring",
            signal_source="LinkedIn",
            signal_title="Hired",
            signal_timestamp=now - timedelta(days=10),
            domain="dash.com",
            has_https=True,
            content_length=5000,
            company_age_days=500,
            now=now,
        )
        snap = orch.dashboard.snapshot(now=now)
        assert snap.signals_collected >= 1
