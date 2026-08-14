from __future__ import annotations

from typing import Any

from revenue_data_recovery.models.types import RevenueRecommendationResult, ServiceRecommendation, UNKNOWN


class RevenueRecommendationEngine:
    """Concrete multi-service recommendations from evidence — never generic 'AI Automation' alone."""

    RULES: list[dict[str, Any]] = [
        {
            "service": "Custom AI Customer Support Platform",
            "value": "$35k-$60k",
            "requires_any": ("zendesk", "intercom", "freshdesk", "customer support", "hiring support", "support ticket"),
            "boosts": ("openai", "anthropic", "chatbots", "automation", "llms", "hiring"),
        },
        {
            "service": "Sales Pipeline Automation System",
            "value": "$25k-$45k",
            "requires_any": ("salesforce", "hubspot", "crm", "sales hiring"),
            "boosts": ("automation", "scaling", "expansion"),
        },
        {
            "service": "Cloud Migration & Ops Automation",
            "value": "$40k-$80k",
            "requires_any": ("migration", "cloud", "aws", "azure", "gcp", "legacy software"),
            "boosts": ("hiring developers", "scaling", "automation"),
        },
        {
            "service": "AI Knowledge Assistant for Internal Ops",
            "value": "$30k-$55k",
            "requires_any": ("openai", "anthropic", "gemini", "llms", "llm", "manual process"),
            "boosts": ("digital transformation", "operations", "automation"),
        },
        {
            "service": "ERP / Operations Modernization",
            "value": "$45k-$90k",
            "requires_any": ("erp", "operations", "manual process", "legacy software"),
            "boosts": ("scaling", "expansion", "digital transformation"),
        },
        {
            "service": "International Expansion Tech Stack",
            "value": "$30k-$70k",
            "requires_any": ("international growth", "expansion", "new product"),
            "boosts": ("funding", "scaling", "crm"),
        },
        {
            "service": "Revenue Analytics & Founder Dashboard",
            "value": "$20k-$40k",
            "requires_any": ("funding", "scaling", "analytics"),
            "boosts": ("expansion", "crm"),
        },
    ]

    def recommend(self, payload: dict[str, Any]) -> RevenueRecommendationResult:
        corpus = self._corpus(payload)
        headcount = payload.get("support_headcount") or payload.get("hiring_count")
        out: list[ServiceRecommendation] = []

        for rule in self.RULES:
            hits = [k for k in rule["requires_any"] if k in corpus]
            if not hits:
                continue
            boosts = [k for k in rule["boosts"] if k in corpus]
            confidence = min(95.0, 55.0 + 10.0 * len(hits) + 5.0 * len(boosts))
            reasons = [f"Observed: {h}" for h in hits] + [f"Boost: {b}" for b in boosts]
            if headcount and "support" in rule["service"].lower():
                reasons.append(f"Hiring signal headcount={headcount}")
            # Never emit bare "AI Automation"
            if rule["service"].lower() == "ai automation":
                continue
            out.append(
                ServiceRecommendation(
                    recommended_service=rule["service"],
                    reason=reasons,
                    estimated_value=rule["value"],
                    confidence=round(confidence, 2),
                    evidence=[f"service:{rule['service']}", *reasons],
                )
            )

        out.sort(key=lambda r: r.confidence, reverse=True)
        out = out[:5]
        primary = out[0].recommended_service if out else UNKNOWN
        estimate = out[0].estimated_value if out else UNKNOWN
        return RevenueRecommendationResult(
            recommendations=out,
            primary_service=primary,
            primary_estimate=estimate,
            evidence=[f"recommendations:{len(out)}"] + ([f"primary:{primary}"] if out else ["no_evidence_based_service"]),
        )

    def _corpus(self, payload: dict[str, Any]) -> str:
        parts: list[str] = [
            str(payload.get("narrative") or "").lower(),
            str(payload.get("description") or "").lower(),
            str(payload.get("industry") or "").lower(),
        ]
        for s in payload.get("signals") or []:
            parts.append(str(s.get("value") if isinstance(s, dict) else s).lower())
        for t in payload.get("technologies") or []:
            parts.append(str(t.get("name") if isinstance(t, dict) else t).lower())
        for row in payload.get("timeline") or []:
            if isinstance(row, dict):
                parts.append(str(row.get("summary") or row.get("signal_type") or "").lower())
        # Intent signal names from prior stage
        intent = payload.get("intent_signals") or []
        for s in intent:
            parts.append(str(s.get("signal") if isinstance(s, dict) else s).lower())
        return " ".join(parts)
