from __future__ import annotations

from sales_intelligence.models.types import OfferType, SalesIntelligenceInput, TrustAsset, TrustBuilderResult


CASE_LIBRARY: dict[str, list[tuple[str, str]]] = {
    "Healthcare": [("case", "Clinical ops automation for mid-market clinic"), ("testimonial", "Cut intake time 40%")],
    "Ecommerce": [("case", "Support deflection for DTC brand"), ("portfolio", "WhatsApp commerce assistant")],
    "SaaS": [("case", "Multi-tenant AI feature for B2B SaaS"), ("success", "Shipped MVP in 8 weeks")],
    "Fintech": [("case", "Onboarding automation under compliance constraints"), ("testimonial", "Passed security review first cycle")],
    "default": [("case", "Custom AI delivery for growth-stage company"), ("portfolio", "Automation + chatbot stack")],
}


class TrustBuilderEngine:
    def build(self, item: SalesIntelligenceInput, *, primary_offer: OfferType | None = None) -> TrustBuilderResult:
        industry = item.industry or "default"
        library = CASE_LIBRARY.get(industry, CASE_LIBRARY["default"])
        case_studies: list[TrustAsset] = []
        portfolio: list[TrustAsset] = []
        testimonials: list[TrustAsset] = []
        success: list[TrustAsset] = []
        for kind, title in library:
            asset = TrustAsset(
                kind=kind,
                title=title,
                relevance=85.0 if industry != "default" else 70.0,
                evidence=[f"industry:{industry}", f"offer:{primary_offer.value if primary_offer else 'n/a'}"],
            )
            if kind == "case":
                case_studies.append(asset)
            elif kind == "portfolio":
                portfolio.append(asset)
            elif kind == "testimonial":
                testimonials.append(asset)
            else:
                success.append(asset)
        if primary_offer:
            portfolio.append(
                TrustAsset(
                    kind="portfolio",
                    title=f"{primary_offer.value} reference architecture",
                    relevance=80.0,
                    evidence=[f"offer:{primary_offer.value}"],
                )
            )
        return TrustBuilderResult(
            case_studies=case_studies,
            portfolio_items=portfolio,
            testimonials=testimonials,
            industries_served=sorted({industry, "SaaS", "Ecommerce", "Healthcare"}),
            technology_stack=list(item.technologies)[:12] or ["Python", "Next.js", "LLM"],
            success_stories=success or case_studies[:1],
        )
