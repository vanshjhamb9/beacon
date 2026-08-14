from revenue_engine.models.types import (
    BuyerPersonaResult,
    RevenueEstimate,
    RevenueOpportunityInput,
    RevenuePlaybook,
    ServiceMatch,
)


class PlaybookEngine:
    def build(
        self,
        item: RevenueOpportunityInput,
        primary: ServiceMatch,
        estimate: RevenueEstimate,
        personas: list[BuyerPersonaResult],
    ) -> RevenuePlaybook:
        pain = self._primary_pain(item)
        decision_maker = personas[0].persona if personas else "CEO"
        why_now = (
            f"Opportunity score {item.opportunity_score:.1f} with urgency {item.urgency_score:.1f} "
            f"and recommendation '{item.recommendation}' indicate contact timing is active."
        )
        return RevenuePlaybook(
            business_pain=pain,
            recommended_service=primary.service.name,
            why=(
                f"{primary.service.name} is the best fit because {primary.reasoning} "
                f"{why_now}"
            ),
            conversation_angle=(
                f"Open with the observed business signal for {item.company_name} and validate whether "
                f"{pain.replace('_', ' ')} is a priority this quarter before proposing {primary.service.name}."
            ),
            decision_maker=decision_maker,
            expected_outcome=(
                f"Deliver a {estimate.project_size.value} engagement that reduces friction around "
                f"{pain.replace('_', ' ')} with {estimate.implementation_complexity} implementation complexity."
            ),
            risk=(
                "Budget ownership or implementation complexity may extend the sales cycle; "
                "confirm decision maker, integrations, and success metrics early."
            ),
        )

    def _primary_pain(self, item: RevenueOpportunityInput) -> str:
        if item.pains:
            category = str(item.pains[0].get("category") or "").strip()
            value = str(item.pains[0].get("value") or "").strip()
            if category and value and value.lower() != category.lower():
                return f"{category}: {value}"
            if category:
                return category
            if value:
                return value
        if item.narrative:
            return item.narrative[:180]
        return "operations"
