from opportunity_engine.models.types import OpportunityRecommendation, OpportunityStatus, RecommendationAction


class RecommendationEngine:
    def recommend(
        self,
        *,
        status: OpportunityStatus,
        opportunity_score: float,
        urgency_score: float,
        confidence_score: float,
        conflict_penalty: float,
    ) -> OpportunityRecommendation:
        reasons: list[str] = []
        if conflict_penalty >= 15:
            reasons.append("Conflicting evidence requires human review before action.")
            return OpportunityRecommendation(
                action=RecommendationAction.COLLECT_MORE_EVIDENCE,
                confidence=confidence_score,
                reasons=reasons,
                next_step="Collect additional evidence to resolve contradictions.",
            )
        if status == OpportunityStatus.HIGH_INTENT and urgency_score >= 82:
            action = RecommendationAction.CONTACT_TODAY
            next_step = "Prioritize this company today because timing and confidence are both strong."
        elif status == OpportunityStatus.HIGH_INTENT:
            action = RecommendationAction.CONTACT_WITHIN_7_DAYS
            next_step = "Prepare a context-backed action plan within seven days."
        elif status == OpportunityStatus.QUALIFIED:
            action = RecommendationAction.CONTACT_WITHIN_30_DAYS
            next_step = "Monitor for one more confirming signal and plan contact within thirty days."
        elif status == OpportunityStatus.EMERGING:
            action = RecommendationAction.WATCH
            next_step = "Watch for additional context or timeline changes."
        elif opportunity_score < 25:
            action = RecommendationAction.IGNORE
            next_step = "Ignore until stronger evidence appears."
        else:
            action = RecommendationAction.COLLECT_MORE_EVIDENCE
            next_step = "Collect more context before making this an active opportunity."
        reasons.append(f"Lifecycle status is {status.value}.")
        reasons.append(f"Opportunity score is {opportunity_score:.1f}.")
        return OpportunityRecommendation(
            action=action,
            confidence=confidence_score,
            reasons=reasons,
            next_step=next_step,
        )
