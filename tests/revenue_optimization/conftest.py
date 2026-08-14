from datetime import UTC, datetime
from uuid import uuid4

import pytest

from revenue_optimization.models.types import OutreachEvent, ROIPInput


@pytest.fixture
def make_event():
    def _make(**overrides: object) -> OutreachEvent:
        payload: dict[str, object] = {
            "event_id": f"evt-{uuid4()}",
            "company_id": uuid4(),
            "company_name": "Acme SaaS",
            "campaign_id": "camp-1",
            "industry": "SaaS",
            "company_size_band": "50-200",
            "channel": "email",
            "subject": "Quick idea for Acme",
            "cta": "book_meeting",
            "offer": "AI Automation",
            "delivered": True,
            "opened": True,
            "open_count": 2,
            "open_hour": 9,
            "open_weekday": 1,
            "open_device": "desktop",
            "open_country": "US",
            "calendly_clicks": 1,
            "website_visits": 2,
            "replied": True,
            "reply_hours": 12.0,
            "reply_text": "interested let's meet",
            "meeting_booked": True,
            "proposal_sent": True,
            "closed_won": True,
            "deal_value": 25000.0,
            "followup_number": 2,
            "sequence_length": 4,
            "delay_days": 4.0,
            "timezone": "UTC",
            "founder_actor": True,
            "evidence": ["unit:true"],
        }
        payload.update(overrides)
        return OutreachEvent.model_validate(payload)

    return _make


@pytest.fixture
def make_input(make_event):
    def _make(n: int = 5, **event_overrides: object) -> ROIPInput:
        events = [make_event(company_name=f"Co{i}", event_id=f"e{i}", **event_overrides) for i in range(n)]
        return ROIPInput(
            events=events,
            previous_period_events=events[: max(1, n // 2)],
            portfolio_assets=[
                {
                    "asset_id": "cs-1",
                    "asset_type": "case_study",
                    "title": "SaaS automation win",
                    "industry": "SaaS",
                    "company_size": "50-200",
                }
            ],
            now=datetime.now(UTC),
        )

    return _make
