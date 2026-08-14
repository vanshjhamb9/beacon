from __future__ import annotations

from lead_enrichment.models.types import (
    DnsMxResult,
    EnrichmentOpportunityInput,
    EnrichmentSourceType,
    TechnologyEntry,
    WebsiteFetchResult,
)

_JS_LIBRARY_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("react", "frameworks", "react"),
    ("next", "frameworks", "next"),
    ("vue", "frameworks", "vue"),
    ("angular", "frameworks", "angular"),
    ("jquery", "frameworks", "jquery"),
    ("gtag", "analytics", "Google Analytics"),
    ("googletagmanager", "analytics", "Google Tag Manager"),
    ("segment", "analytics", "Segment"),
    ("hotjar", "analytics", "Hotjar"),
    ("mixpanel", "analytics", "Mixpanel"),
    ("hubspot", "marketing_tools", "HubSpot"),
    ("marketo", "marketing_tools", "Marketo"),
    ("intercom", "support_tools", "Intercom"),
    ("zendesk", "support_tools", "Zendesk"),
    ("crisp", "support_tools", "Crisp"),
    ("stripe", "payment_gateways", "Stripe"),
    ("paypal", "payment_gateways", "PayPal"),
    ("shopify", "ecommerce", "Shopify"),
    ("woocommerce", "ecommerce", "WooCommerce"),
    ("wordpress", "cms", "WordPress"),
    ("contentful", "cms", "Contentful"),
    ("webflow", "cms", "Webflow"),
    ("cloudflare", "hosting", "Cloudflare"),
    ("amazonaws", "hosting", "AWS"),
    ("vercel", "hosting", "Vercel"),
    ("netlify", "hosting", "Netlify"),
)


class TechnologyConnector:
    name = "technology_intelligence"

    def collect(
        self,
        item: EnrichmentOpportunityInput,
        website: WebsiteFetchResult | None = None,
        dns: DnsMxResult | None = None,
    ) -> list[TechnologyEntry]:
        technologies: list[TechnologyEntry] = []
        seen: set[str] = set()

        for signal in item.technology_signals:
            name = str(signal.get("technology") or signal.get("name") or "").strip()
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            technologies.append(
                TechnologyEntry(
                    name=name,
                    category=str(signal.get("category") or "technology_signals"),
                    confidence=float(signal.get("confidence") or 70.0),
                    source=EnrichmentSourceType.BEACON_CONTEXT,
                    signal=str(signal.get("adoption_signal") or "context_signal"),
                )
            )

        stack = item.context_intelligence.get("technology_stack")
        if isinstance(stack, list):
            for entry in stack:
                name = str(entry).strip()
                if not name or name.lower() in seen:
                    continue
                seen.add(name.lower())
                technologies.append(
                    TechnologyEntry(
                        name=name,
                        category="technology_stack",
                        confidence=72.0,
                        source=EnrichmentSourceType.BEACON_CONTEXT,
                        signal="company_dna",
                    )
                )

        if website:
            for page in website.pages:
                corpus = page.html.lower()
                for needle, category, label in _JS_LIBRARY_PATTERNS:
                    if needle in corpus and label.lower() not in seen:
                        seen.add(label.lower())
                        technologies.append(
                            TechnologyEntry(
                                name=label,
                                category=category,
                                confidence=78.0,
                                source=EnrichmentSourceType.PUBLIC_JS,
                                source_url=page.url,
                                signal=f"detected_on_{page.page_type}",
                            )
                        )

        if dns and dns.mail_provider and dns.mail_provider.lower() not in seen:
            seen.add(dns.mail_provider.lower())
            technologies.append(
                TechnologyEntry(
                    name=dns.mail_provider,
                    category="email_infrastructure",
                    confidence=dns.confidence,
                    source=EnrichmentSourceType.DNS_MX,
                    signal="mx_record",
                )
            )
        return technologies
