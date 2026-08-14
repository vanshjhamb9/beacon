from revenue_engine.buyer_personas.engine import BuyerPersonaEngine
from revenue_engine.matching.engine import ServiceMatchingEngine
from revenue_engine.metrics.timing import RevenueTimer
from revenue_engine.models.types import RevenueOpportunityInput, RevenueRecommendationResult
from revenue_engine.pricing.engine import RevenueEstimator
from revenue_engine.prioritization.engine import SalesPrioritizationEngine
from revenue_engine.recommendations.playbook import PlaybookEngine


class RevenuePipeline:
    def __init__(
        self,
        *,
        matcher: ServiceMatchingEngine | None = None,
        persona_engine: BuyerPersonaEngine | None = None,
        estimator: RevenueEstimator | None = None,
        prioritizer: SalesPrioritizationEngine | None = None,
        playbooks: PlaybookEngine | None = None,
        timer: RevenueTimer | None = None,
    ) -> None:
        self.matcher = matcher or ServiceMatchingEngine()
        self.persona_engine = persona_engine or BuyerPersonaEngine()
        self.estimator = estimator or RevenueEstimator()
        self.prioritizer = prioritizer or SalesPrioritizationEngine()
        self.playbooks = playbooks or PlaybookEngine()
        self.timer = timer or RevenueTimer()

    def process(self, item: RevenueOpportunityInput) -> RevenueRecommendationResult:
        def _run() -> RevenueRecommendationResult:
            matches = self.matcher.match(item)
            if not matches:
                raise ValueError("Revenue recommendations require at least one enabled service.")
            primary = matches[0]
            secondary = matches[1] if len(matches) > 1 else None
            estimate = self.estimator.estimate(item, primary)
            prediction = self.prioritizer.prioritize(item, primary, estimate)
            personas = self.persona_engine.infer(item, primary)
            playbook = self.playbooks.build(item, primary, estimate, personas)
            cross_sell = matches[2:5]
            upsell = [match for match in matches[1:4] if match.service.base_price > primary.service.base_price]
            confidence = round(
                (primary.confidence * 0.45 + item.confidence_score * 0.35 + item.quality_score * 0.2),
                4,
            )
            interesting_why = (
                item.narrative
                if item.narrative
                else f"{item.company_name} shows opportunity score {item.opportunity_score:.1f}."
            )
            return RevenueRecommendationResult(
                company_id=item.company_id,
                opportunity_id=item.opportunity_id,
                primary_service=primary,
                secondary_service=secondary,
                cross_sell=cross_sell,
                upsell=upsell,
                buyer_personas=personas,
                revenue_estimate=estimate,
                deal_prediction=prediction,
                playbook=playbook,
                confidence=confidence,
                reasoning=(
                    f"{interesting_why} {primary.service.name} is the strongest deterministic service match "
                    f"with priority {prediction.priority_level.value}."
                ),
                evidence={
                    "opportunity_score": item.opportunity_score,
                    "urgency_score": item.urgency_score,
                    "quality_score": item.quality_score,
                    "knowledge_node_ids": [str(node_id) for node_id in item.knowledge_node_ids],
                    "matched_services": [match.service.service_key for match in matches],
                    "business_pain": playbook.business_pain,
                    "why_interesting": interesting_why,
                    "why_now": (
                        f"Recommendation '{item.recommendation}' with urgency {item.urgency_score:.1f} "
                        f"supports contacting now."
                    ),
                },
            )

        result, latency_ms = self.timer.measure(_run)
        return result.model_copy(update={"processing_latency_ms": latency_ms})
