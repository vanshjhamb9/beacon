from __future__ import annotations

from global_opportunity_acquisition.models.types import WebsiteProfile
from global_opportunity_acquisition.technology_detection.engine import TechnologyDetectionEngine


class WebsiteAnalysisEngine:
    """Deterministic website analyzer from public HTML/text hints — no private scraping."""

    def analyze(self, *, company_name: str, domain: str | None, hints: list[str]) -> WebsiteProfile:
        blob = " ".join(hints).lower()
        techs = TechnologyDetectionEngine().detect(hints)
        stack = [t.technology for t in techs]
        cms = next((t.technology for t in techs if t.category == "cms"), None)
        framework = next((t.technology for t in techs if t.category == "frontend"), None)
        cloud = next((t.technology for t in techs if t.category == "cloud"), None)
        crm = next((t.technology for t in techs if t.category == "crm"), None)
        payment = next((t.technology for t in techs if t.category == "payments"), None)
        support = next((t.technology for t in techs if t.category == "support"), None)

        ssl = "https" in blob or "ssl" in blob or ("http://" not in blob)

        mobile = any(k in blob for k in ("viewport", "responsive", "mobile-friendly"))
        analytics = any(k in blob for k in ("google-analytics", "gtag", "segment", "mixpanel"))
        chatbot = any(k in blob for k in ("chatbot", "intercom", "drift", "tidio"))
        ai_widget = any(k in blob for k in ("ai widget", "openai", "chat gpt", "ai assistant"))
        booking = any(k in blob for k in ("calendly", "book a demo", "schedule"))
        forms = any(k in blob for k in ("<form", "contact form", "typeform"))
        email_plat = "mailchimp" if "mailchimp" in blob else ("sendgrid" if "sendgrid" in blob else None)
        mkt = "hubspot" if "hubspot" in blob else ("marketo" if "marketo" in blob else None)
        kb = any(k in blob for k in ("knowledge base", "help center", "docs."))
        structured = any(k in blob for k in ("application/ld+json", "schema.org"))
        headers = 70.0 if "content-security-policy" in blob else (40.0 if "x-frame-options" in blob else 20.0)
        perf_issues = []
        if "render-blocking" in blob or "large image" in blob:
            perf_issues.append("performance_hints")
        if "jquery" in blob and "react" not in blob:
            perf_issues.append("legacy_js")
        modernization = 50.0
        if framework in {"React", "Next.js", "Vue"}:
            modernization += 15.0
        if cloud:
            modernization += 10.0
        if ssl:
            modernization += 5.0
        if mobile:
            modernization += 5.0
        if cms == "WordPress" and "woocommerce" not in blob:
            modernization -= 5.0
        modernization = max(0.0, min(100.0, modernization - len(perf_issues) * 8.0))
        opportunity = max(0.0, min(100.0, (100.0 - modernization) * 0.6 + (10.0 if not chatbot else 0) + (8.0 if not ai_widget else 0) + len(perf_issues) * 6.0))
        performance = max(0.0, min(100.0, 75.0 - len(perf_issues) * 12.0 + (5.0 if "cdn" in blob else 0)))
        accessibility = 60.0 + (10.0 if "aria-" in blob else 0) + (10.0 if "alt=" in blob else 0)
        seo = 50.0 + (15.0 if structured else 0) + (10.0 if "meta description" in blob else 0) + (10.0 if mobile else 0)
        hosting = "cloudflare" if "cloudflare" in blob else ("vercel" if "vercel" in blob else None)
        return WebsiteProfile(
            company_name=company_name,
            domain=domain,
            cms=cms,
            framework=framework,
            hosting=hosting,
            cloud=cloud,
            ssl=ssl,
            mobile_responsive=mobile,
            performance_score=round(performance, 2),
            accessibility_score=round(min(100.0, accessibility), 2),
            seo_score=round(min(100.0, seo), 2),
            has_analytics=analytics,
            has_chatbot=chatbot,
            has_ai_widget=ai_widget,
            has_booking=booking,
            has_forms=forms,
            crm=crm,
            email_platform=email_plat,
            marketing_automation=mkt,
            support_software=support,
            knowledge_base=kb,
            payment_provider=payment,
            stack=stack,
            website_age_years=None,
            broken_links_estimate=blob.count("404") + blob.count("broken link"),
            security_headers_score=round(headers, 2),
            structured_data=structured,
            performance_issues=perf_issues,
            modernization_score=round(modernization, 2),
            opportunity_score=round(opportunity, 2),
            evidence=[f"stack:{len(stack)}", f"modernization:{modernization}", "public_hints_only:true"],
        )
