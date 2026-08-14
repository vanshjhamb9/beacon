from __future__ import annotations

from production_validation.models.types import ProductionValidationDecision, ProductionValidationInput
from production_validation.pipelines.validation_pipeline import ProductionValidationPipeline
from production_validation.reporting.playbooks import PlaybookEngine
from production_validation.validators.engine import LeadQualityValidator


class ProductionValidationService:
    def __init__(self, pipeline: ProductionValidationPipeline | None = None) -> None:
        self.pipeline = pipeline or ProductionValidationPipeline()
        self.leads = LeadQualityValidator()
        self.playbooks = PlaybookEngine()

    def evaluate(self, data: ProductionValidationInput) -> ProductionValidationDecision:
        return self.pipeline.process(data)

    def score_lead(self, data: ProductionValidationInput):
        return self.leads.score(data)

    def list_playbooks(self):
        return self.playbooks.all()
