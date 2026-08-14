from revenue_engine.models.types import RevenueOpportunityInput, ServiceMatch


class ServiceMatchingEngine:
    def match(self, item: RevenueOpportunityInput) -> list[ServiceMatch]:
        text = self._text(item)
        matches: list[ServiceMatch] = []
        for service in [service for service in item.services if service.enabled]:
            term_hits = sum(1 for term in service.matching_terms if term.lower() in text)
            pain_hits = sum(
                1
                for pain in item.pains
                if str(pain.get("category", "")).lower() in {target.lower() for target in service.target_pains}
            )
            industry_hit = int(
                item.industry is not None
                and item.industry.lower() in {industry.lower() for industry in service.target_industries}
            )
            knowledge_boost = min(6.0, float(len(item.knowledge_node_ids)) * 1.5)
            base = item.opportunity_score * 0.35 + item.confidence_score * 0.25 + item.quality_score * 0.15
            confidence = min(
                100.0,
                base + term_hits * 8.0 + pain_hits * 12.0 + industry_hit * 6.0 + knowledge_boost,
            )
            if confidence >= 35.0:
                matches.append(
                    ServiceMatch(
                        service=service,
                        confidence=round(confidence, 4),
                        reasoning=(
                            f"Matched {service.name} using {term_hits} term hit(s), "
                            f"{pain_hits} pain hit(s), industry fit {bool(industry_hit)}, "
                            f"knowledge-graph refs {len(item.knowledge_node_ids)}, "
                            f"and opportunity score {item.opportunity_score:.1f}."
                        ),
                        evidence={
                            "term_hits": term_hits,
                            "pain_hits": pain_hits,
                            "industry_hit": industry_hit,
                            "knowledge_node_count": len(item.knowledge_node_ids),
                            "quality_score": item.quality_score,
                        },
                    )
                )
        if not matches and item.services:
            fallback = next((service for service in item.services if service.enabled), item.services[0])
            matches.append(
                ServiceMatch(
                    service=fallback,
                    confidence=round(max(35.0, item.opportunity_score * 0.4 + item.quality_score * 0.2), 4),
                    reasoning=(
                        f"No strong specialty match; defaulted to {fallback.name} using opportunity and quality scores."
                    ),
                    evidence={"fallback": True, "quality_score": item.quality_score},
                )
            )
        return sorted(matches, key=lambda match: match.confidence, reverse=True)

    def _text(self, item: RevenueOpportunityInput) -> str:
        values: list[str] = [
            item.company_name,
            item.recommendation,
            item.narrative,
            item.industry or "",
            item.business_model or "",
            " ".join(item.technology_stack),
        ]
        values.extend(str(pain.get("category", "")) + " " + str(pain.get("value", "")) for pain in item.pains)
        values.extend(str(goal.get("category", "")) + " " + str(goal.get("value", "")) for goal in item.goals)
        values.extend(str(context) for context in item.contexts)
        values.extend(str(evidence) for evidence in item.opportunity_evidence)
        return " ".join(values).lower()
