from __future__ import annotations

from sales_intelligence.models.types import OfferRecommendation, OfferType, SalesIntelligenceInput


OFFER_RULES: list[dict[str, object]] = [
    {
        "offer": OfferType.AI_CUSTOMER_SUPPORT,
        "terms": ["support", "zendesk", "chatbot", "whatsapp", "gorgias"],
        "pains": ["growing support", "high support cost"],
        "base": 40.0,
        "value": "$25k–$55k",
    },
    {
        "offer": OfferType.AI_AUTOMATION,
        "terms": ["automation", "workflow", "manual", "ops", "rpa"],
        "pains": ["manual workflows", "no automation"],
        "base": 42.0,
        "value": "$20k–$45k",
    },
    {
        "offer": OfferType.CUSTOM_SAAS,
        "terms": ["saas", "platform", "multi-tenant", "product"],
        "pains": ["scaling issues", "product"],
        "base": 38.0,
        "value": "$45k–$90k",
    },
    {
        "offer": OfferType.WEBSITE,
        "terms": ["website", "seo", "conversion", "wordpress"],
        "pains": ["poor website", "poor conversion"],
        "base": 36.0,
        "value": "$12k–$30k",
    },
    {
        "offer": OfferType.MOBILE_APP,
        "terms": ["mobile", "ios", "android", "app"],
        "pains": ["engagement", "customer experience"],
        "base": 34.0,
        "value": "$30k–$70k",
    },
    {
        "offer": OfferType.MVP,
        "terms": ["mvp", "startup", "seed", "prototype"],
        "pains": ["speed", "validation"],
        "base": 33.0,
        "value": "$15k–$35k",
    },
    {
        "offer": OfferType.MARKETPLACE,
        "terms": ["marketplace", "two-sided", "sellers", "buyers"],
        "pains": ["platform"],
        "base": 32.0,
        "value": "$50k–$120k",
    },
    {
        "offer": OfferType.CONSULTING,
        "terms": ["strategy", "roadmap", "advisory"],
        "pains": ["transformation"],
        "base": 30.0,
        "value": "$8k–$25k",
    },
    {
        "offer": OfferType.DIGITAL_TRANSFORMATION,
        "terms": ["legacy", "modernization", "erp", "transformation"],
        "pains": ["old technology", "scaling issues"],
        "base": 35.0,
        "value": "$60k–$150k",
    },
]


class OfferRecommendationEngine:
    def recommend(self, item: SalesIntelligenceInput) -> OfferRecommendation:
        text = " ".join(
            [
                item.recommended_service or "",
                item.industry or "",
                " ".join(item.technologies),
                " ".join(item.pains),
                " ".join(item.signals),
                " ".join(item.goals),
            ]
        ).lower()
        ranked: list[dict[str, object]] = []
        for rule in OFFER_RULES:
            terms = [str(t) for t in rule["terms"]]  # type: ignore[index]
            pains = [str(p) for p in rule["pains"]]  # type: ignore[index]
            term_hits = sum(1 for t in terms if t in text)
            pain_hits = sum(1 for p in pains if p in text)
            score = float(rule["base"]) + term_hits * 8.0 + pain_hits * 10.0
            if item.recommended_service and str(rule["offer"].value).lower() in item.recommended_service.lower():
                score += 15.0
            ranked.append(
                {
                    "offer": rule["offer"],
                    "score": round(score, 4),
                    "expected_value": rule["value"],
                    "term_hits": term_hits,
                    "pain_hits": pain_hits,
                }
            )
        ranked.sort(key=lambda r: (-float(r["score"]), str(r["offer"])))
        primary = ranked[0]["offer"]
        secondary = ranked[1]["offer"] if len(ranked) > 1 else None
        cross = [r["offer"] for r in ranked[2:5]]
        evidence = [
            f"primary:{primary.value}",
            f"primary_score:{ranked[0]['score']}",
            f"service_hint:{item.recommended_service or 'n/a'}",
        ]
        return OfferRecommendation(
            primary_offer=primary,  # type: ignore[arg-type]
            secondary_offer=secondary,  # type: ignore[arg-type]
            cross_sell=cross,  # type: ignore[arg-type]
            expected_value=str(item.expected_budget or ranked[0]["expected_value"]),
            ranking=[{"offer": r["offer"].value, "score": r["score"], "expected_value": r["expected_value"]} for r in ranked],
            evidence=evidence,
        )
