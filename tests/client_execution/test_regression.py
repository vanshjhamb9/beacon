from pathlib import Path
from uuid import uuid4

from client_execution import ClientExecutionPipeline
from client_execution.models.types import ClientExecutionInput


def test_no_gpt_dependency_in_package() -> None:
    root = Path(__file__).resolve().parents[2] / "packages" / "client_execution"
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "openai" not in text.lower()
        assert "chatgpt" not in text.lower()
        assert "gpt-4" not in text.lower()


def test_compose_only_marker() -> None:
    d = ClientExecutionPipeline().process(ClientExecutionInput(company_id=uuid4(), company_name="R", won=True))
    assert "compose_only:true" in d.evidence_chain


def test_sidebar_and_ci_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    sidebar = (root / "apps" / "dashboard" / "components" / "layout" / "sidebar.tsx").read_text(encoding="utf-8")
    ci = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    routes = (root / "apps" / "api" / "app" / "api" / "routes" / "__init__.py").read_text(encoding="utf-8")
    assert "/client-execution" in sidebar
    assert "Client Delivery" in sidebar
    assert "tests/client_execution" in ci
    assert "client_execution_router" in routes


def test_docs_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "docs" / "client-execution.md").exists()
    assert (root / "docs" / "sprint-25-engineering-report.md").exists()
