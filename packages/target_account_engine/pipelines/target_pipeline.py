from __future__ import annotations

from target_account_engine.budget.engine import BudgetEngine
from target_account_engine.buyer.accessibility import AccessibilityEngine
from target_account_engine.competition.engine import CompetitionEngine
from target_account_engine.fit.engine import FitEngine
from target_account_engine.hunter.mode import HunterMode
from target_account_engine.industry.defaults import default_icp_profiles
from target_account_engine.intent.engine import IntentEngine
from target_account_engine.models.types import (
    SCORING_VERSION,
    AccountTier,
    ICPProfile,
    TargetAccountDecision,
    TargetAccountInput,
)
from target_account_engine.recommendations.why_now import WhyNowEngine
from target_account_engine.scoring.engine import RevenueOpportunityScorer
from target_account_engine.urgency.engine import UrgencyEngine


class TargetAccountPipeline:
    """Master-brain pipeline: ICP match → multi-engine scores → revenue score → hunter."""

    def __init__(
        self,
        *,
        profiles: list[ICPProfile] | None = None,
        top_tier_threshold: float = 70.0,
        hunter_threshold: float = 75.0,
        mid_tier_threshold: float = 50.0,
    ) -> None:
        self.profiles = profiles or default_icp_profiles()
        self.fit = FitEngine()
        self.intent = IntentEngine()
        self.budget = BudgetEngine()
        self.urgency = UrgencyEngine()
        self.accessibility = AccessibilityEngine()
        self.competition = CompetitionEngine()
        self.scorer = RevenueOpportunityScorer(
            top_tier_threshold=top_tier_threshold,
            mid_tier_threshold=mid_tier_threshold,
        )
        self.why_now = WhyNowEngine()
        self.hunter = HunterMode(threshold=hunter_threshold)
        self.top_tier_threshold = top_tier_threshold

    def process(self, item: TargetAccountInput) -> TargetAccountDecision:
        fit_score, profile = self.fit.score(item, self.profiles)
        intent = self.intent.score(item)
        budget = self.budget.score(item)
        urgency = self.urgency.score(item)
        accessibility = self.accessibility.score(item)
        competition = self.competition.score(item)

        revenue_score, breakdown, tier = self.scorer.combine(
            {
                "fit": fit_score.score,
                "intent": intent.score,
                "budget": budget.score,
                "urgency": urgency.score,
                "accessibility": accessibility.score,
                "competition": competition.score,
            },
            explanations={
                "fit": fit_score.explanation,
                "intent": intent.explanation,
                "budget": budget.explanation,
                "urgency": urgency.explanation,
                "accessibility": accessibility.explanation,
                "competition": competition.explanation,
            },
            evidence={
                "fit": fit_score.evidence,
                "intent": intent.evidence,
                "budget": budget.evidence,
                "urgency": urgency.evidence,
                "accessibility": accessibility.evidence,
                "competition": competition.evidence,
            },
        )

        # Negative ICP hard exclude
        if profile is None and fit_score.score < 25:
            tier = AccountTier.EXCLUDED

        service = profile.service_match if profile else None
        why = self.why_now.generate(
            item,
            profile=profile,
            fit=fit_score,
            intent=intent,
            urgency=urgency,
            service_match=service,
        )
        hunter_job = self.hunter.plan(item, revenue_score=revenue_score)
        buying = list(dict.fromkeys(intent.evidence + urgency.evidence))[:20]
        negative = [
            ev
            for ev in fit_score.evidence
            if "negative" in ev.lower()
        ]
        evidence_chain = list(
            dict.fromkeys(
                fit_score.evidence
                + intent.evidence
                + budget.evidence
                + urgency.evidence
                + accessibility.evidence
                + competition.evidence
            )
        )[:40]

        return TargetAccountDecision(
            company_id=item.company_id,
            company_name=item.company_name,
            opportunity_id=item.opportunity_id,
            matched_icp_key=profile.key if profile else None,
            matched_icp_name=profile.name if profile else None,
            service_match=service,
            fit=fit_score,
            intent=intent,
            budget=budget,
            urgency=urgency,
            accessibility=accessibility,
            competition=competition,
            revenue_opportunity_score=revenue_score,
            tier=tier,
            why_now=why,
            buying_signals=buying,
            negative_signals=negative,
            score_breakdown=breakdown,
            hunter_triggered=hunter_job is not None,
            hunter_tasks=list(hunter_job.tasks) if hunter_job else [],
            proceed_to_copilot=tier == AccountTier.TOP,
            scoring_version=SCORING_VERSION,
            explanations={
                "industry": item.industry or "unknown",
                "country": item.country or "unknown",
                "why_now": why,
                "tier": tier.value,
            },
            evidence_chain=evidence_chain,
        )
