"""Tests for DQEOrchestrator — full pipeline integration tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from discovery_quality_engine.activity_engine import ActivityEvidence
from discovery_quality_engine.competitor_engine import CompetitorConfig
from discovery_quality_engine.dqe_orchestrator import DQEOrchestrator, DQEResult
from discovery_quality_engine.quality_engine import QualityDecision, QualityGate


class TestDQEOrchestrator:
    def setup_method(self) -> None:
        self.orchestrator = DQEOrchestrator(
            competitor_engine=CompetitorEngineStub(),
        )

    def test_full_acceptance(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orchestrator.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring SDRs",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="A legitimate company website with real content.",
            company_age_days=365,
            activity_evidence=[
                ActivityEvidence(
                    activity_type="HIRING",
                    timestamp=now - timedelta(days=3),
                    source="linkedin",
                    title="New job posting",
                ),
            ],
            description="Cloud-based CRM software",
            now=now,
        )
        assert result.decision == QualityDecision.ACCEPT
        assert len(result.gates_passed) >= 12
        assert len(result.gates_failed) == 0

    def test_reject_missing_company_name(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orchestrator.evaluate(
            company_id=uuid4(),
            company_name="",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT

    def test_reject_stale_signal(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orchestrator.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Old hiring",
            signal_timestamp=now - timedelta(days=45),
            has_https=True,
            content_length=500,
            page_text="Legit content",
            company_age_days=365,
            activity_evidence=[
                ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a"),
            ],
            description="Software",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT
        assert "FRESHNESS" in result.gates_failed
        assert any("STALE_SIGNAL" in r for r in result.rejection_reasons)

    def test_reject_no_buying_signal(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orchestrator.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Something",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="Legit content",
            company_age_days=365,
            activity_evidence=[
                ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a"),
            ],
            signal_types=["INVALID_SIGNAL"],
            description="Software",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT
        assert "BUYING_SIGNAL" in result.gates_failed

    def test_reject_competitor(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orchestrator.evaluate(
            company_id=uuid4(),
            company_name="Google",
            website="https://google.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="Legit content",
            company_age_days=365,
            activity_evidence=[
                ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a"),
            ],
            description="Software",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT
        assert "COMPETITOR_CHECK" in result.gates_failed

    def test_reject_ai_company(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orchestrator.evaluate(
            company_id=uuid4(),
            company_name="AI Startups Inc",
            website="https://aistartup.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="Legit content",
            company_age_days=365,
            activity_evidence=[
                ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a"),
            ],
            description="We build AI models for enterprise",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT
        assert "AI_COMPANY_FILTER" in result.gates_failed

    def test_reject_unsupported_region(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orchestrator.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="technology",
            country="KP",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="Legit content",
            company_age_days=365,
            activity_evidence=[
                ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a"),
            ],
            description="Software",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT
        assert "REGION_RULES" in result.gates_failed

    def test_reject_no_activity(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orchestrator.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="Legit content",
            company_age_days=365,
            activity_evidence=[],
            description="Software",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT
        assert "ACTIVITY_CHECK" in result.gates_failed

    def test_reject_parked_website(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orchestrator.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="This domain is parked and for sale",
            company_age_days=365,
            activity_evidence=[
                ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a"),
            ],
            description="Software",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT
        assert "WEBSITE_QUALITY" in result.gates_failed

    def test_reject_low_source_trust(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orchestrator.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="unknown_blog",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="Legit content",
            company_age_days=365,
            activity_evidence=[
                ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a"),
            ],
            description="Software",
            now=now,
        )
        assert result.decision == QualityDecision.REJECT
        assert "SOURCE_TRUST" in result.gates_failed

    def test_gates_passed_populated(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orchestrator.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            website="https://acme.com",
            industry="technology",
            country="US",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            has_https=True,
            content_length=500,
            page_text="Legit content",
            company_age_days=365,
            activity_evidence=[
                ActivityEvidence(activity_type="HIRING", timestamp=now - timedelta(days=3), source="a", title="a"),
            ],
            description="Software",
            now=now,
        )
        assert QualityGate.FRESHNESS.value in result.gates_passed
        assert QualityGate.BUYING_SIGNAL.value in result.gates_passed
        assert QualityGate.COMPANY_VALIDATION.value in result.gates_passed
        assert QualityGate.COMPETITOR_CHECK.value in result.gates_passed

    def test_dashboard_records_events(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        self.orchestrator.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            now=now,
        )
        snap = self.orchestrator.dashboard.snapshot()
        assert snap.signals_collected >= 1

    def test_metadata_contains_event_id(self) -> None:
        now = datetime(2026, 7, 29, tzinfo=UTC)
        result = self.orchestrator.evaluate(
            company_id=uuid4(),
            company_name="Acme Corp",
            signal_type="HIRING",
            signal_source="linkedin",
            signal_title="Hiring",
            signal_timestamp=now - timedelta(days=5),
            now=now,
        )
        assert "event_id" in result.metadata


from discovery_quality_engine.competitor_engine import CompetitorEngine


class CompetitorEngineStub(CompetitorEngine):
    def __init__(self) -> None:
        super().__init__(config=CompetitorConfig(
            competitors=["google", "microsoft", "salesforce"],
        ))
