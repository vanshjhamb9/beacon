from __future__ import annotations

from typing import Any

from sales_readiness.models.types import ServiceRecommendation, UNKNOWN


class ServiceMatchingEngineV2:
    """Concrete service recommendations from observed evidence — never generic 'AI Automation' alone."""

    RULES: list[dict[str, Any]] = [
        {
            "service": "Custom AI Customer Support Platform",
            "value": "$35k-$60k",
            "requires_any": ("zendesk", "intercom", "freshdesk", "customer support", "support hiring"),
            "boosts": ("openai", "anthropic", "automation", "hiring"),
        },
        {
            "service": "Sales Pipeline Automation System",
            "value": "$25k-$45k",
            "requires_any": ("salesforce", "hubspot", "sales hiring", "crm"),
            "boosts": ("automation", "scaling", "zapier"),
        },
        {
            "service": "Cloud Migration & Ops Automation",
            "value": "$40k-$80k",
            "requires_any": ("migration", "cloud migration", "aws", "azure", "gcp"),
            "boosts": ("engineering hiring", "scaling"),
        },
        {
            "service": "AI Knowledge Assistant for Internal Ops",
            "value": "$30k-$55k",
            "requires_any": ("openai", "anthropic", "gemini", "ai"),
            "boosts": ("digital transformation", "automation"),
        },
        {
            "service": "Revenue Analytics & Founder Dashboard",
            "value": "$20k-$40k",
            "requires_any": ("mixpanel", "amplitude", "segment", "analytics", "funding"),
            "boosts": ("scaling", "expansion"),
        },
    ]

    def match(self, payload: dict[str, Any]) -> list[ServiceRecommendation]:
        techs = [str(t.get("name") if isinstance(t, dict) else t).lower() for t in (payload.get("technologies") or [])]
        signals = [str(s.get("value") if isinstance(s, dict) else s).lower() for s in (payload.get("signals") or [])]
        narrative = str(payload.get("narrative") or "").lower()
        industry = str(payload.get("industry") or "").lower()
        corpus = " ".join(techs + signals + [narrative, industry])

        out: list[ServiceRecommendation] = []
        for rule in self.RULES:
            req = rule["requires_any"]
            hits = [k for k in req if k in corpus]
            if not hits:
                continue
            boosts = [k for k in rule["boosts"] if k in corpus]
            confidence = min(95.0, 55.0 + 10.0 * len(hits) + 5.0 * len(boosts))
            reasons = [f"Observed: {h}" for h in hits] + [f"Boost: {b}" for b in boosts]
            if payload.get("support_headcount"):
                reasons.append(f"Hiring signal headcount={payload['support_headcount']}")
            out.append(
                ServiceRecommendation(
                    recommended_service=rule["service"],
                    reason=reasons or ["matched_rule"],
                    estimated_value=rule["value"],
                    confidence=round(confidence, 2),
                    evidence=[f"service:{rule['service']}", *reasons],
                )
            )

        out.sort(key=lambda r: r.confidence, reverse=True)
        if not out:
            # Still never fabricate a pitch — return empty with UNKNOWN sentinel via caller
            return []
        return out[:5]
