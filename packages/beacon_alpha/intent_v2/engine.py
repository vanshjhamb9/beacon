from __future__ import annotations

from typing import Any

from beacon_alpha.models.types import IntentScores, IntentV2Result, ServiceBucket, UNKNOWN

BUCKET_KEYWORDS: dict[ServiceBucket, tuple[str, ...]] = {
    ServiceBucket.AI_AUTOMATION: (
        "repetitive",
        "manual work",
        "manual process",
        "operations",
        "workflows",
        "workflow",
        "agents",
        "ai integration",
        "internal tools",
        "automation",
        "openai",
        "anthropic",
        "llm",
        "chatbot",
    ),
    ServiceBucket.SAAS_DEVELOPMENT: (
        "startup",
        "mvp",
        "build product",
        "web platform",
        "portal",
        "dashboard",
        "marketplace",
        "subscription",
        "saas",
    ),
    ServiceBucket.CUSTOM_SOFTWARE: (
        "erp",
        "crm",
        "inventory",
        "booking",
        "pos",
        "hrms",
        "internal software",
        "custom software",
    ),
    ServiceBucket.MOBILE_APP: (
        "ios",
        "android",
        "flutter",
        "react native",
        "customer app",
        "employee app",
        "mobile app",
    ),
    ServiceBucket.ECOMMERCE: (
        "shopify",
        "woocommerce",
        "magento",
        "conversion",
        "checkout",
        "ecommerce",
        "e-commerce",
    ),
    ServiceBucket.ENTERPRISE: (
        "digital transformation",
        "legacy modernization",
        "legacy",
        "cloud migration",
        "workflow automation",
        "enterprise",
    ),
}

SERVICE_LABELS = {
    ServiceBucket.AI_AUTOMATION: "Custom AI Automation Platform",
    ServiceBucket.SAAS_DEVELOPMENT: "SaaS Product Build / MVP",
    ServiceBucket.CUSTOM_SOFTWARE: "Custom Business Software (ERP/CRM)",
    ServiceBucket.MOBILE_APP: "Mobile App Development",
    ServiceBucket.ECOMMERCE: "E-commerce Growth & Automation",
    ServiceBucket.ENTERPRISE: "Enterprise Modernization & Migration",
}

BUDGET_BY_BUCKET = {
    ServiceBucket.AI_AUTOMATION: "$35k-$60k",
    ServiceBucket.SAAS_DEVELOPMENT: "$40k-$90k",
    ServiceBucket.CUSTOM_SOFTWARE: "$45k-$100k",
    ServiceBucket.MOBILE_APP: "$30k-$70k",
    ServiceBucket.ECOMMERCE: "$25k-$55k",
    ServiceBucket.ENTERPRISE: "$60k-$150k",
}


