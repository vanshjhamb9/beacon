from data_verification.models.types import VerificationInput, VerificationResult
from data_verification.pipelines.verification_pipeline import VerificationPipeline


class VerificationService:
    def __init__(self, pipeline: VerificationPipeline | None = None) -> None:
        self.pipeline = pipeline or VerificationPipeline()

    def verify(self, item: VerificationInput) -> VerificationResult:
        return self.pipeline.process(item)
