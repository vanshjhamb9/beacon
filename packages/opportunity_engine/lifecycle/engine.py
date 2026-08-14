from opportunity_engine.models.types import OpportunityStatus


class LifecycleEngine:
    def determine(
        self,
        *,
        opportunity_score: float,
        confidence_score: float,
        urgency_score: float,
        current_status: OpportunityStatus | None = None,
    ) -> OpportunityStatus:
        if current_status in {
            OpportunityStatus.CONTACTED,
            OpportunityStatus.MEETING,
            OpportunityStatus.PROPOSAL,
            OpportunityStatus.WON,
            OpportunityStatus.LOST,
            OpportunityStatus.ARCHIVED,
        }:
            return current_status
        if opportunity_score >= 82 and confidence_score >= 70 and urgency_score >= 70:
            return OpportunityStatus.HIGH_INTENT
        if opportunity_score >= 72 and confidence_score >= 65:
            return OpportunityStatus.QUALIFIED
        if opportunity_score >= 58:
            return OpportunityStatus.EMERGING
        if opportunity_score >= 42:
            return OpportunityStatus.WATCHING
        return OpportunityStatus.OBSERVED
