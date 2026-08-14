from revenue_engine.models.types import DealPrediction, PriorityLevel, RevenueEstimate, RevenueOpportunityInput, ServiceMatch


class SalesPrioritizationEngine:
    def prioritize(
        self,
        item: RevenueOpportunityInput,
        primary: ServiceMatch,
        estimate: RevenueEstimate,
    ) -> DealPrediction:
        revenue_score = min(100.0, estimate.strategic_account_value / 1000.0)
        strategic = min(100.0, item.opportunity_score * 0.45 + primary.confidence * 0.35 + item.quality_score * 0.2)
        complexity_penalty = {"low": 15.0, "medium": 35.0, "high": 55.0}.get(estimate.implementation_complexity, 35.0)
        closing = max(5.0, min(95.0, item.confidence_score * 0.45 + item.urgency_score * 0.25 + primary.confidence * 0.3 - complexity_penalty * 0.2))
        clv = estimate.strategic_account_value + estimate.renewal_potential * 2.0
        priority_score = revenue_score * 0.25 + item.urgency_score * 0.25 + closing * 0.25 + strategic * 0.25
        priority = PriorityLevel.CRITICAL if priority_score >= 82 else PriorityLevel.HIGH if priority_score >= 68 else PriorityLevel.MEDIUM if priority_score >= 45 else PriorityLevel.LOW
        return DealPrediction(
            revenue_score=round(revenue_score, 4),
            urgency=round(item.urgency_score, 4),
            closing_probability=round(closing, 4),
            strategic_importance=round(strategic, 4),
            customer_lifetime_value=round(clv, 2),
            implementation_complexity=complexity_penalty,
            priority_level=priority,
            expected_sales_cycle_days=45 if priority in {PriorityLevel.CRITICAL, PriorityLevel.HIGH} else 90,
            explanation="Priority combines revenue potential, urgency, close probability, and strategic fit.",
        )
