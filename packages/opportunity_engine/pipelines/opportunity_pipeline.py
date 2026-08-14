from opportunity_engine.conflict_resolution.engine import ConflictResolver
from opportunity_engine.lifecycle.engine import LifecycleEngine
from opportunity_engine.models.types import (
    CompanyOpportunityInput,
    OpportunityDecision,
    OpportunityDelta,
    OpportunityEvidenceItem,
)
from opportunity_engine.recommendations.engine import RecommendationEngine
from opportunity_engine.scoring.engine import OpportunityScorer
from opportunity_engine.timing.timer import OpportunityTimer


class OpportunityPipeline:
    def __init__(
        self,
        *,
        scorer: OpportunityScorer | None = None,
        conflict_resolver: ConflictResolver | None = None,
        lifecycle: LifecycleEngine | None = None,
        recommendations: RecommendationEngine | None = None,
        timer: OpportunityTimer | None = None,
    ) -> None:
        self.scorer = scorer or OpportunityScorer()
        self.conflict_resolver = conflict_resolver or ConflictResolver()
        self.lifecycle = lifecycle or LifecycleEngine()
        self.recommendations = recommendations or RecommendationEngine()
        self.timer = timer or OpportunityTimer()

    def process(self, item: CompanyOpportunityInput) -> OpportunityDecision:
        scored, scoring_latency_ms = self.timer.measure(lambda: self.scorer.score(item))
        conflicts = self.conflict_resolver.resolve(item.evidence)
        conflict_penalty = min(35.0, sum(conflict.severity for conflict in conflicts) * 0.15)
        opportunity_score = max(0.0, float(scored["opportunity_score"]) - conflict_penalty)
        status, decision_latency_ms = self.timer.measure(
            lambda: self.lifecycle.determine(
                opportunity_score=opportunity_score,
                confidence_score=float(scored["confidence_score"]),
                urgency_score=float(scored["urgency_score"]),
                current_status=item.previous_status,
            )
        )
        recommendation = self.recommendations.recommend(
            status=status,
            opportunity_score=opportunity_score,
            urgency_score=float(scored["urgency_score"]),
            confidence_score=float(scored["confidence_score"]),
            conflict_penalty=conflict_penalty,
        )
        supporting = [evidence for evidence in item.evidence if evidence.polarity != "contradicting"]
        contradicting = [evidence for evidence in item.evidence if evidence.polarity == "contradicting"]
        delta = self._delta(item, opportunity_score)
        return OpportunityDecision(
            company_id=item.company_id,
            company_name=item.company_name,
            status=status,
            recommendation=recommendation,
            opportunity_score=round(opportunity_score, 4),
            timing_score=float(scored["timing_score"]),
            confidence_score=float(scored["confidence_score"]),
            urgency_score=float(scored["urgency_score"]),
            growth_score=float(scored["growth_score"]),
            technology_fit_score=float(scored["technology_fit_score"]),
            ai_readiness_score=float(scored["ai_readiness_score"]),
            automation_readiness_score=float(scored["automation_readiness_score"]),
            decision_confidence_score=float(scored["decision_confidence_score"]),
            budget_probability_score=float(scored["budget_probability_score"]),
            score_breakdown=list(scored["score_breakdown"]),
            evidence=item.evidence,
            supporting_signals=supporting,
            contradicting_signals=contradicting,
            conflicts=conflicts,
            delta=delta,
            narrative=self._narrative(item, opportunity_score, delta, conflicts),
            created_from_context_ids=item.business_context_ids,
            scoring_latency_ms=scoring_latency_ms,
            decision_latency_ms=decision_latency_ms,
        )

    def _delta(self, item: CompanyOpportunityInput, opportunity_score: float) -> OpportunityDelta:
        previous = item.previous_score if item.previous_score is not None else 0.0
        change = round(opportunity_score - previous, 4)
        direction = "increased" if change > 0 else "decreased" if change < 0 else "unchanged"
        reasons = [f"Score {direction} by {abs(change):.1f} points."]
        if item.evidence:
            reasons.append(f"{len(item.evidence)} evidence items contributed to the decision.")
        return OpportunityDelta(
            score_change=change,
            direction=direction,
            new_evidence=[evidence.reference_id for evidence in item.evidence],
            expired_evidence=[],
            reasons=reasons,
        )

    def _narrative(
        self,
        item: CompanyOpportunityInput,
        opportunity_score: float,
        delta: OpportunityDelta,
        conflicts: list[object],
    ) -> str:
        conflict_text = f" {len(conflicts)} conflict(s) need review." if conflicts else ""
        return (
            f"{item.company_name} is evaluated as an opportunity with score {opportunity_score:.1f}. "
            f"The decision is based on {len(item.contexts)} context record(s), "
            f"{len(item.signals)} signal(s), and {len(item.evidence)} evidence item(s). "
            f"Score direction: {delta.direction}.{conflict_text}"
        )
