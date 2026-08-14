"""Dashboard contract: founder home consumes command-center shaped pack."""

from founder_os import FounderOsPipeline, FounderOsInput
from datetime import UTC, datetime
from uuid import uuid4


def test_dashboard_pack_has_required_home_sections() -> None:
    decision = FounderOsPipeline().process(
        FounderOsInput(
            expected_revenue=10_000,
            estimated_pipeline=50_000,
            a_plus_opportunities=1,
            campaigns_waiting_approval=1,
            replies_waiting=1,
            meetings_today=1,
            top_companies=[
                {
                    "company_id": str(uuid4()),
                    "company_name": "Acme",
                    "priority_grade": "A",
                    "recommended_service": "Website",
                    "expected_budget": "$12k–$30k",
                    "probability": 55,
                    "evidence": ["x"],
                }
            ],
            now=datetime.now(UTC),
        )
    )
    pack = {
        "brief": decision.brief.model_dump(mode="json"),
        "assistant": decision.assistant.model_dump(mode="json"),
        "command_center": decision.command_center.model_dump(mode="json"),
        "tasks": [t.model_dump(mode="json") for t in decision.tasks],
        "recommendations": [r.model_dump(mode="json") for r in decision.recommendations],
        "meeting_packs": [m.model_dump(mode="json") for m in decision.meeting_packs],
    }
    assert "executive_summary" in pack["brief"]
    assert "greeting" in pack["assistant"]
    assert "mission" in pack["assistant"]
    assert "todays_top_companies" in pack["command_center"]
    assert "campaign_queue" in pack["command_center"]
    assert "inbox" in pack["command_center"]
