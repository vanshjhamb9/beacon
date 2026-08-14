from pathlib import Path
from uuid import uuid4

from account_journey import AccountJourneyPipeline
from account_journey.models.types import AccountJourneyInput


FORBIDDEN = ("openai", "gpt-4", "ChatCompletion", "langchain")


def test_no_gpt_dependency() -> None:
    root = Path(__file__).resolve().parents[2] / "packages" / "account_journey"
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for token in FORBIDDEN:
            assert token not in text


def test_founder_approval_on_outbound() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="Gate", emailed=True, no_reply_days=2)
    )
    if d.follow_up.channel.value != "wait":
        assert d.follow_up.requires_founder_approval is True


def test_compose_only_marker() -> None:
    d = AccountJourneyPipeline().process(AccountJourneyInput(company_id=uuid4(), company_name="X"))
    assert "compose_only:true" in d.evidence_chain
    assert "no_gpt:true" in d.evidence_chain
