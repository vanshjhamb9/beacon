from pathlib import Path
from uuid import uuid4

from client_execution import ClientExecutionPipeline
from client_execution.models.types import ClientExecutionInput, ClientProjectSignal


def test_delivery_dashboard_keys() -> None:
    d = ClientExecutionPipeline().process(
        ClientExecutionInput(
            company_id=uuid4(),
            company_name="Dash Co",
            won=True,
            projects=[ClientProjectSignal(name="Web", due_today=True, deliverable="Home", milestone="Launch")],
            hiring_signals=["hiring"],
        )
    )
    dash = d.delivery_dashboard.model_dump()
    for key in [
        "todays_deliveries",
        "upcoming_milestones",
        "blocked_projects",
        "at_risk_projects",
        "client_health",
        "renewals",
        "upsells",
    ]:
        assert key in dash


def test_founder_executive_keys() -> None:
    d = ClientExecutionPipeline().process(
        ClientExecutionInput(company_id=uuid4(), company_name="Founder Co", won=True, contract_value=99000)
    )
    fv = d.founder_view.model_dump()
    for key in [
        "revenue_closed",
        "projects_running",
        "revenue_delivered",
        "pending_payments",
        "renewals",
        "upsells",
        "client_risks",
        "team_capacity",
    ]:
        assert key in fv


def test_dashboard_workspace_page_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    page = root / "apps" / "dashboard" / "app" / "(workspace)" / "client-execution" / "page.tsx"
    feature = root / "apps" / "dashboard" / "features" / "aep" / "client-execution-workspace.tsx"
    assert page.exists()
    assert feature.exists()
    text = feature.read_text(encoding="utf-8")
    assert "Agency Execution Platform" in text
    assert "Founder View" in text
    assert "aepDashboard" in text or "beaconApi.aep" in text
