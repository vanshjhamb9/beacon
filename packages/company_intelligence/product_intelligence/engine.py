"""Product Intelligence — catalog products/solutions/capabilities from evidence."""

from __future__ import annotations

import re
from typing import Any

from company_intelligence.models.types import UNKNOWN, AttributedValue, ProductCatalog, WebsiteCorpus


def _attr(value: str, *, source: str, page: str | None = None, confidence: float = 70) -> AttributedValue:
    if not value or value == UNKNOWN:
        return AttributedValue()
    return AttributedValue(
        value=value[:240],
        confidence=confidence,
        source=source,
        page=page,
        excerpt=value[:160],
        evidence=[f"{source}:{value[:60]}"],
    )


class ProductIntelligenceEngine:
    def extract(self, corpus: WebsiteCorpus, payload: dict[str, Any] | None = None) -> ProductCatalog:
        payload = payload or {}
        products: list[AttributedValue] = []
        solutions: list[AttributedValue] = []
        features: list[AttributedValue] = []
        plans: list[AttributedValue] = []
        integrations: list[AttributedValue] = []
        capabilities: list[AttributedValue] = []
        pricing = AttributedValue()
        free_trial = AttributedValue()
        enterprise = AttributedValue()
        api = AttributedValue()
        marketplace = AttributedValue()
        mobile = AttributedValue()
        platform = AttributedValue()

        for page in corpus.pages:
            path = page.path.lower()
            blob = f"{page.title} {' '.join(page.headings)} {page.text}".lower()
            if any(x in path for x in ("/product", "/solution")):
                for h in page.headings[:8]:
                    if h and h != UNKNOWN:
                        (products if "product" in path else solutions).append(
                            _attr(h, source="heading", page=page.url, confidence=82)
                        )
            if "/pricing" in path or "pricing" in blob:
                pricing = _attr(page.title if page.title != UNKNOWN else "Pricing page", source="pricing_page", page=page.url, confidence=85)
                if "free trial" in blob or "start free" in blob:
                    free_trial = _attr("Yes", source="pricing_page", page=page.url, confidence=88)
                for plan in ("starter", "pro", "business", "enterprise", "free"):
                    if plan in blob:
                        plans.append(_attr(plan.title(), source="pricing_page", page=page.url, confidence=75))
            if "/enterprise" in path or "enterprise" in blob:
                enterprise = _attr("Enterprise offering", source="enterprise_page", page=page.url, confidence=80)
            if "/api" in path or "api" in blob or "/developers" in path or "/docs" in path:
                api = _attr("API available", source="api_docs", page=page.url, confidence=85)
            if "marketplace" in blob:
                marketplace = _attr("Marketplace", source="page_text", page=page.url, confidence=78)
            if "ios" in blob or "android" in blob or "mobile app" in blob:
                mobile = _attr("Mobile apps", source="page_text", page=page.url, confidence=75)
            if "platform" in blob:
                platform = _attr("Platform", source="page_text", page=page.url, confidence=70)
            if "/integration" in path or "integrat" in blob:
                for name in ("salesforce", "hubspot", "slack", "zapier", "shopify", "stripe", "aws"):
                    if name in blob:
                        integrations.append(_attr(name.title(), source="integrations", page=page.url, confidence=80))
            for cue in ("automation", "ai agents", "analytics", "workflow", "dashboard", "crm"):
                if cue in blob:
                    capabilities.append(_attr(cue.title(), source="capability", page=page.url, confidence=72))
            for h in page.headings:
                if re.search(r"\b(feature|capability|benefit)\b", h, re.I):
                    features.append(_attr(h, source="heading", page=page.url, confidence=70))

        # Payload overrides (never invent if missing)
        for name in payload.get("products") or []:
            products.append(_attr(str(name), source="payload", confidence=90))

        # Dedupe
        def dedupe(items: list[AttributedValue]) -> list[AttributedValue]:
            seen: set[str] = set()
            out: list[AttributedValue] = []
            for item in items:
                key = item.value.lower()
                if key in seen or item.value == UNKNOWN:
                    continue
                seen.add(key)
                out.append(item)
            return out[:20]

        products, solutions, features, plans, integrations, capabilities = (
            dedupe(products),
            dedupe(solutions),
            dedupe(features),
            dedupe(plans),
            dedupe(integrations),
            dedupe(capabilities),
        )
        return ProductCatalog(
            products=products,
            solutions=solutions,
            features=features,
            plans=plans,
            pricing=pricing,
            free_trial=free_trial,
            enterprise=enterprise,
            api=api,
            marketplace=marketplace,
            mobile_apps=mobile,
            platform=platform,
            integrations=integrations,
            capabilities=capabilities,
            evidence=[
                f"products:{len(products)}",
                f"solutions:{len(solutions)}",
                f"integrations:{len(integrations)}",
            ],
        )
