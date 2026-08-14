from sales_copilot.models.types import SalesCopilotInput, SalesIntelligencePackage
from sales_copilot.pipelines.copilot_pipeline import SalesCopilotPipeline


class SalesCopilotService:
    def __init__(self, pipeline: SalesCopilotPipeline | None = None) -> None:
        self.pipeline = pipeline or SalesCopilotPipeline()

    def generate(self, item: SalesCopilotInput, *, version: int = 1) -> SalesIntelligencePackage:
        return self.pipeline.process(item, version=version)
