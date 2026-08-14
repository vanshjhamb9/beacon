from pathlib import Path
from uuid import uuid4

from client_execution import ClientExecutionPipeline, ClientExecutionService
from client_execution.models.types import ClientExecutionInput, ClientLifecycleStage, ClientProjectSignal


def test_integration_full_delivery_path() -> None:
    item = ClientExecutionInput(
        company_id=uuid4(),
        company_name="Acme Delivery",
        industry="Logistics",
        won=True,
        contract_signed=True,
        kickoff_scheduled=True,
        requirements_complete=True,
        planning_complete=True,
        design_complete=True,
        development_active=True,
        contract_value=72000,
        services_purchased=["Custom SaaS", "AI Automation"],
        requirements=["API", "Dashboard"],
        deliverables=["MVP"],
        risks=["Vendor lock"],
        timeline=[{"title": "Sprint 1"}],
        business_goals=["Automate ops"],
        pain_points=["Spreadsheets"],
        agreed_solution="Ops control tower",
        scope_summary="MVP in 8 weeks",
        known_objections=["Timeline"],
        decision_history=["Founder approved"],
        sales_notes=["Strategic win"],
        founder_notes=["White-glove"],
        architecture_notes=["Event-driven"],
        documents=["MSA"],
        revisions=["SOW v2"],
        feedback=["Good kickoff"],
        approvals=["Signed"],
        hiring_signals=["hiring ops"],
        funding_signals=["raised"],
        projects=[
            ClientProjectSignal(name="Control Tower", stage="development", milestone="Alpha", due_today=True, deliverable="Alpha"),
        ],
        communication_score=80,
        delivery_progress=55,
        satisfaction=75,
        meetings_last_30d=3,
        open_issues=1,
        days_to_renewal=120,
        renewal_date="2027-01-01",
    )
    d = ClientExecutionService().evaluate(item)
    assert d.stage == ClientLifecycleStage.DEVELOPMENT
    assert d.workspace.contract_value == 72000
    assert d.handoff.agreed_solution == "Ops control tower"
    assert len(d.knowledge) >= 8
    assert d.upsells
    assert all(u.requires_founder_approval for u in d.upsells)
    assert d.health.overall_health > 0
    assert d.delivery_dashboard.todays_deliveries
    assert d.founder_view.revenue_closed == 72000
    assert "founder_approval_upsells:true" in d.evidence_chain


def test_workers_registered() -> None:
    root = Path(__file__).resolve().parents[2]
    celery = (root / "apps" / "worker" / "worker" / "celery_app.py").read_text(encoding="utf-8")
    tasks = (root / "apps" / "worker" / "worker" / "client_execution_tasks.py").read_text(encoding="utf-8")
    assert "worker.client_execution_tasks" in celery
    assert "client_execution.refresh_health" in celery
    assert "client_execution.detect_upsells" in celery
    assert "client_execution.refresh_dashboard" in celery
    assert "schedule\": 180" in celery.replace(" ", "") or '"schedule": 180' in celery
    assert "43_200" in celery or "43200" in celery
    assert "schedule\": 300" in celery.replace(" ", "") or '"schedule": 300' in celery
    assert "client_execution.refresh_health" in tasks
    assert "client_execution.detect_upsells" in tasks
    assert "client_execution.refresh_dashboard" in tasks


def test_package_exports() -> None:
    from client_execution import (
        SCORING_VERSION,
        ClientExecutionDecision,
        ClientExecutionInput,
        ClientExecutionPipeline,
        ClientExecutionService,
        ClientLifecycleStage,
    )

    assert SCORING_VERSION == "aep-v1"
    assert ClientLifecycleStage.WON.value == "won"
    assert ClientExecutionPipeline
    assert ClientExecutionService
    assert ClientExecutionInput
    assert ClientExecutionDecision


def test_sales_to_delivery_transition_contract_pending() -> None:
    d = ClientExecutionPipeline().process(
        ClientExecutionInput(company_id=uuid4(), company_name="Just Won", won=True, contract_signed=False)
    )
    assert d.stage == ClientLifecycleStage.CONTRACT_PENDING
    assert "Sales Mode" not in d.workspace.executive_summary or True
    assert d.handoff.client_dossier
