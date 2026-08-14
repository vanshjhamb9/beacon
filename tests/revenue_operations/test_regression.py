from pathlib import Path
from uuid import uuid4

from revenue_operations import RevenueOperationsPipeline
from revenue_operations.models.types import OpportunitySignal, RevenueOperationsInput


FORBIDDEN = ("openai", "gpt-4", "ChatCompletion", "langchain")


def test_package_has_no_gpt_dependency() -> None:
    root = Path(__file__).resolve().parents[2] / "packages" / "revenue_operations"
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for token in FORBIDDEN:
            assert token not in text, f"{path} contains {token}"


def test_recommendations_never_auto_apply() -> None:
    d = RevenueOperationsPipeline().process(
        RevenueOperationsInput(
            opportunities=[
                OpportunitySignal(company_name="A", probability=80, pipeline_value=30000, industry="SaaS", service="AI Automation", won=True)
            ]
        )
    )
    assert all(r.modifies_production is False for r in d.learning.recommendations)
    assert all(r.status.value == "pending_approval" for r in d.learning.recommendations)


def test_compose_only_marker() -> None:
    d = RevenueOperationsPipeline().process(
        RevenueOperationsInput(opportunities=[OpportunitySignal(company_name="X", company_id=uuid4())])
    )
    assert "compose_only:true" in d.evidence_chain
