from uuid import uuid4

import pytest

from client_execution.models.types import ClientExecutionInput, UpsellService
from client_execution.upsell.engine import UpsellEngine


def _item(**overrides: object) -> ClientExecutionInput:
    base: dict[str, object] = {"company_id": uuid4(), "company_name": "Upsell Co", "won": True}
    base.update(overrides)
    return ClientExecutionInput.model_validate(base)


@pytest.mark.parametrize(
    ("signals", "service"),
    [
        ({"hiring_signals": ["team growth hiring"]}, UpsellService.INTERNAL_TOOLS),
        ({"funding_signals": ["raised series b"]}, UpsellService.CUSTOM_SAAS),
        ({"usage_signals": ["active users adoption"]}, UpsellService.ANALYTICS),
        ({"support_requests": [{"summary": "ticket incident flood"}]}, UpsellService.AI_AUTOMATION),
        ({"expansion_signals": ["new market office"]}, UpsellService.WEBSITE_UPGRADE),
        ({"pain_points": ["need mobile ios android app"]}, UpsellService.MOBILE_APP),
        ({"pain_points": ["crm salesforce pipeline"]}, UpsellService.CRM),
        ({"pain_points": ["manual ops automation"]}, UpsellService.AI_AUTOMATION),
    ],
)
def test_upsell_signal_map(signals: dict, service: UpsellService) -> None:
    ups = UpsellEngine().recommend(_item(**signals))
    assert any(u.service == service for u in ups)


def test_upsell_ids_stable() -> None:
    item = _item(company_id=uuid4(), hiring_signals=["hiring"])
    # freeze company id
    cid = uuid4()
    a = UpsellEngine().recommend(_item(company_id=cid, hiring_signals=["hiring"]))
    b = UpsellEngine().recommend(_item(company_id=cid, hiring_signals=["hiring"]))
    assert [u.recommendation_id for u in a] == [u.recommendation_id for u in b]


def test_upsell_max_seven() -> None:
    ups = UpsellEngine().recommend(
        _item(
            hiring_signals=["hiring"],
            funding_signals=["raised series"],
            usage_signals=["usage adoption"],
            support_requests=[{"summary": "ticket"}],
            expansion_signals=["new market"],
            pain_points=["mobile ios", "crm salesforce", "manual ops automation"],
        )
    )
    assert len(ups) <= 7


def test_no_production_mutation() -> None:
    ups = UpsellEngine().recommend(_item(upsell_signal=True, hiring_signals=["hiring"]))
    assert all(u.modifies_production is False for u in ups)
    assert all(u.requires_founder_approval is True for u in ups)
