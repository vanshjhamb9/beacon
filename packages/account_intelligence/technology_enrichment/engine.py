from __future__ import annotations

from datetime import UTC, datetime

from account_intelligence.models.types import AccountIntelligenceInput, TechnologyProfile, WebsiteEnrichment

TECH_MAP: dict[str, tuple[str, ...]] = {
    "frontend": ("react", "vue", "angular", "next.js", "svelte"),
    "backend": ("node", "python", "django", "fastapi", "java", "laravel", ".net", "php", "go "),
    "database": ("postgres", "mysql", "mongodb", "redis"),
    "cloud": ("aws", "azure", "gcp", "google cloud"),
    "hosting": ("vercel", "netlify", "heroku", "digitalocean"),
    "cdn": ("cloudflare", "fastly", "akamai"),
    "crm": ("salesforce", "hubspot", "pipedrive"),
    "erp": ("sap", "netsuite", "odoo"),
    "analytics": ("google-analytics", "gtag", "mixpanel", "amplitude", "segment"),
    "marketing_automation": ("marketo", "mailchimp", "klaviyo", "hubspot"),
    "payment_gateway": ("stripe", "paypal", "braintree", "razorpay"),
    "customer_support": ("zendesk", "intercom", "freshdesk", "helpscout"),
    "ai_stack": ("openai", "anthropic", "langchain", "pinecone", "huggingface"),
    "llm_stack": ("gpt-4", "claude", "llama", "mistral"),
    "security_stack": ("okta", "auth0", "cloudflare zero trust", "snyk"),
    "devops": ("docker", "kubernetes", "terraform"),
    "monitoring": ("datadog", "new relic", "sentry", "grafana"),
    "cicd": ("github actions", "gitlab ci", "circleci", "jenkins"),
    "search": ("elasticsearch", "algolia", "opensearch"),
    "caching": ("redis", "memcached", "varnish"),
    "storage": ("s3", "gcs", "azure blob"),
    "cms": ("wordpress", "contentful", "sanity", "strapi"),
    "framework": ("next.js", "django", "rails", "spring", "laravel"),
}


class TechnologyEnrichmentEngine:
    def enrich(self, item: AccountIntelligenceInput) -> TechnologyProfile:
        now = item.now or datetime.now(UTC)
        blob = " ".join(item.html_hints + item.tech_hints).lower()
        buckets: dict[str, list[str]] = {k: [] for k in TECH_MAP}
        for category, patterns in TECH_MAP.items():
            for p in patterns:
                if p in blob:
                    label = p.strip().title() if p != ".net" else ".NET"
                    if label not in buckets[category]:
                        buckets[category].append(label)
        filled = sum(1 for v in buckets.values() if v)
        conf = min(95.0, 30.0 + filled * 4.0)
        return TechnologyProfile(
            **buckets,
            confidence=round(conf, 2),
            source="public_hints",
            last_verified=now,
            evidence=[f"categories:{filled}", "public_hints_only:true"],
        )


class CRMDetectionEngine:
    def detect(self, tech: TechnologyProfile) -> list[str]:
        return list(tech.crm)


class MarketingStackEngine:
    def detect(self, tech: TechnologyProfile) -> list[str]:
        return list(dict.fromkeys(tech.marketing_automation + tech.analytics))


class SecurityStackEngine:
    def detect(self, tech: TechnologyProfile) -> list[str]:
        return list(tech.security_stack)


class CloudStackEngine:
    def detect(self, tech: TechnologyProfile) -> list[str]:
        return list(dict.fromkeys(tech.cloud + tech.hosting + tech.cdn))


class AIStackEngine:
    def detect(self, tech: TechnologyProfile) -> list[str]:
        return list(dict.fromkeys(tech.ai_stack + tech.llm_stack))


class WebsiteEnrichmentEngine:
    def enrich(self, item: AccountIntelligenceInput) -> WebsiteEnrichment:
        now = item.now or datetime.now(UTC)
        blob = " ".join(item.html_hints).lower()
        ssl = "https" in blob or "ssl" in blob or bool(item.website and item.website.startswith("https"))
        mobile = any(k in blob for k in ("viewport", "responsive", "mobile"))
        schema = "schema.org" in blob or "ld+json" in blob
        headers = 70.0 if "content-security-policy" in blob else (40.0 if "x-frame-options" in blob else 20.0)
        forms = any(k in blob for k in ("<form", "contact form", "typeform"))
        booking = any(k in blob for k in ("calendly", "book a demo", "schedule"))
        contact = "contact" in blob
        pricing = "pricing" in blob
        blog = "blog" in blob
        resources = "resources" in blob or "whitepaper" in blob
        cases = "case study" in blob or "case studies" in blob
        testimonials = "testimonial" in blob
        careers = "careers" in blob or "we're hiring" in blob
        kb = "knowledge base" in blob or "help center" in blob
        support = "support portal" in blob or "support." in blob
        ai_widgets = any(k in blob for k in ("ai widget", "ai assistant", "chatgpt"))
        chatbot = any(k in blob for k in ("chatbot", "intercom", "drift"))
        automation = "automation" in blob or "zapier" in blob
        seo = 40.0 + (20.0 if schema else 0) + (15.0 if mobile else 0) + (10.0 if "meta description" in blob else 0)
        a11y = 50.0 + (15.0 if "aria-" in blob else 0) + (10.0 if "alt=" in blob else 0)
        perf = 70.0 - (15.0 if "render-blocking" in blob else 0) - (10.0 if "large image" in blob else 0)
        cwv = max(0.0, min(100.0, perf - 5.0))
        flags = sum(
            [
                ssl,
                mobile,
                schema,
                forms,
                booking,
                contact,
                pricing,
                blog,
                resources,
                cases,
                testimonials,
                careers,
                kb,
                support,
                ai_widgets,
                chatbot,
                automation,
            ]
        )
        return WebsiteEnrichment(
            seo_score=round(min(100.0, seo), 2),
            accessibility_score=round(min(100.0, a11y), 2),
            core_web_vitals=round(cwv, 2),
            performance_score=round(max(0.0, perf), 2),
            ssl=ssl,
            schema_markup=schema,
            security_headers_score=round(headers, 2),
            mobile=mobile,
            forms=forms,
            booking=booking,
            contact_page=contact,
            pricing=pricing,
            blog=blog,
            resources=resources,
            case_studies=cases,
            testimonials=testimonials,
            careers=careers,
            knowledge_base=kb,
            support_portal=support,
            ai_widgets=ai_widgets,
            chatbot=chatbot,
            automation=automation,
            confidence=round(min(95.0, 25.0 + flags * 3.0), 2),
            source="public_hints",
            last_verified=now,
            evidence=[f"flags:{flags}", "public_hints_only:true"],
        )
