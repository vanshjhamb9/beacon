from uuid import uuid4

from client_execution.handoff.engine import ProjectHandoffEngine
from client_execution.knowledge.engine import ClientKnowledgeBaseEngine
from client_execution.models.types import ClientExecutionInput, ClientLifecycleStage


def _item(**overrides: object) -> ClientExecutionInput:
    base: dict[str, object] = {"company_id": uuid4(), "company_name": "Handoff Co", "won": True, "industry": "Fintech"}
    base.update(overrides)
    return ClientExecutionInput.model_validate(base)


def test_handoff_defaults() -> None:
    h = ProjectHandoffEngine().generate(_item(), stage=ClientLifecycleStage.WON)
    assert h.business_goals
    assert h.pain_points
    assert h.timeline
    assert h.decision_history
    assert "handoff:auto" in h.evidence


def test_handoff_uses_scope_and_solution() -> None:
    h = ProjectHandoffEngine().generate(
        _item(agreed_solution="Build analytics suite", scope_summary="Phase 1 analytics", timeline=[{"title": "Phase 1"}]),
        stage=ClientLifecycleStage.PLANNING,
    )
    assert h.agreed_solution == "Build analytics suite"
    assert h.scope_summary == "Phase 1 analytics"
    assert "Phase 1" in h.timeline


def test_knowledge_empty_query_returns_all() -> None:
    kb = ClientKnowledgeBaseEngine()
    records = kb.build(_item(requirements=["A", "B"]))
    assert len(kb.search(records, "  ")) == len(records)


def test_knowledge_search_miss() -> None:
    kb = ClientKnowledgeBaseEngine()
    records = kb.build(_item(requirements=["CRM"]))
    assert kb.search(records, "blockchain") == []


def test_knowledge_title_truncation() -> None:
    long = "x" * 500
    rec = ClientKnowledgeBaseEngine().build(_item(requirements=[long]))[0]
    assert len(rec.title) <= 200
    assert len(rec.body) <= 2000


def test_handoff_string_meeting_history() -> None:
    h = ProjectHandoffEngine().generate(
        _item(meeting_history=[]),
        stage=ClientLifecycleStage.KICKOFF_SCHEDULED,
    )
    assert "Kickoff" in h.meeting_summary or "sales handoff" in h.meeting_summary.lower()
