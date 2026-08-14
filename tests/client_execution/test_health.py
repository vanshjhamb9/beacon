from uuid import uuid4

import pytest

from client_execution.health.engine import ClientHealthEngine
from client_execution.models.types import ClientExecutionInput, ClientLifecycleStage


def _item(**overrides: object) -> ClientExecutionInput:
    base: dict[str, object] = {"company_id": uuid4(), "company_name": "Health Co", "won": True}
    base.update(overrides)
    return ClientExecutionInput.model_validate(base)


@pytest.mark.parametrize(
    ("kwargs", "expected_status"),
    [
        ({"satisfaction": 90, "communication_score": 90, "delivery_progress": 90, "open_issues": 0}, "healthy"),
        ({"satisfaction": 55, "communication_score": 55, "delivery_progress": 50, "open_issues": 1}, "watch"),
        ({"satisfaction": 20, "communication_score": 20, "delivery_progress": 20, "open_issues": 6, "risks": ["a", "b", "c", "d", "e"]}, "at_risk"),
    ],
)
def test_health_status_bands(kwargs: dict, expected_status: str) -> None:
    h = ClientHealthEngine().score(_item(**kwargs), stage=ClientLifecycleStage.SUPPORT)
    assert h.status == expected_status


def test_renewal_boost_near_window() -> None:
    near = ClientHealthEngine().score(_item(days_to_renewal=30, satisfaction=70), stage=ClientLifecycleStage.SUPPORT)
    far = ClientHealthEngine().score(_item(days_to_renewal=200, satisfaction=70), stage=ClientLifecycleStage.SUPPORT)
    assert near.renewal_probability >= far.renewal_probability


def test_upsell_probability_grows_with_signals() -> None:
    low = ClientHealthEngine().score(_item(), stage=ClientLifecycleStage.LAUNCH)
    high = ClientHealthEngine().score(
        _item(growth_signals=["growth"], hiring_signals=["hiring"], funding_signals=["funding"], upsell_signal=True),
        stage=ClientLifecycleStage.LAUNCH,
    )
    assert high.upsell_probability > low.upsell_probability


def test_meeting_frequency_score() -> None:
    h = ClientHealthEngine().score(_item(meetings_last_30d=5), stage=ClientLifecycleStage.DEVELOPMENT)
    assert h.meeting_frequency_score == 100.0


def test_delay_score_scales() -> None:
    h = ClientHealthEngine().score(_item(delay_days=5), stage=ClientLifecycleStage.TESTING)
    assert h.delay_score == 40.0
