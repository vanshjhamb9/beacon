from uuid import uuid4

import pytest

from client_execution.lifecycle.engine import ClientLifecycleEngine
from client_execution.models.types import ClientExecutionInput, ClientLifecycleStage


def _item(**overrides: object) -> ClientExecutionInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Lifecycle Co",
        "won": True,
    }
    payload.update(overrides)
    return ClientExecutionInput.model_validate(payload)


@pytest.mark.parametrize(
    ("kwargs", "stage"),
    [
        ({"contract_signed": True}, ClientLifecycleStage.WON),
        ({"won": True, "contract_signed": False}, ClientLifecycleStage.CONTRACT_PENDING),
        ({"contract_signed": True, "kickoff_scheduled": True}, ClientLifecycleStage.KICKOFF_SCHEDULED),
        ({"kickoff_scheduled": True, "requirements": ["x"]}, ClientLifecycleStage.REQUIREMENTS_GATHERING),
        ({"requirements_complete": True, "kickoff_scheduled": True}, ClientLifecycleStage.REQUIREMENTS_GATHERING),
        ({"planning_complete": True}, ClientLifecycleStage.PLANNING),
        ({"design_complete": True}, ClientLifecycleStage.DESIGN),
        ({"development_active": True}, ClientLifecycleStage.DEVELOPMENT),
        ({"testing_active": True}, ClientLifecycleStage.TESTING),
        ({"in_review": True}, ClientLifecycleStage.REVIEW),
        ({"launched": True}, ClientLifecycleStage.LAUNCH),
        ({"in_support": True}, ClientLifecycleStage.SUPPORT),
        ({"launched": True, "upsell_signal": True}, ClientLifecycleStage.UPSELL_OPPORTUNITY),
        ({"renewal_due": True}, ClientLifecycleStage.RENEWAL),
        ({"referral_made": True}, ClientLifecycleStage.REFERRAL),
        ({"lost_client": True}, ClientLifecycleStage.LOST_CLIENT),
        ({"archived": True}, ClientLifecycleStage.ARCHIVE),
    ],
)
def test_lifecycle_stages(kwargs: dict, stage: ClientLifecycleStage) -> None:
    assert ClientLifecycleEngine().infer_stage(_item(**kwargs)) == stage


def test_stage_hint_fallback() -> None:
    assert ClientLifecycleEngine().infer_stage(_item(won=True, contract_signed=True, stage_hint="support")) == ClientLifecycleStage.SUPPORT


def test_invalid_stage_hint_defaults_won() -> None:
    assert ClientLifecycleEngine().infer_stage(_item(won=True, contract_signed=True, stage_hint="nope")) == ClientLifecycleStage.WON


def test_all_stages_enum_complete() -> None:
    expected = {
        "won",
        "contract_pending",
        "kickoff_scheduled",
        "requirements_gathering",
        "planning",
        "design",
        "development",
        "testing",
        "review",
        "launch",
        "support",
        "upsell_opportunity",
        "renewal",
        "referral",
        "lost_client",
        "archive",
    }
    assert {s.value for s in ClientLifecycleStage} == expected