class IntentV2Engine:
    """Rule 4 — classify into high-value service buckets with structured scores."""

    def classify(self, payload: dict[str, Any]) -> IntentV2Result:
        corpus = self._corpus(payload)
        buckets: dict[str, float] = {}
        evidence: list[str] = []

        for bucket, keys in BUCKET_KEYWORDS.items():
            hits = [k for k in keys if k in corpus]
            score = min(100.0, 18.0 * len(hits))
            buckets[bucket.value] = round(score, 2)
            if hits:
                evidence.append(f"bucket:{bucket.value}:{','.join(hits[:4])}")

        primary = ServiceBucket.UNKNOWN
        best = 0.0
        for name, score in buckets.items():
            if score > best:
                best = score
                primary = ServiceBucket(name)

        scores = self._scores(corpus, payload, primary, best)
        pain = self._pain_phrase(corpus, primary)
        why_now = self._why_now(corpus, scores)
        budget = BUDGET_BY_BUCKET.get(primary, UNKNOWN)
        if payload.get("estimated_budget"):
            budget = str(payload["estimated_budget"])

        return IntentV2Result(
            primary_bucket=primary,
            buckets=buckets,
            best_service=SERVICE_LABELS.get(primary, UNKNOWN) if primary != ServiceBucket.UNKNOWN else UNKNOWN,
            scores=scores,
            why_now=why_now,
            pain=pain,
            estimated_budget=budget,
            evidence=evidence or ["no_bucket_match"],
        )

    def _scores(self, corpus: str, payload: dict[str, Any], primary: ServiceBucket, bucket_score: float) -> IntentScores:
        pain = min(100.0, bucket_score + (15.0 if any(x in corpus for x in ("manual", "legacy", "pain", "bottleneck")) else 0))
        budget = 40.0
        if any(x in corpus for x in ("funding", "series", "enterprise", "raised")):
            budget += 30.0
        if primary == ServiceBucket.ENTERPRISE:
            budget += 20.0
        urgency = 20.0
        if any(x in corpus for x in ("hiring", "urgent", "this quarter", "asap", "launching")):
            urgency += 40.0
        if any(x in corpus for x in ("careers", "open role", "job")):
            urgency += 20.0
        tech_gap = 25.0
        if any(x in corpus for x in ("legacy", "migration", "manual process", "spreadsheet")):
            tech_gap += 35.0
        ai_adoption = 15.0
        if any(x in corpus for x in ("openai", "anthropic", "llm", "ai ", "agents", "chatbot")):
            ai_adoption += 50.0
        buying = min(100.0, (pain + urgency + bucket_score) / 3.0)
        if buying >= 70:
            window = "0-30 days"
        elif buying >= 45:
            window = "30-60 days"
        elif buying >= 25:
            window = "60-90 days"
        else:
            window = "90+ days / research"
        return IntentScores(
            pain_score=round(min(100.0, pain), 2),
            budget_score=round(min(100.0, budget), 2),
            urgency=round(min(100.0, urgency), 2),
            technology_gap=round(min(100.0, tech_gap), 2),
            ai_adoption=round(min(100.0, ai_adoption), 2),
            buying_signal=round(buying, 2),
            decision_window=window,
            evidence=[f"buying:{round(buying, 2)}", f"window:{window}"],
        )

    def _pain_phrase(self, corpus: str, primary: ServiceBucket) -> str:
        if "manual" in corpus:
            return "Repetitive manual work slowing operations"
        if "legacy" in corpus:
            return "Legacy systems blocking growth"
        if "hiring" in corpus and "support" in corpus:
            return "Support hiring pressure — automation opportunity"
        if primary == ServiceBucket.SAAS_DEVELOPMENT:
            return "Need to ship / scale a product platform"
        if primary == ServiceBucket.ECOMMERCE:
            return "Checkout / conversion / store ops friction"
        if primary == ServiceBucket.UNKNOWN:
            return UNKNOWN
        return f"Observed need aligned to {primary.value}"

    def _why_now(self, corpus: str, scores: IntentScores) -> str:
        bits = []
        if scores.urgency >= 50:
            bits.append("Active hiring / urgency signals")
        if scores.ai_adoption >= 50:
            bits.append("AI stack already in motion")
        if scores.technology_gap >= 50:
            bits.append("Clear technology gap")
        if "funding" in corpus:
            bits.append("Recent funding / budget capacity")
        return "; ".join(bits) if bits else "Observed opportunity evidence — review before outreach"

    def _corpus(self, payload: dict[str, Any]) -> str:
        parts = [
            str(payload.get("narrative") or ""),
            str(payload.get("description") or ""),
            str(payload.get("business_description") or ""),
            str(payload.get("industry") or ""),
            str(payload.get("use_case") or ""),
        ]
        for s in payload.get("signals") or []:
            parts.append(str(s.get("value") if isinstance(s, dict) else s))
        for t in payload.get("technologies") or []:
            parts.append(str(t.get("name") if isinstance(t, dict) else t))
        for row in payload.get("timeline") or []:
            if isinstance(row, dict):
                parts.append(str(row.get("summary") or row.get("signal_type") or ""))
        for item in payload.get("evidence") or []:
            if isinstance(item, dict):
                parts.append(str(item.get("summary") or item.get("text") or ""))
            else:
                parts.append(str(item))
        return " ".join(parts).lower()
