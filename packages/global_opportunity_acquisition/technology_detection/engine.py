from __future__ import annotations

from global_opportunity_acquisition.models.types import TechnologyHit

TECH_CATALOG: list[tuple[str, str, tuple[str, ...]]] = [
    ("React", "frontend", ("react", "react.js", "reactjs")),
    ("Angular", "frontend", ("angular",)),
    ("Vue", "frontend", ("vue.js", "vuejs", " vue ")),
    ("Next.js", "frontend", ("next.js", "nextjs")),
    ("WordPress", "cms", ("wordpress", "wp-content")),
    ("Shopify", "commerce", ("shopify",)),
    ("Magento", "commerce", ("magento", "adobe commerce")),
    ("Laravel", "backend", ("laravel",)),
    ("Node", "backend", ("nodejs", "node.js", "express")),
    ("Python", "backend", ("python", "django", "fastapi")),
    ("Java", "backend", (" java ", "spring boot")),
    (".NET", "backend", (".net", "asp.net", "dotnet")),
    ("PHP", "backend", (" php ", "php/")),
    ("AWS", "cloud", ("amazonaws", "aws ", "amazon web services")),
    ("Azure", "cloud", ("azure", "microsoft azure")),
    ("GCP", "cloud", ("gcp", "google cloud")),
    ("Cloudflare", "edge", ("cloudflare",)),
    ("Stripe", "payments", ("stripe",)),
    ("HubSpot", "crm", ("hubspot",)),
    ("Salesforce", "crm", ("salesforce",)),
    ("Intercom", "support", ("intercom",)),
    ("Zendesk", "support", ("zendesk",)),
    ("OpenAI SDK", "ai", ("openai", "gpt-4", "gpt-3.5")),
    ("Anthropic SDK", "ai", ("anthropic", "claude")),
    ("LangChain", "ai", ("langchain",)),
    ("Pinecone", "ai", ("pinecone",)),
    ("Redis", "data", ("redis",)),
    ("Postgres", "data", ("postgres", "postgresql")),
]


class TechnologyDetectionEngine:
    def detect(self, texts: list[str]) -> list[TechnologyHit]:
        blob = f" {' '.join(texts).lower()} "
        out: list[TechnologyHit] = []
        for name, category, patterns in TECH_CATALOG:
            hits = [p for p in patterns if p in blob]
            if hits:
                out.append(
                    TechnologyHit(
                        technology=name,
                        category=category,
                        confidence=min(95.0, 70.0 + len(hits) * 8.0),
                        evidence=[f"hits:{','.join(hits[:3])}"],
                    )
                )
        out.sort(key=lambda t: (-t.confidence, t.technology))
        return out
