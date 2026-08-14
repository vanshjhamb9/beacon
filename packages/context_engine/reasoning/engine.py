from context_engine.extractors.taxonomy import TaxonomyExtractor
from context_engine.models.types import (
    BusinessContextInput,
    BusinessContextResult,
    BuyingStage,
    CompanyDNAResult,
    ContextInference,
    DecisionStage,
    GrowthStage,
)
from context_engine.rules.definitions import ContextRule, ContextRuleCatalog
from context_engine.rules.defaults import default_context_rules
from context_engine.services.evidence import EvidenceBuilder
from context_engine.taxonomy.business import ReasoningTaxonomy


class BusinessReasoningEngine:
    def __init__(
        self,
        *,
        rules: ContextRuleCatalog | None = None,
        extractor: TaxonomyExtractor | None = None,
        evidence_builder: EvidenceBuilder | None = None,
        taxonomy: ReasoningTaxonomy | None = None,
    ) -> None:
        self.rules = rules or default_context_rules()
        self.extractor = extractor or TaxonomyExtractor()
        self.evidence_builder = evidence_builder or EvidenceBuilder()
        self.taxonomy = taxonomy or ReasoningTaxonomy()

    def reason(self, item: BusinessContextInput) -> tuple[BusinessContextResult, CompanyDNAResult]:
        matching_rules = self._matching_rules(item)
        pain_terms = self.extractor.matching_pains(item)
        technology_terms = self.extractor.matching_technologies(item)
        base_confidence = self._confidence(item, matching_rules)
        pressures = self._pressures(item, pain_terms)
        buying_stage = self._buying_stage(item, matching_rules)
        decision_stage = self._decision_stage(item, matching_rules)
        growth_stage = self._growth_stage(item)
        maturity = self._maturity_scores(item, technology_terms)
        evidence = self.evidence_builder.build(
            item,
            rules=matching_rules,
            confidence_breakdown={
                "signal_confidence": item.signal_confidence,
                "quality_score": item.quality_score,
                "rule_match_score": min(100.0, len(matching_rules) * 12.0),
            },
            explanation=self._explanation(item, matching_rules),
        )

        context = BusinessContextResult(
            company_id=item.company_id,
            classified_signal_id=item.classified_signal_id,
            raw_event_id=item.raw_event_id,
            business_pain=self._inference("business_pain", self._pain(item, pain_terms), item, matching_rules, base_confidence),
            business_goal=self._inference("business_goal", self._goal(item), item, matching_rules, base_confidence),
            business_trigger=self._inference("business_trigger", self._trigger(item), item, matching_rules, base_confidence),
            business_impact=self._inference("business_impact", self._impact(item), item, matching_rules, base_confidence),
            business_urgency=item.urgency,
            buying_stage=buying_stage,
            decision_stage=decision_stage,
            growth_stage=growth_stage,
            digital_maturity=maturity["digital_maturity"],
            ai_readiness=maturity["ai_readiness"],
            automation_readiness=maturity["automation_readiness"],
            budget_probability=self._budget_probability(item),
            technology_maturity=maturity["technology_maturity"],
            expansion_probability=self._expansion_probability(item),
            operational_pressure=pressures["operations"],
            customer_experience_pressure=pressures["customer_experience"],
            support_pressure=pressures["support"],
            engineering_pressure=pressures["engineering"],
            marketing_pressure=pressures["marketing"],
            sales_pressure=pressures["sales"],
            confidence=base_confidence,
            evidence=evidence,
            processing_time_ms=0.0,
        )
        dna = CompanyDNAResult(
            company_id=item.company_id,
            industry=str(item.company_attributes.get("industry")) if item.company_attributes.get("industry") else None,
            business_model=self._business_model(item),
            company_stage=growth_stage,
            growth_pattern=self._growth_pattern(item),
            technology_stack=[term.label for term in technology_terms],
            digital_maturity=maturity["digital_maturity"],
            ai_adoption=maturity["ai_readiness"],
            automation_adoption=maturity["automation_readiness"],
            hiring_pattern="active" if item.category == "hiring" else "unknown",
            expansion_pattern="active" if item.category == "expansion" else "unknown",
            innovation_score=min(100.0, maturity["ai_readiness"] * 0.5 + maturity["technology_maturity"] * 0.5),
            support_maturity=max(0.0, 100.0 - pressures["support"]),
            operational_maturity=max(0.0, 100.0 - pressures["operations"]),
            technology_maturity=maturity["technology_maturity"],
            customer_maturity=max(0.0, 100.0 - pressures["customer_experience"]),
            evidence=evidence,
            completeness_score=self._dna_completeness(item, technology_terms),
        )
        return context, dna

    def _matching_rules(self, item: BusinessContextInput) -> list[ContextRule]:
        matches: list[ContextRule] = []
        for rule in self.rules.enabled():
            categories = set(rule.conditions.get("categories", []))
            terms = [str(term).lower() for term in rule.conditions.get("terms", [])]
            category_match = not categories or item.category in categories
            term_match = not terms or any(term in item.text for term in terms)
            if category_match and term_match:
                matches.append(rule)
        return matches

    def _confidence(self, item: BusinessContextInput, rules: list[ContextRule]) -> float:
        rule_score = min(100.0, 50.0 + (len(rules) * 10.0))
        return round((item.signal_confidence * 0.45) + (item.quality_score * 0.35) + (rule_score * 0.2), 4)

    def _inference(
        self,
        kind: str,
        value: str,
        item: BusinessContextInput,
        rules: list[ContextRule],
        confidence: float,
    ) -> ContextInference:
        evidence = self.evidence_builder.build(
            item,
            rules=rules,
            confidence_breakdown={"context_confidence": confidence},
            explanation=f"{kind.replace('_', ' ').title()} inferred as {value} from {item.category}.",
        )
        return ContextInference(kind=kind, category=value, value=value.replace("_", " ").title(), confidence=confidence, evidence=evidence)

    def _pain(self, item: BusinessContextInput, pain_terms: list[object]) -> str:
        if pain_terms:
            return getattr(pain_terms[0], "key")
        return self.taxonomy.pain_by_category.get(item.category, "operations")

    def _goal(self, item: BusinessContextInput) -> str:
        return self.taxonomy.goal_by_category.get(item.category, "improve_business_performance")

    def _trigger(self, item: BusinessContextInput) -> str:
        return self.taxonomy.trigger_by_category.get(item.category, "business_signal_detected")

    def _impact(self, item: BusinessContextInput) -> str:
        if item.polarity == "negative":
            return "risk_reduction_required"
        return self.taxonomy.impact_by_category.get(item.category, "operational_priority_change")

    def _pressures(self, item: BusinessContextInput, pain_terms: list[object]) -> dict[str, float]:
        base = 25.0 + (20.0 if item.urgency in {"high", "critical"} else 0.0)
        pressures = {key: 15.0 for key in ["operations", "customer_experience", "support", "engineering", "marketing", "sales"]}
        if item.category in {"customer_support", "customer_complaints"}:
            pressures["support"] = base + 25.0
            pressures["customer_experience"] = base + 20.0
        if item.category in {"technology_migration", "ai_adoption", "automation"}:
            pressures["engineering"] = base + 20.0
            pressures["operations"] = base + 15.0
        if item.category in {"product_launch", "pricing_changes"}:
            pressures["marketing"] = base + 15.0
            pressures["sales"] = base + 15.0
        if item.category in {"expansion", "hiring"}:
            pressures["operations"] = base + 20.0
        for term in pain_terms:
            key = getattr(term, "key")
            if key in pressures:
                pressures[key] = min(100.0, pressures[key] + 10.0)
        return {key: min(100.0, value) for key, value in pressures.items()}

    def _buying_stage(self, item: BusinessContextInput, rules: list[ContextRule]) -> BuyingStage:
        for rule in rules:
            if rule.outputs.get("buying_stage"):
                return BuyingStage(str(rule.outputs["buying_stage"]))
        if item.category in {"technology_migration", "automation", "ai_adoption"}:
            return BuyingStage.SOLUTION_EXPLORING
        if item.category in {"customer_complaints", "pricing_changes"}:
            return BuyingStage.PROBLEM_AWARE
        return BuyingStage.AWARE

    def _decision_stage(self, item: BusinessContextInput, rules: list[ContextRule]) -> DecisionStage:
        for rule in rules:
            if rule.outputs.get("decision_stage"):
                return DecisionStage(str(rule.outputs["decision_stage"]))
        if item.category == "funding":
            return DecisionStage.BUDGET_DISCOVERY
        return DecisionStage.INDIVIDUAL_RESEARCH

    def _growth_stage(self, item: BusinessContextInput) -> GrowthStage:
        if item.category == "funding":
            return GrowthStage.SCALING
        if item.category == "expansion":
            return GrowthStage.EXPANDING
        if item.company_attributes.get("signal_frequency", 0):
            return GrowthStage.MATURE
        return GrowthStage.UNKNOWN

    def _maturity_scores(self, item: BusinessContextInput, technologies: list[object]) -> dict[str, float]:
        technology_count = len(technologies)
        ai_count = sum(1 for term in technologies if getattr(term, "key") in self.taxonomy.ai_terms)
        automation_signal = item.category in {"automation", "ai_adoption"}
        return {
            "digital_maturity": min(100.0, 45.0 + technology_count * 8.0),
            "ai_readiness": min(100.0, 30.0 + ai_count * 20.0 + (20.0 if item.category == "ai_adoption" else 0.0)),
            "automation_readiness": min(100.0, 35.0 + (30.0 if automation_signal else 0.0) + technology_count * 4.0),
            "technology_maturity": min(100.0, 40.0 + technology_count * 7.0),
        }

    def _budget_probability(self, item: BusinessContextInput) -> float:
        base = 35.0
        if item.category == "funding":
            base += 35.0
        if item.urgency in {"high", "critical"}:
            base += 15.0
        return min(100.0, base)

    def _expansion_probability(self, item: BusinessContextInput) -> float:
        return 82.0 if item.category == "expansion" else 35.0

    def _business_model(self, item: BusinessContextInput) -> str:
        text = item.text
        if "shopify" in text or "woocommerce" in text or "inventory" in text:
            return "commerce"
        if "saas" in text or "subscription" in text:
            return "saas"
        return "unknown"

    def _growth_pattern(self, item: BusinessContextInput) -> str:
        if item.category in {"hiring", "funding", "expansion"}:
            return item.category
        return "signal_accumulation"

    def _dna_completeness(self, item: BusinessContextInput, technologies: list[object]) -> float:
        fields = [
            bool(item.company_name),
            bool(item.category),
            bool(item.business_function),
            bool(technologies),
            bool(item.company_attributes),
        ]
        return round(sum(1 for value in fields if value) / len(fields) * 100.0, 4)

    def _explanation(self, item: BusinessContextInput, rules: list[ContextRule]) -> str:
        rule_keys = ", ".join(rule.key for rule in rules) or "baseline_context"
        return f"Context derived from classified signal '{item.category}' using rules: {rule_keys}."
