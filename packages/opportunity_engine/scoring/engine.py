from statistics import mean

from opportunity_engine.decay.policies import DecayPolicyCatalog
from opportunity_engine.models.types import CompanyOpportunityInput, OpportunityEvidenceItem, ScoreComponent


class OpportunityScorer:
    def __init__(self, decay: DecayPolicyCatalog | None = None) -> None:
        self.decay = decay or DecayPolicyCatalog()

    def score(self, item: CompanyOpportunityInput) -> dict[str, float | list[ScoreComponent]]:
        evidence = item.evidence
        weighted_confidence = self._weighted_average(evidence)
        urgency = self._max_context_value(item.contexts, "support_pressure", "operational_pressure", "sales_pressure")
        growth = self._growth_score(item)
        technology_fit = self._profile_value(item, "technology_maturity")
        ai_readiness = self._profile_value(item, "ai_adoption", fallback_key="ai_readiness")
        automation_readiness = self._profile_value(item, "automation_adoption", fallback_key="automation_readiness")
        decision_confidence = self._max_context_value(item.contexts, "budget_probability", "confidence")
        budget_probability = self._max_context_value(item.contexts, "budget_probability")
        timing = self._timing_score(evidence)
        conflict_penalty = 0.0
        components = [
            self._component("timing_score", timing, 0.14, "Recent evidence increases timing strength.", evidence),
            self._component("confidence_score", weighted_confidence, 0.16, "Merged confidence from source, context, and quality evidence.", evidence),
            self._component("urgency_score", urgency, 0.12, "Urgency comes from pressure and context urgency.", evidence),
            self._component("growth_score", growth, 0.10, "Growth is inferred from expansion, hiring, funding, and company DNA.", evidence),
            self._component("technology_fit_score", technology_fit, 0.10, "Technology maturity indicates ability to adopt a solution.", evidence),
            self._component("ai_readiness_score", ai_readiness, 0.10, "AI readiness comes from Company DNA and technology context.", evidence),
            self._component("automation_readiness_score", automation_readiness, 0.08, "Automation readiness measures likelihood of workflow change.", evidence),
            self._component("decision_confidence_score", decision_confidence, 0.10, "Decision confidence uses buying stage, budget, and context confidence.", evidence),
            self._component("budget_probability_score", budget_probability, 0.10, "Budget probability reflects funding and context budget signals.", evidence),
        ]
        opportunity_score = sum(component.value * component.weight for component in components) - conflict_penalty
        return {
            "opportunity_score": round(max(0.0, min(100.0, opportunity_score)), 4),
            "timing_score": round(timing, 4),
            "confidence_score": round(weighted_confidence, 4),
            "urgency_score": round(urgency, 4),
            "growth_score": round(growth, 4),
            "technology_fit_score": round(technology_fit, 4),
            "ai_readiness_score": round(ai_readiness, 4),
            "automation_readiness_score": round(automation_readiness, 4),
            "decision_confidence_score": round(decision_confidence, 4),
            "budget_probability_score": round(budget_probability, 4),
            "score_breakdown": components,
        }

    def _weighted_average(self, evidence: list[OpportunityEvidenceItem]) -> float:
        if not evidence:
            return 0.0
        weights = [self.decay.weight(item) for item in evidence]
        weighted = sum(item.confidence * weight for item, weight in zip(evidence, weights, strict=False))
        total_weight = sum(weights)
        return weighted / total_weight if total_weight else 0.0

    def _timing_score(self, evidence: list[OpportunityEvidenceItem]) -> float:
        if not evidence:
            return 0.0
        return min(100.0, mean(self.decay.weight(item) * 100.0 for item in evidence))

    def _max_context_value(self, contexts: list[dict[str, object]], *keys: str) -> float:
        values: list[float] = []
        for context in contexts:
            for key in keys:
                value = context.get(key)
                if isinstance(value, int | float):
                    values.append(float(value))
        return max(values) if values else 0.0

    def _profile_value(self, item: CompanyOpportunityInput, key: str, *, fallback_key: str | None = None) -> float:
        value = item.company_profile.get(key)
        if not isinstance(value, int | float) and fallback_key is not None:
            value = self._max_context_value(item.contexts, fallback_key)
        return float(value) if isinstance(value, int | float) else 0.0

    def _growth_score(self, item: CompanyOpportunityInput) -> float:
        categories = {signal.get("category") for signal in item.signals}
        score = 35.0
        score += 18.0 if "funding" in categories else 0.0
        score += 16.0 if "expansion" in categories else 0.0
        score += 12.0 if "hiring" in categories else 0.0
        score += min(20.0, len(item.timeline) * 2.0)
        return min(100.0, score)

    def _component(
        self,
        name: str,
        value: float,
        weight: float,
        explanation: str,
        evidence: list[OpportunityEvidenceItem],
    ) -> ScoreComponent:
        return ScoreComponent(
            name=name,
            value=round(value, 4),
            weight=weight,
            explanation=explanation,
            evidence_ids=[item.reference_id for item in evidence[:20]],
        )
