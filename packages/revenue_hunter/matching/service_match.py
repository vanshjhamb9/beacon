from __future__ import annotations

from revenue_hunter.models.types import BeaconService, RevenueHunterInput, ServiceMatchResult


# Deterministic catalog: term/pain/industry → service pitch
SERVICE_CATALOG: list[dict[str, object]] = [
    {
        "service": BeaconService.COMAI.value,
        "terms": ["comai", "commerce ai", "whatsapp", "gorgias", "shopify", "support inbox", "omnichannel"],
        "pains": ["growing support", "high support cost", "poor conversion", "customer support"],
        "industries": ["ecommerce", "saas", "retail"],
        "base": 42.0,
    },
    {
        "service": BeaconService.CUSTOM_AI.value,
        "terms": ["custom ai", "machine learning", "llm", "openai", "model", "prediction", "ml"],
        "pains": ["old technology", "no automation", "scaling issues", "manual workflows"],
        "industries": ["saas", "fintech", "healthcare", "technology"],
        "base": 40.0,
    },
    {
        "service": BeaconService.WEBSITE.value,
        "terms": ["website", "wordpress", "landing page", "webflow", "seo", "lighthouse"],
        "pains": ["poor website", "poor conversion", "weak seo", "outdated website"],
        "industries": ["marketing", "real estate", "legal", "education", "construction"],
        "base": 38.0,
    },
    {
        "service": BeaconService.MOBILE_APP.value,
        "terms": ["mobile", "ios", "android", "flutter", "react native", "app store"],
        "pains": ["poor conversion", "customer experience", "engagement"],
        "industries": ["ecommerce", "fintech", "healthcare", "education"],
        "base": 36.0,
    },
    {
        "service": BeaconService.SAAS.value,
        "terms": ["saas", "multi-tenant", "subscription", "platform product", "b2b software"],
        "pains": ["scaling issues", "product", "digital transformation"],
        "industries": ["saas", "technology", "fintech"],
        "base": 40.0,
    },
    {
        "service": BeaconService.INTERNAL_SOFTWARE.value,
        "terms": ["internal tools", "ops platform", "back office", "admin portal", "intranet"],
        "pains": ["manual workflows", "hiring operations", "scaling issues", "operations"],
        "industries": ["manufacturing", "logistics", "legal", "construction"],
        "base": 35.0,
    },
    {
        "service": BeaconService.AUTOMATION.value,
        "terms": ["automation", "workflow", "rpa", "zapier", "n8n", "process automation"],
        "pains": ["manual workflows", "no automation", "hiring operations", "efficiency"],
        "industries": ["saas", "ecommerce", "logistics", "manufacturing", "marketing"],
        "base": 39.0,
    },
    {
        "service": BeaconService.AI_CHATBOT.value,
        "terms": ["chatbot", "intercom", "zendesk", "livechat", "conversational", "bot"],
        "pains": ["growing support", "high support cost", "customer support"],
        "industries": ["ecommerce", "saas", "fintech", "healthcare"],
        "base": 37.0,
    },
    {
        "service": BeaconService.CRM.value,
        "terms": ["crm", "salesforce", "hubspot", "pipedrive", "lead management"],
        "pains": ["poor conversion", "sales process", "pipeline"],
        "industries": ["saas", "real estate", "marketing", "fintech"],
        "base": 34.0,
    },
    {
        "service": BeaconService.ERP.value,
        "terms": ["erp", "sap", "netsuite", "inventory", "finance system"],
        "pains": ["old technology", "scaling issues", "operations"],
        "industries": ["manufacturing", "logistics", "construction", "ecommerce"],
        "base": 33.0,
    },
    {
        "service": BeaconService.MULTI_AGENT_SYSTEMS.value,
        "terms": ["multi agent", "agents", "autonomous", "agentic", "orchestration", "swarm"],
        "pains": ["no automation", "scaling issues", "manual workflows", "operations"],
        "industries": ["saas", "technology", "fintech", "logistics"],
        "base": 41.0,
    },
]


class ServiceMatchEngine:
    """Pitch the highest-confidence Beacon service with evidence."""

    def match(self, item: RevenueHunterInput) -> list[ServiceMatchResult]:
        text = self._text(item)
        industry = (item.industry or "").lower()
        pains_lower = [p.lower() for p in item.pains]
        results: list[ServiceMatchResult] = []

        for entry in SERVICE_CATALOG:
            terms = [str(t).lower() for t in entry["terms"]]  # type: ignore[index]
            pain_targets = [str(p).lower() for p in entry["pains"]]  # type: ignore[index]
            industries = [str(i).lower() for i in entry["industries"]]  # type: ignore[index]
            term_hits = sum(1 for t in terms if t in text)
            pain_hits = sum(1 for p in pain_targets if any(p in pain or pain in p for pain in pains_lower))
            industry_hit = any(i in industry or industry in i for i in industries) if industry else False
            opp_boost = min(20.0, item.opportunity_score * 0.2)
            confidence = float(entry["base"]) + term_hits * 8.0 + pain_hits * 10.0 + (8.0 if industry_hit else 0.0) + opp_boost
            confidence = min(100.0, round(confidence, 4))
            if confidence < 35.0 and term_hits == 0 and pain_hits == 0:
                continue
            evidence = [f"term_hits:{term_hits}", f"pain_hits:{pain_hits}"]
            if industry_hit:
                evidence.append(f"industry_fit:{item.industry}")
            for t in terms:
                if t in text:
                    evidence.append(f"matched_term:{t}")
            results.append(
                ServiceMatchResult(
                    service=str(entry["service"]),
                    confidence=confidence,
                    reasoning=(
                        f"Matched {entry['service']} with {term_hits} term hit(s), "
                        f"{pain_hits} pain hit(s), industry fit={industry_hit}, "
                        f"opportunity_score={item.opportunity_score:.1f}."
                    ),
                    evidence=evidence[:12],
                    term_hits=term_hits,
                    pain_hits=pain_hits,
                    industry_hit=industry_hit,
                )
            )

        if not results:
            results.append(
                ServiceMatchResult(
                    service=BeaconService.CUSTOM_AI.value,
                    confidence=round(max(35.0, item.opportunity_score * 0.4), 4),
                    reasoning="No strong specialty match; defaulted to Custom AI for agency discovery call.",
                    evidence=["fallback:custom_ai"],
                )
            )
        return sorted(results, key=lambda r: (-r.confidence, r.service))

    def _text(self, item: RevenueHunterInput) -> str:
        parts = [
            item.company_name,
            item.industry or "",
            item.business_model or "",
            " ".join(item.technologies),
            " ".join(item.pains),
            " ".join(item.goals),
            " ".join(item.signals),
            " ".join(item.hiring_roles),
            " ".join(item.products),
            " ".join(item.growth_signals),
        ]
        return " ".join(parts).lower()
