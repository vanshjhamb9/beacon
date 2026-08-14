from __future__ import annotations

from typing import Any

from sales_readiness.models.types import AttributedField, TechnologyReadiness, UNKNOWN

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "CRM": ("salesforce", "hubspot", "pipedrive", "zoho crm", "dynamics"),
    "CMS": ("wordpress", "contentful", "webflow", "drupal", "ghost"),
    "Hosting": ("vercel", "netlify", "heroku", "digitalocean", "godaddy"),
    "Cloud": ("aws", "azure", "gcp", "google cloud", "cloudflare"),
    "Payments": ("stripe", "braintree", "adyen", "paypal", "square"),
    "Analytics": ("ga4", "google analytics", "mixpanel", "amplitude", "segment"),
    "AI": ("openai", "anthropic", "gemini", "langchain", "huggingface", "cohere"),
    "Automation": ("zapier", "make.com", "n8n", "workato", "tray.io"),
    "Support": ("zendesk", "intercom", "freshdesk", "gorgias", "helpscout"),
    "ERP": ("sap", "netsuite", "oracle erp", "odoo", "microsoft dynamics 365"),
}


class TechnologyReadinessEngine:
    """Map observed tech list into CRM/CMS/… categories — never invent stack items."""

    def evaluate(self, payload: dict[str, Any]) -> TechnologyReadiness:
        techs = payload.get("technologies") or payload.get("technology_stack") or []
        source = str(payload.get("tech_source") or payload.get("source") or "technology_profile")
        collected = payload.get("collected_at") or payload.get("last_seen_at")
        categories: dict[str, list[AttributedField]] = {k: [] for k in CATEGORY_KEYWORDS}
        evidence: list[str] = []

        normalized: list[tuple[str, float | None]] = []
        for item in techs:
            if isinstance(item, dict):
                name = str(item.get("name") or item.get("technology") or "").strip()
                conf = item.get("confidence")
                src = str(item.get("source") or source)
                if name:
                    normalized.append((name, float(conf) if conf is not None else None))
                    for cat, keys in CATEGORY_KEYWORDS.items():
                        if any(k in name.lower() for k in keys):
                            categories[cat].append(
                                AttributedField.of(
                                    name,
                                    source=src,
                                    collected_at=collected,
                                    confidence=float(conf) if conf is not None else 80.0,
                                    evidence=[f"matched:{cat}"],
                                )
                            )
                            evidence.append(f"{cat}:{name}")
            else:
                name = str(item).strip()
                if not name:
                    continue
                normalized.append((name, None))
                for cat, keys in CATEGORY_KEYWORDS.items():
                    if any(k in name.lower() for k in keys):
                        categories[cat].append(
                            AttributedField.of(
                                name,
                                source=source,
                                collected_at=collected,
                                confidence=80.0,
                                evidence=[f"matched:{cat}"],
                            )
                        )
                        evidence.append(f"{cat}:{name}")

        filled = sum(1 for v in categories.values() if v)
        maturity = round(min(100.0, filled * 10.0 + min(20.0, len(normalized) * 2.0)), 2)
        if not normalized:
            evidence.append("no_technologies_observed")
        return TechnologyReadiness(categories=categories, maturity_score=maturity, evidence=evidence or ["empty"])
