from datetime import UTC, datetime
from uuid import uuid4

from founder_os import FounderOsService, FounderOsInput
from founder_os.models.types import AnalyticsEventType


def test_integration_evaluate_track_roundtrip() -> None:
    service = FounderOsService()
    decision = service.evaluate(
        FounderOsInput(
            a_plus_opportunities=1,
            expected_revenue=12_000,
            estimated_pipeline=40_000,
            contacted_count=10,
            replied_count=3,
            industry_wins={"SaaS": 2},
            top_companies=[
                {
                    "company_id": str(uuid4()),
                    "company_name": "Orbit",
                    "priority_grade": "A+",
                    "recommended_service": "SaaS",
                    "expected_budget": "$40k–$90k",
                    "probability": 72,
                    "evidence": ["grade:A+"],
                }
            ],
            now=datetime.now(UTC),
        )
    )
    assert decision.scoring_version == "fos-v1"
    tracked = service.track(
        event_type=AnalyticsEventType.APPROVAL,
        action="approve_campaign",
        entity_type="campaign",
        entity_id=str(uuid4()),
    )
    assert tracked.event_type == AnalyticsEventType.APPROVAL
