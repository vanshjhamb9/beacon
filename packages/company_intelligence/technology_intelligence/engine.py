"""Technology Intelligence — detect stack signals from HTML/text evidence."""

from __future__ import annotations

from typing import Any

from company_intelligence.models.types import TechnologyHit, WebsiteCorpus

TECH_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("WordPress", "CMS", ("wp-content", "wordpress")),
    ("Webflow", "CMS", ("webflow",)),
    ("Contentful", "CMS", ("contentful",)),
    ("React", "Framework", ("react", "next.js", "nextjs", "__next")),
    ("Vue", "Framework", ("vue.js", "nuxt")),
    ("Angular", "Framework", ("angular", "ng-")),
    ("Django", "Framework", ("csrfmiddlewaretoken", "django")),
    ("Rails", "Framework", ("rails", "ruby on rails")),
    ("Google Analytics", "Analytics", ("google-analytics", "gtag(", "ga.js", "googletagmanager")),
    ("Segment", "Analytics", ("cdn.segment.com", "analytics.js")),
    ("Mixpanel", "Analytics", ("mixpanel",)),
    ("Cloudflare", "CDN", ("cloudflare", "cf-ray")),
    ("AWS", "Cloud", ("amazonaws.com", "aws", "amazon web services")),
    ("GCP", "Cloud", ("googleapis.com", "google cloud")),
    ("Azure", "Cloud", ("azure", "microsoft azure")),
    ("Salesforce", "CRM", ("salesforce", "force.com")),
    ("HubSpot", "CRM", ("hubspot", "hs-scripts")),
    ("Intercom", "Chat Widget", ("intercom", "widget.intercom")),
    ("Drift", "Chat Widget", ("drift.com", "driftt")),
    ("Stripe", "Payments", ("stripe.com", "js.stripe")),
    ("PayPal", "Payments", ("paypal",)),
    ("Mailchimp", "Email", ("mailchimp", "list-manage")),
    ("SendGrid", "Email", ("sendgrid",)),
    ("Zapier", "Automation", ("zapier",)),
    ("n8n", "Automation", ("n8n",)),
    ("OpenAI", "AI", ("openai", "gpt-4", "gpt-3")),
    ("Anthropic", "LLMs", ("anthropic", "claude")),
    ("Calendly", "Scheduling", ("calendly",)),
    ("Marketo", "Marketing", ("marketo", "munchkin")),
    ("Vercel", "Cloud", ("vercel",)),
)


class TechnologyIntelligenceEngine:
    def detect(self, corpus: WebsiteCorpus, payload: dict[str, Any] | None = None) -> list[TechnologyHit]:
        payload = payload or {}
        blob_parts = [str(payload.get("website_html") or ""), str(payload.get("description") or "")]
        for p in corpus.pages:
            blob_parts.extend([p.text, " ".join(p.navigation), str(p.metadata), str(p.structured_data)])
        blob = " ".join(blob_parts).lower()

        hits: list[TechnologyHit] = []
        for name, category, terms in TECH_RULES:
            term = next((t for t in terms if t in blob), None)
            if not term:
                continue
            hits.append(
                TechnologyHit(
                    technology=name,
                    category=category,
                    version=str(payload.get("tech_versions", {}).get(name) or "UNKNOWN"),
                    confidence=85.0 if term in ("wp-content", "gtag(", "js.stripe") else 75.0,
                    evidence=[f"term:{term}", f"category:{category}"],
                    source="website",
                )
            )

        for raw in payload.get("technologies") or []:
            if isinstance(raw, str) and raw.strip():
                hits.append(
                    TechnologyHit(
                        technology=raw.strip(),
                        category="Declared",
                        confidence=90.0,
                        evidence=[f"payload:{raw}"],
                        source="payload",
                    )
                )
            elif isinstance(raw, dict) and raw.get("technology"):
                hits.append(
                    TechnologyHit(
                        technology=str(raw["technology"]),
                        category=str(raw.get("category") or "Declared"),
                        version=str(raw.get("version") or "UNKNOWN"),
                        confidence=float(raw.get("confidence") or 90),
                        evidence=list(raw.get("evidence") or ["payload"]),
                        source="payload",
                    )
                )

        seen: set[str] = set()
        unique: list[TechnologyHit] = []
        for h in hits:
            key = h.technology.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(h)
        return unique[:40]
