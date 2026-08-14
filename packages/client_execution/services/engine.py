from __future__ import annotations

from client_execution.knowledge.engine import ClientKnowledgeBaseEngine
from client_execution.models.types import ClientExecutionDecision, ClientExecutionInput, KnowledgeRecord
from client_execution.pipelines.aep_pipeline import ClientExecutionPipeline


class ClientExecutionService:
    def __init__(self, pipeline: ClientExecutionPipeline | None = None) -> None:
        self.pipeline = pipeline or ClientExecutionPipeline()
        self.knowledge = ClientKnowledgeBaseEngine()

    def evaluate(self, data: ClientExecutionInput) -> ClientExecutionDecision:
        return self.pipeline.process(data)

    def evaluate_many(self, items: list[ClientExecutionInput]) -> list[ClientExecutionDecision]:
        return [self.evaluate(item) for item in items]

    def search_knowledge(self, records: list[KnowledgeRecord], query: str) -> list[KnowledgeRecord]:
        return self.knowledge.search(records, query)
