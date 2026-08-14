from opportunity_engine.models.types import OpportunityConflict, OpportunityEvidenceItem


class ConflictResolver:
    CONFLICT_PAIRS: tuple[tuple[str, str, str], ...] = (
        ("hiring", "layoffs", "hiring_vs_layoffs"),
        ("funding", "budget_cuts", "funding_vs_budget_cuts"),
        ("expansion", "store_closures", "expansion_vs_closures"),
        ("growth", "customer_complaints", "growth_vs_customer_complaints"),
    )

    def resolve(self, evidence: list[OpportunityEvidenceItem]) -> list[OpportunityConflict]:
        categories = {item.category: item for item in evidence}
        conflicts: list[OpportunityConflict] = []
        for positive, negative, conflict_type in self.CONFLICT_PAIRS:
            if positive in categories and negative in categories:
                first = categories[positive]
                second = categories[negative]
                severity = round((first.confidence + second.confidence) / 2.0, 4)
                conflicts.append(
                    OpportunityConflict(
                        conflict_type=conflict_type,
                        supporting_signal=positive,
                        contradicting_signal=negative,
                        severity=severity,
                        explanation=f"{positive.replace('_', ' ')} conflicts with {negative.replace('_', ' ')}.",
                        evidence_ids=[first.reference_id, second.reference_id],
                    )
                )
        return conflicts
