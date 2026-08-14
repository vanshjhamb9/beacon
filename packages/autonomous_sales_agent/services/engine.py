from __future__ import annotations

from autonomous_sales_agent.models.types import (
    AutonomousSalesAgentDecision,
    AutonomousSalesAgentInput,
    SalesWorkflowStage,
    WorkflowTransition,
)
from autonomous_sales_agent.pipelines.asa_pipeline import AutonomousSalesAgentPipeline
from autonomous_sales_agent.workflow.engine import SalesWorkflowEngine


class AutonomousSalesAgentService:
    def __init__(self, pipeline: AutonomousSalesAgentPipeline | None = None) -> None:
        self.pipeline = pipeline or AutonomousSalesAgentPipeline()
        self.workflow = SalesWorkflowEngine()

    def evaluate(self, data: AutonomousSalesAgentInput) -> AutonomousSalesAgentDecision:
        return self.pipeline.process(data)

    def evaluate_many(self, items: list[AutonomousSalesAgentInput]) -> list[AutonomousSalesAgentDecision]:
        return [self.evaluate(item) for item in items]

    def transition(
        self,
        current: SalesWorkflowStage,
        target: SalesWorkflowStage,
        *,
        reason: str,
        evidence: list[str] | None = None,
        actor: str = "system",
        next_action: str = "continue",
    ) -> WorkflowTransition:
        return self.workflow.transition(
            current,
            target,
            reason=reason,
            evidence=evidence,
            actor=actor,
            next_action=next_action,
        )
