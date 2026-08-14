from data_acquisition.pipelines.acquisition_analytics import AcquisitionAnalyticsPipeline


class AcquisitionAnalyticsService:
    def __init__(self, pipeline: AcquisitionAnalyticsPipeline | None = None) -> None:
        self.pipeline = pipeline or AcquisitionAnalyticsPipeline()
