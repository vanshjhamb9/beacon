from __future__ import annotations

from autonomous_sales_agent.models.types import AutonomousSalesAgentDecision


class InMemoryAsaRepository:
    """Append-only in-memory store for unit tests / local compose."""

    def __init__(self) -> None:
        self._runs: list[AutonomousSalesAgentDecision] = []
        self._timeline: list[dict[str, object]] = []
        self._transitions: list[dict[str, object]] = []

    def append_decision(self, decision: AutonomousSalesAgentDecision) -> None:
        self._runs.append(decision)
        for t in decision.transitions:
            self._transitions.append(t.model_dump(mode="json"))
        for e in decision.timeline:
            self._timeline.append(e.model_dump(mode="json"))

    def latest(self, company_id: object) -> AutonomousSalesAgentDecision | None:
        for d in reversed(self._runs):
            if d.company_id == company_id:
                return d
        return None

    def all_runs(self) -> list[AutonomousSalesAgentDecision]:
        return list(self._runs)

    def timeline_events(self) -> list[dict[str, object]]:
        return list(self._timeline)

    def transitions(self) -> list[dict[str, object]]:
        return list(self._transitions)
