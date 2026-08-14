from __future__ import annotations

from autonomous_sales_agent.models.types import AutonomousSalesAgentDecision


def decision_to_api_dict(decision: AutonomousSalesAgentDecision) -> dict:
    """Serialize ASA decision for HTTP payloads."""
    return decision.model_dump(mode="json")
