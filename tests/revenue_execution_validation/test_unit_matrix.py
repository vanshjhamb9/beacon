"""rev-v1 unit + volume matrix."""

from __future__ import annotations

import pytest

from revenue_execution_validation import LIVE_OUTREACH_ENABLED, PRODUCTION_SEND_LOCKED, SCORING_VERSION
from revenue_execution_validation.acceptance.engine import AcceptanceGateEngine
from revenue_execution_validation.connector_scoreboard.engine import ConnectorScoreboardEngine
from revenue_execution_validation.founder_queue_v3.engine import FounderQueueV3Engine
from revenue_execution_validation.funnel.engine import STAGE_ORDER, RealityFunnelEngine
from revenue_execution_validation.manual_qa.engine import ManualQaWorkspaceEngine
from revenue_execution_validation.models.types import ConnectorGrade, ManualQaRating, RejectionReason
from revenue_execution_validation.pipelines.engine import RevenueExecutionPipeline
from revenue_execution_validation.rebuild.engine import RevRebuildEngine
from revenue_execution_validation.rejection.engine import RejectionAnalysisEngine


def _ready(i: int, *, source: str = "product_hunt") -> dict:
    return {
        "company_id": f"ready-{i}",
        "company_name": f"ReadyCo{i}",
        "website": f"https://ready{i}.com",
        "official_website": f"https://ready{i}.com",
        "domain": f"ready{i}.com",
        "country": "United States",
        "industry": "Software",
        "description": f"ReadyCo{i} enterprise SaaS automation platform",
        "erowd_admitted": True,
        "erowd_verified": True,
        "website_verified": True,
        "source": source,
        "buying_signals": ["Hiring", "Scaling"],
        "best_service": "AI Automation",
        "service_matches": [{"service": "AI Automation"}],
        "business_email": f"hello@ready{i}.com",
        "decision_maker": f"Pat {i} (CEO)",
        "why_now": "Hiring while scaling",
        "opportunity": "AI Automation",
        "confidence": 85,
        "evidence": ["hiring"],
        "cir_classification": "Revenue Ready",
    }


def _noise(i: int, *, source: str = "reddit") -> dict:
    return {
        "company_id": f"noise-{i}",
        "company_name": f"Noise{i}",
        "source": source,
        "url": f"https://reddit.com/r/x/{i}",
    }


pipe = RevenueExecutionPipeline()


def test_locks():
    assert SCORING_VERSION == "rev-v1"
    assert LIVE_OUTREACH_ENABLED is False
    assert PRODUCTION_SEND_LOCKED is True


def test_funnel_stages_complete():
    assert len(STAGE_ORDER) == 15
    assert STAGE_ORDER[0] == "Signals Collected"
    assert STAGE_ORDER[-1] == "Won"


@pytest.mark.parametrize("i", range(40))
def test_ready_matrix(i):
    snap = pipe.evaluate(_ready(i, source=["product_hunt", "github_trending", "rss", "devto"][i % 4]))
    assert snap.check.is_revenue_ready
    assert snap.check.business_email
    assert snap.check.evidence


@pytest.mark.parametrize("i", range(40))
def test_reject_noise_matrix(i):
    snap = pipe.evaluate(_noise(i))
    assert not snap.check.is_revenue_ready


@pytest.mark.parametrize("reason", list(RejectionReason))
def test_rejection_taxonomy(reason):
    assert reason.value


@pytest.mark.parametrize("rating", list(ManualQaRating))
def test_qa_ratings(rating):
    assert rating.value


def test_founder_queue_top_10_only_ready():
    snaps = [pipe.evaluate(_ready(i)) for i in range(15)] + [pipe.evaluate(_noise(i)) for i in range(20)]
    cards = FounderQueueV3Engine().build(snaps)
    assert len(cards) == 10
    assert all(c.revenue_ready and c.verified_email != "UNKNOWN" for c in cards)


def test_connector_grades_not_hardcoded_per_name():
    snaps = [pipe.evaluate(_ready(i, source="product_hunt")) for i in range(10)] + [
        pipe.evaluate(_noise(i, source="reddit")) for i in range(30)
    ]
    scores = ConnectorScoreboardEngine().score(snaps)
    by = {s.connector: s for s in scores}
    assert by["product_hunt"].grade in {ConnectorGrade.EXCELLENT, ConnectorGrade.GOOD, ConnectorGrade.WEAK}
    assert by["reddit"].revenue_ready_pct < by["product_hunt"].revenue_ready_pct


def test_rejection_analysis():
    snaps = [pipe.evaluate(_noise(i)) for i in range(20)] + [pipe.evaluate(_ready(1))]
    report = RejectionAnalysisEngine().analyze(snaps)
    assert report["total_rejected"] >= 20
    assert report["top_rejection_reasons"]


def test_manual_qa_analytics_only():
    engine = ManualQaWorkspaceEngine()
    analytics = engine.analytics(
        [{"rating": "Excellent"}, {"rating": "Good"}, {"rating": "Fake"}, {"rating": "Wrong contact"}]
    )
    assert analytics["note"].startswith("Analytics only")
    assert analytics["accuracy_pct"] == 50.0


def test_acceptance_gates_lock_production():
    snaps = [pipe.evaluate(_ready(i)) for i in range(10)]
    cards = FounderQueueV3Engine().build(snaps)
    gate = AcceptanceGateEngine().evaluate(snaps, founder_queue=cards, qa_accuracy=100, qa_sample_size=10)
    assert gate.production_unlocked is False
    assert "revenue_ready_below_25" in gate.failures
    flags = AcceptanceGateEngine().outreach_flags(gate)
    assert flags["GMAIL_PRODUCTION_ENABLED"] is False


def test_acceptance_gates_pass_with_volume():
    snaps = [pipe.evaluate(_ready(i)) for i in range(30)]
    cards = FounderQueueV3Engine().build(snaps)
    gate = AcceptanceGateEngine().evaluate(snaps, founder_queue=cards, qa_accuracy=96, qa_sample_size=20)
    assert gate.revenue_ready_count >= 25
    assert gate.verified_emails >= 15
    assert gate.named_decision_makers >= 10
    assert gate.production_unlocked is True


def test_rebuild_report():
    snaps = [pipe.evaluate(_ready(i)) for i in range(30)] + [pipe.evaluate(_noise(i)) for i in range(20)]
    report = RevRebuildEngine().build(snaps, signals_collected=100, qa_accuracy=96, qa_sample_size=20)
    assert report.revenue_ready >= 25
    assert report.funnel.stages
    assert report.daily.recommendation
    assert report.acceptance.production_unlocked


def test_funnel_percentages():
    snaps = [pipe.evaluate(_ready(i)) for i in range(5)]
    funnel = RealityFunnelEngine().build(snaps, signals_collected=10)
    assert funnel.stages[0].count == 10
    assert funnel.revenue_ready == 5


@pytest.mark.parametrize("i", range(80))
def test_volume_pipeline(i):
    payload = _ready(i) if i % 3 else _noise(i)
    snap = pipe.evaluate(payload)
    assert snap.company_id
    assert snap.processing_ms >= 0
