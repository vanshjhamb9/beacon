from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

from revenue_optimization.cta_intelligence.engine import CTAIntelligenceEngine, FollowupIntelligenceEngine
from revenue_optimization.email_performance.engine import EmailPerformanceEngine, SubjectLineIntelligenceEngine
from revenue_optimization.industry_conversion.engine import (
    CaseStudyIntelligenceEngine,
    FounderPerformanceEngine,
    IndustryConversionEngine,
    OfferIntelligenceEngine,
)
from revenue_optimization.models.types import SCORING_VERSION, ROIPDecision, ROIPInput
from revenue_optimization.reply_intelligence.engine import (
    OptimizationRecommendationEngine,
    ReplyIntelligenceV2Engine,
    RevenueBenchmarkEngine,
    RevenueLearningEngine,
)


class RevenueOptimizationPipeline:
    """Compose-only Revenue Optimization Intelligence — evidence-driven, never auto-apply."""

    def __init__(self) -> None:
        self.email = EmailPerformanceEngine()
        self.subjects = SubjectLineIntelligenceEngine()
        self.ctas = CTAIntelligenceEngine()
        self.followup = FollowupIntelligenceEngine()
        self.industries = IndustryConversionEngine()
        self.founder = FounderPerformanceEngine()
        self.offers = OfferIntelligenceEngine()
        self.case_studies = CaseStudyIntelligenceEngine()
        self.replies = ReplyIntelligenceV2Engine()
        self.learning = RevenueLearningEngine()
        self.benchmarks = RevenueBenchmarkEngine()
        self.recommendations = OptimizationRecommendationEngine()

    def process(self, data: ROIPInput) -> ROIPDecision:
        now = data.now or datetime.now(UTC)
        events = list(data.events)
        email = self.email.analyze(events)
        subjects = self.subjects.rank(events)
        ctas = self.ctas.analyze(events)
        followup = self.followup.analyze(events)
        industries = self.industries.analyze(events)
        founder = self.founder.analyze(events)
        offers = self.offers.analyze(events)
        cases = self.case_studies.recommend(events, list(data.portfolio_assets))
        replies = self.replies.analyze(events)
        learning = self.learning.learn(events)
        benches = self.benchmarks.benchmark(events, list(data.previous_period_events))

        # channel preferences by industry for recommendations
        channel_by_industry: dict[str, str] = {}
        by_ind: dict[str, list] = {}
        for e in events:
            if e.industry:
                by_ind.setdefault(e.industry, []).append(e)
        for ind, items in by_ind.items():
            engaged = [e for e in items if e.replied or e.meeting_booked]
            if engaged:
                channel_by_industry[ind] = Counter(e.channel for e in engaged).most_common(1)[0][0]

        recs = self.recommendations.generate(
            followup_delay=followup.best_delay_days,
            industries=industries,
            offers=offers,
            followup_day=followup.best_day,
            channels_by_industry=channel_by_industry,
        )
        evidence = [
            f"scoring_version:{SCORING_VERSION}",
            "compose_only:true",
            "no_gpt:true",
            "never_auto_send:true",
            "never_auto_apply:true",
            f"events:{len(events)}",
            f"recommendations:{len(recs)}",
            "founder_approval:required",
        ]
        return ROIPDecision(
            scoring_version=SCORING_VERSION,
            email_metrics=email,
            subjects=subjects,
            ctas=ctas,
            followup=followup,
            industries=industries,
            founder=founder,
            offers=offers,
            case_studies=cases,
            replies=replies,
            learning=learning,
            benchmarks=benches,
            recommendations=recs,
            evidence_chain=evidence,
            evaluated_at=now,
        )
