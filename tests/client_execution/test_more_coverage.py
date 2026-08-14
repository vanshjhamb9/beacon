from uuid import uuid4

import pytest

from client_execution import ClientExecutionPipeline
from client_execution.models.types import ClientExecutionInput, ClientLifecycleStage, UpsellService
from client_execution.upsell.engine import UpsellEngine


def _item(**overrides: object) -> ClientExecutionInput:
    base: dict[str, object] = {"company_id": uuid4(), "company_name": "More Co", "won": True}
    base.update(overrides)
    return ClientExecutionInput.model_validate(base)


@pytest.mark.parametrize("service", list(UpsellService))
def test_all_upsell_services_enum(service: UpsellService) -> None:
    assert isinstance(service.value, str)
    assert service.value


def test_empty_upsell_without_signals() -> None:
    assert UpsellEngine().recommend(_item(upsell_signal=False)) == []


def test_support_stage_after_launch_flags() -> None:
    d = ClientExecutionPipeline().process(_item(in_support=True, launched=True))
    assert d.stage == ClientLifecycleStage.SUPPORT


def test_referral_beats_renewal() -> None:
    d = ClientExecutionPipeline().process(_item(referral_made=True, renewal_due=True))
    assert d.stage == ClientLifecycleStage.REFERRAL


def test_workspace_limits_lists() -> None:
    d = ClientExecutionPipeline().process(
        _item(
            requirements=[f"r{i}" for i in range(30)],
            deliverables=[f"d{i}" for i in range(30)],
            risks=[f"risk{i}" for i in range(20)],
            decision_makers=[{"name": f"n{i}"} for i in range(20)],
        )
    )
    assert len(d.workspace.requirements) <= 20
    assert len(d.workspace.deliverables) <= 20
    assert len(d.workspace.risks) <= 12
    assert len(d.workspace.decision_makers) <= 8


def test_delivery_fallback_from_deliverables() -> None:
    d = ClientExecutionPipeline().process(_item(deliverables=["Ship portal"], projects=[]))
    assert d.delivery_dashboard.todays_deliveries
    assert d.delivery_dashboard.todays_deliveries[0]["deliverable"] == "Ship portal"


def test_at_risk_from_health_status() -> None:
    d = ClientExecutionPipeline().process(
        _item(
            satisfaction=15,
            communication_score=15,
            delivery_progress=10,
            open_issues=8,
            risks=["a", "b", "c", "d", "e", "f"],
            projects=[],
        )
    )
    assert d.health.status == "at_risk"
    assert d.delivery_dashboard.at_risk_projects or d.founder_view.client_risks >= 1


@pytest.mark.parametrize(
    "flag",
    [
        "planning_complete",
        "design_complete",
        "development_active",
        "testing_active",
        "in_review",
        "launched",
        "in_support",
        "renewal_due",
        "referral_made",
        "lost_client",
        "archived",
    ],
)
def test_single_flag_stages(flag: str) -> None:
    d = ClientExecutionPipeline().process(_item(**{flag: True}))
    assert isinstance(d.stage, ClientLifecycleStage)


def test_evidence_chain_upsell_count() -> None:
    d = ClientExecutionPipeline().process(_item(hiring_signals=["hiring"], funding_signals=["raised series"]))
    assert any(e.startswith("upsells:") for e in d.evidence_chain)


def test_knowledge_search_case_insensitive() -> None:
    from client_execution.knowledge.engine import ClientKnowledgeBaseEngine

    recs = ClientKnowledgeBaseEngine().build(_item(requirements=["CRM Sync Layer"]))
    assert ClientKnowledgeBaseEngine().search(recs, "crm")
