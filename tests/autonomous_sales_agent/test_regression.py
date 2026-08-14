"""Regression: ASA must not depend on GPT and must keep founder-only focus contract."""

from pathlib import Path

from autonomous_sales_agent import AutonomousSalesAgentPipeline
from autonomous_sales_agent.models.types import AutonomousSalesAgentInput
from uuid import uuid4


FORBIDDEN = ("openai", "gpt-4", "ChatCompletion", "langchain")


def test_package_has_no_gpt_dependency_strings() -> None:
    root = Path(__file__).resolve().parents[2] / "packages" / "autonomous_sales_agent"
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for token in FORBIDDEN:
            assert token.lower() not in text, f"{path} contains {token}"


def test_wait_action_protects_founder_focus() -> None:
    d = AutonomousSalesAgentPipeline().process(
        AutonomousSalesAgentInput(
            company_id=uuid4(),
            company_name="Quiet Co",
            email_sent=True,
            days_since_last_touch=0,
            has_decision_makers=True,
            decision_makers=[{"name": "A"}],
            pains=["ops"],
            priority_grade="B",
            probability=45,
        )
    )
    assert d.next_best_action.action.value == "wait"
    assert d.work_queue == [] or all(w.kind in {
        "meet_today",
        "proposal_pending",
        "negotiation",
        "needs_approval",
        "high_intent_reply",
        "urgent_follow_up",
    } for w in d.work_queue)
