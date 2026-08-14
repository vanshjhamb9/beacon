from revenue_engine.models.types import (
    BudgetRange,
    ProjectSize,
    RevenueEstimate,
    RevenueOpportunityInput,
    ServiceMatch,
)


class RevenueEstimator:
    def estimate(self, item: RevenueOpportunityInput, primary: ServiceMatch) -> RevenueEstimate:
        complexity_multiplier = {"low": 0.8, "medium": 1.0, "high": 1.45}.get(primary.service.complexity, 1.0)
        stage_multiplier = {"scaling": 1.2, "expanding": 1.3, "mature": 1.15}.get(item.company_stage or "", 1.0)
        confidence_multiplier = max(item.confidence_score, 50.0) / 100.0
        one_time = round(primary.service.base_price * complexity_multiplier * stage_multiplier, 2)
        mrr = round(primary.service.monthly_price * stage_multiplier, 2)
        expansion = round(one_time * 0.35 + mrr * 12.0 * 0.25, 2)
        renewal = round(mrr * 12.0 * confidence_multiplier, 2)
        strategic = round(one_time + expansion + renewal, 2)
        project_size = self._project_size(one_time)
        budget = self._budget_range(project_size)
        return RevenueEstimate(
            project_size=project_size,
            implementation_complexity=primary.service.complexity,
            estimated_budget_range=budget,
            mrr_potential=mrr,
            one_time_revenue=one_time,
            expansion_potential=expansion,
            renewal_potential=renewal,
            strategic_account_value=strategic,
            explanation=(
                f"Estimated from {primary.service.name} base price, {primary.service.complexity} complexity, "
                f"company stage {item.company_stage or 'unknown'}, and confidence {item.confidence_score:.1f}."
            ),
        )

    def _project_size(self, value: float) -> ProjectSize:
        if value >= 75000:
            return ProjectSize.ENTERPRISE
        if value >= 35000:
            return ProjectSize.LARGE
        if value >= 15000:
            return ProjectSize.MEDIUM
        return ProjectSize.SMALL

    def _budget_range(self, project_size: ProjectSize) -> BudgetRange:
        mapping = {
            ProjectSize.SMALL: BudgetRange.SMALL,
            ProjectSize.MEDIUM: BudgetRange.MEDIUM,
            ProjectSize.LARGE: BudgetRange.LARGE,
            ProjectSize.ENTERPRISE: BudgetRange.ENTERPRISE,
        }
        return mapping[project_size]
