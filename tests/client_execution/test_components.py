from uuid import uuid4

from client_execution import ClientExecutionPipeline, ClientExecutionService
from client_execution.dashboard.delivery import DeliveryDashboardEngine
from client_execution.dashboard.founder import FounderExecutiveEngine
from client_execution.handoff.engine import ProjectHandoffEngine
from client_execution.health.engine import ClientHealthEngine
from client_execution.knowledge.engine import ClientKnowledgeBaseEngine
from client_execution.lifecycle.engine import ClientLifecycleEngine
from client_execution.models.types import (
    ClientExecutionInput,
    ClientLifecycleStage,
    ClientProjectSignal,
    UpsellService,
)
from client_execution.upsell.engine import UpsellEngine
from client_execution.workspace.engine import ClientWorkspaceEngine


def _item(**overrides: object) -> ClientExecutionInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Component Co",
        "won": True,
        "contract_value": 25000,
        "services_purchased": ["Custom SaaS"],
    }
    payload.update(overrides)
    return ClientExecutionInput.model_validate(payload)


def test_workspace_fields() -> None:
    stage = ClientLifecycleStage.DEVELOPMENT
    ws = ClientWorkspaceEngine().build(_item(development_active=True, primary_contacts=[{"name": "A"}]), stage=stage)
    assert ws.company == "Component Co"
    assert ws.contract_value == 25000
    assert ws.invoices_status == "placeholder"
    assert ws.services_purchased
    assert ws.evidence


def test_handoff_fields() -> None:
    h = ProjectHandoffEngine().generate(
        _item(
            pain_points=["Slow CRM"],
            business_goals=["Scale"],
            known_objections=["Budget"],
            sales_notes=["Hot"],
            founder_notes=["Strategic"],
            meeting_history=[{"summary": "Discovery call"}],
        ),
        stage=ClientLifecycleStage.WON,
    )
    assert "Component Co" in h.client_dossier
    assert h.meeting_summary == "Discovery call"
    assert "Slow CRM" in h.pain_points
    assert "Budget" in h.known_objections
    assert h.sales_notes and h.founder_notes


def test_knowledge_append_only_types() -> None:
    kb = ClientKnowledgeBaseEngine()
    records = kb.build(
        _item(
            requirements=["Req1"],
            meeting_history=[{"summary": "Kickoff"}],
            architecture_notes=["Hexagonal"],
            documents=["SOW"],
            revisions=["v2"],
            feedback=["Nice"],
            approvals=["Founder OK"],
            founder_notes=["Watch closely"],
        )
    )
    types = {r.record_type for r in records}
    assert {"requirement", "meeting_note", "architecture", "document", "revision", "feedback", "approval"} <= types
    assert all("append_only:true" in r.evidence for r in records)


def test_knowledge_search() -> None:
    svc = ClientExecutionService()
    records = ClientKnowledgeBaseEngine().build(_item(requirements=["CRM sync", "Mobile app"]))
    hits = svc.search_knowledge(records, "mobile")
    assert len(hits) == 1
    assert "mobile" in hits[0].searchable_text


def test_upsell_founder_gate() -> None:
    ups = UpsellEngine().recommend(_item(hiring_signals=["hiring engineers"], funding_signals=["series a raised"]))
    assert ups
    assert all(u.requires_founder_approval for u in ups)
    assert all(u.modifies_production is False for u in ups)
    assert {u.service for u in ups} & {UpsellService.INTERNAL_TOOLS, UpsellService.CUSTOM_SAAS}


def test_upsell_flag_without_blob() -> None:
    ups = UpsellEngine().recommend(_item(upsell_signal=True))
    assert any(u.service == UpsellService.AI_AUTOMATION for u in ups)


def test_health_at_risk() -> None:
    h = ClientHealthEngine().score(
        _item(satisfaction=20, open_issues=5, risks=["delay", "scope", "budget", "comm"], delay_days=10, communication_score=20),
        stage=ClientLifecycleStage.DEVELOPMENT,
    )
    assert h.status in {"at_risk", "watch"}
    assert h.risk_score > 0
    assert 0 <= h.renewal_probability <= 100


def test_health_lost() -> None:
    h = ClientHealthEngine().score(_item(lost_client=True), stage=ClientLifecycleStage.LOST_CLIENT)
    assert h.status == "lost"
    assert h.renewal_probability == 5.0


def test_delivery_dashboard_sections() -> None:
    health = ClientHealthEngine().score(_item(), stage=ClientLifecycleStage.WON)
    dash = DeliveryDashboardEngine().build(
        _item(
            projects=[
                ClientProjectSignal(name="A", blocked=True, due_today=True, deliverable="X", milestone="M1"),
                ClientProjectSignal(name="B", at_risk=True, milestone="M2"),
            ],
            days_to_renewal=30,
            renewal_date="2026-09-01",
            hiring_signals=["hiring"],
        ),
        health=health,
        upsells=UpsellEngine().recommend(_item(hiring_signals=["hiring"])),
    )
    assert dash.todays_deliveries
    assert dash.upcoming_milestones
    assert dash.blocked_projects
    assert dash.renewals
    assert dash.client_health


def test_founder_view_placeholders() -> None:
    health = ClientHealthEngine().score(_item(open_issues=4), stage=ClientLifecycleStage.SUPPORT)
    fv = FounderExecutiveEngine().build(
        _item(revenue_delivered=12000, renewal_due=True, open_issues=4),
        health=health,
        upsells=[],
    )
    assert fv.pending_payments == "placeholder"
    assert fv.team_capacity == "placeholder"
    assert fv.revenue_delivered == 12000
    assert fv.renewals == 1
    assert fv.client_risks >= 1


def test_lifecycle_priority_archive_over_lost() -> None:
    assert ClientLifecycleEngine().infer_stage(_item(archived=True, lost_client=True)) == ClientLifecycleStage.ARCHIVE


def test_pipeline_compose_only_version() -> None:
    d = ClientExecutionPipeline().process(_item())
    assert d.scoring_version == "aep-v1"
    assert d.workspace.evidence
    assert d.health.evidence
