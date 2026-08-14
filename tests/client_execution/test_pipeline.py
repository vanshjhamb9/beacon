from uuid import uuid4

from client_execution import SCORING_VERSION, ClientExecutionInput, ClientExecutionPipeline, ClientExecutionService
from client_execution.models.types import ClientLifecycleStage, ClientProjectSignal


def _item(**overrides: object) -> ClientExecutionInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Northwind Agency Client",
        "industry": "SaaS",
        "won": True,
        "contract_value": 48000,
        "services_purchased": ["AI Automation"],
        "requirements": ["Automate lead intake"],
        "deliverables": ["Intake bot"],
        "pain_points": ["Manual ops"],
        "business_goals": ["Cut ops cost 30%"],
    }
    payload.update(overrides)
    return ClientExecutionInput.model_validate(payload)


def test_pipeline_deterministic() -> None:
    item = _item(kickoff_scheduled=True, requirements=["A"], hiring_signals=["hiring engineers"])
    a = ClientExecutionPipeline().process(item)
    b = ClientExecutionPipeline().process(item)
    assert a.stage == b.stage
    assert a.health.overall_health == b.health.overall_health
    assert a.workspace.contract_value == b.workspace.contract_value
    assert [u.recommendation_id for u in a.upsells] == [u.recommendation_id for u in b.upsells]


def test_pipeline_evidence_backed() -> None:
    d = ClientExecutionPipeline().process(_item())
    assert any(e.startswith("scoring_version:") for e in d.evidence_chain)
    assert "compose_only:true" in d.evidence_chain
    assert "no_gpt:true" in d.evidence_chain
    assert d.scoring_version == SCORING_VERSION == "aep-v1"


def test_service_evaluate_many() -> None:
    svc = ClientExecutionService()
    out = svc.evaluate_many([_item(company_name=f"C{i}") for i in range(5)])
    assert len(out) == 5
    assert all(x.stage == ClientLifecycleStage.WON or x.stage == ClientLifecycleStage.CONTRACT_PENDING for x in out)


def test_pipeline_handoff_and_workspace() -> None:
    d = ClientExecutionPipeline().process(
        _item(
            contract_signed=True,
            kickoff_scheduled=True,
            agreed_solution="Build CRM automation",
            founder_notes=["Priority account"],
            decision_makers=[{"name": "Sam", "title": "CEO"}],
        )
    )
    assert "Northwind" in d.workspace.executive_summary
    assert d.workspace.invoices_status == "placeholder"
    assert "CRM" in d.handoff.agreed_solution or "Automate" in d.handoff.scope_summary or d.handoff.client_dossier
    assert d.handoff.founder_notes


def test_pipeline_delivery_and_founder() -> None:
    d = ClientExecutionPipeline().process(
        _item(
            launched=True,
            projects=[
                ClientProjectSignal(name="Portal", blocked=True, at_risk=True, due_today=True, milestone="UAT", deliverable="Portal v1"),
            ],
            renewal_due=True,
            hiring_signals=["hiring"],
        )
    )
    assert d.delivery_dashboard.todays_deliveries
    assert d.delivery_dashboard.blocked_projects
    assert d.founder_view.pending_payments == "placeholder"
    assert d.founder_view.team_capacity == "placeholder"
    assert d.founder_view.revenue_closed == 48000
