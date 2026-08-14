from __future__ import annotations

from datetime import UTC, datetime

from client_execution.dashboard.delivery import DeliveryDashboardEngine
from client_execution.dashboard.founder import FounderExecutiveEngine
from client_execution.handoff.engine import ProjectHandoffEngine
from client_execution.health.engine import ClientHealthEngine
from client_execution.knowledge.engine import ClientKnowledgeBaseEngine
from client_execution.lifecycle.engine import ClientLifecycleEngine
from client_execution.models.types import SCORING_VERSION, ClientExecutionDecision, ClientExecutionInput
from client_execution.upsell.engine import UpsellEngine
from client_execution.workspace.engine import ClientWorkspaceEngine


class ClientExecutionPipeline:
    """Compose-only Agency Execution Platform — Sales → Delivery transition."""

    def __init__(self) -> None:
        self.lifecycle = ClientLifecycleEngine()
        self.workspace = ClientWorkspaceEngine()
        self.handoff = ProjectHandoffEngine()
        self.knowledge = ClientKnowledgeBaseEngine()
        self.upsell = UpsellEngine()
        self.health = ClientHealthEngine()
        self.delivery = DeliveryDashboardEngine()
        self.founder = FounderExecutiveEngine()

    def process(self, item: ClientExecutionInput) -> ClientExecutionDecision:
        stage = self.lifecycle.infer_stage(item)
        workspace = self.workspace.build(item, stage=stage)
        handoff = self.handoff.generate(item, stage=stage)
        knowledge = self.knowledge.build(item)
        upsells = self.upsell.recommend(item)
        health = self.health.score(item, stage=stage)
        delivery = self.delivery.build(item, health=health, upsells=upsells)
        founder = self.founder.build(item, health=health, upsells=upsells)
        evidence = [
            f"scoring_version:{SCORING_VERSION}",
            f"stage:{stage.value}",
            f"health:{health.status}",
            f"upsells:{len(upsells)}",
            "compose_only:true",
            "no_gpt:true",
            "founder_approval_upsells:true",
        ]
        return ClientExecutionDecision(
            company_id=item.company_id,
            company_name=item.company_name,
            stage=stage,
            workspace=workspace,
            handoff=handoff,
            knowledge=knowledge,
            upsells=upsells,
            health=health,
            delivery_dashboard=delivery,
            founder_view=founder,
            scoring_version=SCORING_VERSION,
            evidence_chain=evidence,
            evaluated_at=item.now or datetime.now(UTC),
        )
