"""Service Match Engine v3 — Urban Webworks offerings vs company evidence."""

from __future__ import annotations

from typing import Any

from company_intelligence.models.types import (
    BuyingSignal,
    CompanyBusinessProfile,
    IcpProfile,
    ProductCatalog,
    ServiceMatch,
    TechnologyHit,
    WebsiteCorpus,
)

URBAN_WEBWORKS_SERVICES: tuple[dict[str, Any], ...] = (
    {"service": "AI Automation", "terms": ("automation", "workflow", "rpa", "automate"), "value": "$25k-$80k"},
    {"service": "AI Agents", "terms": ("agent", "agents", "llm", "openai", "copilot"), "value": "$40k-$120k"},
    {"service": "Custom Software", "terms": ("custom software", "bespoke", "internal tools"), "value": "$30k-$100k"},
    {"service": "Enterprise Software", "terms": ("enterprise", "sso", "soc 2", "compliance"), "value": "$60k-$200k"},
    {"service": "CRM", "terms": ("crm", "salesforce", "hubspot", "pipeline"), "value": "$20k-$70k"},
    {"service": "ERP", "terms": ("erp", "inventory", "netsuite", "sap"), "value": "$50k-$180k"},
    {"service": "SaaS", "terms": ("saas", "subscription", "multi-tenant", "platform"), "value": "$35k-$110k"},
    {"service": "Marketplace", "terms": ("marketplace", "two-sided", "vendors"), "value": "$40k-$130k"},
    {"service": "Website", "terms": ("website", "wordpress", "webflow", "landing"), "value": "$8k-$40k"},
    {"service": "Mobile App", "terms": ("mobile", "ios", "android", "react native"), "value": "$25k-$90k"},
    {"service": "Cloud", "terms": ("aws", "azure", "gcp", "cloud migration"), "value": "$30k-$100k"},
    {"service": "DevOps", "terms": ("devops", "ci/cd", "kubernetes", "docker"), "value": "$25k-$85k"},
    {"service": "Data Engineering", "terms": ("data pipeline", "warehouse", "etl", "analytics"), "value": "$35k-$120k"},
    {"service": "Integrations", "terms": ("integration", "api", "zapier", "webhook"), "value": "$15k-$60k"},
    {"service": "Dashboards", "terms": ("dashboard", "reporting", "bi", "metrics"), "value": "$15k-$55k"},
    {"service": "Automation", "terms": ("automate", "orchestration", "ops automation"), "value": "$20k-$75k"},
    {"service": "MVP Development", "terms": ("mvp", "prototype", "launch fast", "startup"), "value": "$15k-$50k"},
    {"service": "Maintenance", "terms": ("maintenance", "support plan", "legacy"), "value": "$5k-$25k/mo"},
    {"service": "Digital Transformation", "terms": ("digital transformation", "modernize", "legacy system"), "value": "$50k-$200k"},
)


class ServiceMatchEngineV3:
    def match(
        self,
        *,
        corpus: WebsiteCorpus,
        business: CompanyBusinessProfile,
        products: ProductCatalog,
        icp: IcpProfile,
        technologies: list[TechnologyHit],
        signals: list[BuyingSignal],
        payload: dict[str, Any] | None = None,
    ) -> list[ServiceMatch]:
        payload = payload or {}
        blob = " ".join(
            [
                business.description.value,
                business.industry.value,
                business.primary_product.value,
                icp.primary_icp.value,
                " ".join(p.value for p in products.capabilities),
                " ".join(t.technology for t in technologies),
                " ".join(s.signal_type for s in signals),
                " ".join(p.text[:1500] for p in corpus.pages[:8]),
                str(payload.get("description") or ""),
            ]
        ).lower()

        matches: list[ServiceMatch] = []
        for item in URBAN_WEBWORKS_SERVICES:
            terms: tuple[str, ...] = item["terms"]
            hits = [t for t in terms if t in blob]
            if not hits:
                continue
            need = min(100.0, 40.0 + 15.0 * len(hits))
            if any(s.signal_type in {"Hiring", "AI Hiring", "Scaling", "Product Launch"} for s in signals):
                need = min(100.0, need + 10.0)
            if business.enterprise_status.value != "UNKNOWN" and "enterprise" in item["service"].lower():
                need = min(100.0, need + 8.0)
            conf = min(95.0, 60.0 + 10.0 * len(hits))
            matches.append(
                ServiceMatch(
                    service=str(item["service"]),
                    need_score=round(need, 2),
                    confidence=round(conf, 2),
                    evidence=[f"term:{h}" for h in hits[:4]],
                    reason=f"Evidence of {', '.join(hits[:3])} aligns with {item['service']}",
                    potential_value=str(item["value"]),
                )
            )

        matches.sort(key=lambda m: (m.need_score, m.confidence), reverse=True)
        return matches[:12]
