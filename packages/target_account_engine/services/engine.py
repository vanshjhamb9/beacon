from __future__ import annotations

from target_account_engine.analytics.summary import TargetAccountAnalytics
from target_account_engine.hunter.mode import HunterMode
from target_account_engine.industry.defaults import default_icp_profiles
from target_account_engine.models.types import (
    HunterJob,
    ICPProfile,
    ImprovementRecommendation,
    TargetAccountDecision,
    TargetAccountInput,
)
from target_account_engine.pipelines.target_pipeline import TargetAccountPipeline
from target_account_engine.recommendations.improvements import ImprovementAdvisor


class TargetAccountEngineService:
    def __init__(
        self,
        *,
        profiles: list[ICPProfile] | None = None,
        pipeline: TargetAccountPipeline | None = None,
        top_tier_threshold: float = 70.0,
        hunter_threshold: float = 75.0,
    ) -> None:
        self.profiles = list(profiles or default_icp_profiles())
        self.pipeline = pipeline or TargetAccountPipeline(
            profiles=self.profiles,
            top_tier_threshold=top_tier_threshold,
            hunter_threshold=hunter_threshold,
        )
        self.hunter = HunterMode(threshold=hunter_threshold)
        self.analytics = TargetAccountAnalytics()
        self.improvements = ImprovementAdvisor()

    def evaluate(self, item: TargetAccountInput) -> TargetAccountDecision:
        # Keep pipeline profiles in sync with service profile mutations
        self.pipeline.profiles = self.profiles
        return self.pipeline.process(item)

    def list_icps(self) -> list[ICPProfile]:
        return list(self.profiles)

    def upsert_icp(self, profile: ICPProfile) -> ICPProfile:
        self.profiles = [p for p in self.profiles if p.key != profile.key] + [profile]
        self.profiles.sort(key=lambda p: p.priority)
        self.pipeline.profiles = self.profiles
        return profile

    def delete_icp(self, key: str) -> bool:
        before = len(self.profiles)
        self.profiles = [p for p in self.profiles if p.key != key]
        self.pipeline.profiles = self.profiles
        return len(self.profiles) < before

    def start_hunter(self, item: TargetAccountInput, *, revenue_score: float) -> HunterJob | None:
        job = self.hunter.plan(item, revenue_score=revenue_score)
        if job is None:
            return None
        return self.hunter.simulate_run(job, item)

    def recommend_improvements(
        self, decision: TargetAccountDecision, *, outcome: str, notes: str | None = None
    ) -> list[ImprovementRecommendation]:
        return self.improvements.from_outcome(decision, outcome=outcome, notes=notes)

    def summarize(self, decisions: list[TargetAccountDecision]) -> dict:
        return self.analytics.summarize(decisions)
