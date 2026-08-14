from __future__ import annotations

from intelligence_center.discovery_engine import filter_discoveries, make_headline
from intelligence_center.journey_engine import assemble_company_journey, build_journey_stages
from intelligence_center.models import DiscoveryCard, DiscoveryEventType
from intelligence_center.roi_engine import compute_roi_row, rank_connectors
from intelligence_center.dataset_engine import compute_dataset_statistics
from intelligence_center.replay_engine import build_heatmap, heatmap_tone
from datetime import UTC, datetime


def test_journey_builds_end_to_end_stages() -> None:
    now = datetime.now(UTC)
    facts = {
        "signal_at": now,
        "identity_at": now,
        "website_at": now,
        "email_at": now,
        "decision_maker_at": now,
        "sales_ready_at": now,
        "revenue_ready_at": now,
        "outreach_at": now,
        "reply_at": now,
        "meeting_at": now,
        "proposal_at": now,
        "won_at": now,
        "signal_connector": "github_trending",
        "website_evidence": ["heroiclabs.com"],
    }
    stages = build_journey_stages(facts)
    assert len(stages) == 13
    assert all(s.status in {"completed", "skipped"} for s in stages)
    assert next(s for s in stages if s.stage == "won").status == "completed"
    assert next(s for s in stages if s.stage == "lost").status == "skipped"
    journey = assemble_company_journey(
        company_id="abc",
        company_name="Heroic Labs",
        industry="Gaming",
        facts=facts,
    )
    assert journey.current_stage == "won"
    assert len(journey.pipeline_health) == 13

    lost_facts = {**facts}
    del lost_facts["won_at"]
    lost_facts["lost_at"] = now
    lost_journey = assemble_company_journey(
        company_id="abc",
        company_name="Heroic Labs",
        industry="Gaming",
        facts=lost_facts,
    )
    assert lost_journey.current_stage == "lost"


def test_connector_roi_estimates_cost() -> None:
    row = compute_roi_row(
        connector="hunter",
        healthy=True,
        emails=92,
        revenue_ready=18,
        meetings=3,
        wins=1,
        latency_ms=340,
        success_pct=78,
    )
    assert row.api_cost > 0
    assert row.win_pct > 0
    ranked = rank_connectors(
        [
            row,
            compute_roi_row(connector="github_trending", healthy=True, signals=820, revenue_ready=17),
        ]
    )
    assert ranked[0].connector in {"hunter", "github_trending"}


def test_dataset_rates() -> None:
    stats = compute_dataset_statistics(
        signals_collected=1000,
        duplicates=100,
        spam=50,
        working_websites=200,
        dead_websites=50,
        emails_found=80,
        verified_emails=40,
        decision_makers=20,
        revenue_ready=10,
    )
    # 100 duplicates over 1100 observed items (1000 stored + 100 removed)
    assert stats.duplicate_rate == 9.1
    assert stats.spam_rate == 5.0
    assert stats.verification_rate == 80.0


def test_discovery_filters_and_headlines() -> None:
    cards = [
        DiscoveryCard(
            id="1",
            event_type=DiscoveryEventType.REVENUE_READY.value,
            timestamp=datetime.now(UTC),
            company_name="Clay",
            collector="github_trending",
            is_revenue_ready=True,
            headline=make_headline(DiscoveryEventType.REVENUE_READY.value, detail="98"),
        ),
        DiscoveryCard(
            id="2",
            event_type="Error",
            timestamp=datetime.now(UTC),
            company_name="X",
            is_error=True,
            headline="fail",
        ),
    ]
    filtered = filter_discoveries(cards, revenue_ready_only=True)
    assert len(filtered) == 1
    assert filtered[0].company_name == "Clay"
    errors = filter_discoveries(cards, errors_only=True)
    assert len(errors) == 1


def test_heatmap_tone() -> None:
    assert heatmap_tone(success_pct=95, failures=0, count=10) == "green"
    assert heatmap_tone(success_pct=20, failures=5, count=10) == "red"
    cells = build_heatmap(
        [{"stage": "collector", "count": 10, "success_pct": 90, "failures": 0, "avg_duration": 1.0}]
    )
    assert cells[0].tone == "green"


def test_bic_routes_registered() -> None:
    from app.main import app

    paths = {route.path for route in app.routes}
    assert "/api/v1/discoveries/live" in paths
    assert "/api/v1/discoveries/company/{company_id}" in paths
    assert "/api/v1/connectors/roi" in paths
    assert "/api/v1/dataset/statistics" in paths
    assert "/api/v1/company/{company_id}/journey" in paths
    assert "/api/v1/pipeline/replay" in paths
    assert "/api/v1/analytics/v2" in paths
    assert "/api/v1/intelligence/search" in paths
