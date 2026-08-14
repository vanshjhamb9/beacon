from __future__ import annotations

from founder_os.analytics.tracker import AnalyticsTracker
from founder_os.models.types import AnalyticsEvent, AnalyticsEventType, FounderOsDecision, FounderOsInput
from founder_os.pipelines.founder_os_pipeline import FounderOsPipeline


class FounderOsService:
    def __init__(self, pipeline: FounderOsPipeline | None = None) -> None:
        self.pipeline = pipeline or FounderOsPipeline()
        self.analytics = AnalyticsTracker()

    def evaluate(self, data: FounderOsInput) -> FounderOsDecision:
        return self.pipeline.process(data)

    def track(self, **kwargs) -> AnalyticsEvent:
        return self.analytics.track(**kwargs)

    def track_brief_view(self, *, actor: str = "founder") -> AnalyticsEvent:
        return self.analytics.track(
            event_type=AnalyticsEventType.BRIEF_VIEW,
            action="view_daily_brief",
            actor=actor,
        )
