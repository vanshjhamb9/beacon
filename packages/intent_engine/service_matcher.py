"""Service Matcher — maps detected intent to specific Inowix services.

Given an intent signal and a company profile, determines which
Inowix service(s) solve the company's stated problem.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.opportunity_intelligence.canonical import (
    BusinessUnit,
    EvidenceConfidence,
    ServiceMatch,
)


# ============================================================
# SERVICE CATALOG
# ============================================================

SERVICE_CATALOG: dict[str, dict] = {
    # --- COMAI ---
    "comai_whatsapp": {
        "business_unit": BusinessUnit.COMAI,
        "name": "COMAI WhatsApp Automation",
        "description": "AI-powered WhatsApp sales, support, and lead capture",
        "keywords": ["whatsapp", "whatsapp automation", "whatsapp bot", "whatsapp sales", "whatsapp support"],
        "problem_solved": "Manual WhatsApp responses, lost leads, slow customer support",
    },
    "comai_chatbot": {
        "business_unit": BusinessUnit.COMAI,
        "name": "COMAI AI Chatbot",
        "description": "AI customer support chatbot for ecommerce",
        "keywords": ["chatbot", "ai chatbot", "customer support", "support automation", "customer service"],
        "problem_solved": "High support volume, 24/7 availability, repetitive queries",
    },
    "comai_customer_support": {
        "business_unit": BusinessUnit.COMAI,
        "name": "COMAI Customer Support Automation",
        "description": "End-to-end customer support automation",
        "keywords": ["customer support", "support automation", "ticket automation"],
        "problem_solved": "High support costs, slow response times",
    },
    "comai_shopify": {
        "business_unit": BusinessUnit.COMAI,
        "name": "COMAI Shopify AI",
        "description": "AI automation for Shopify stores",
        "keywords": ["shopify", "shopify automation", "shopify ai", "shopify bot"],
        "problem_solved": "Manual Shopify operations, cart abandonment, low conversion",
    },
    "comai_automation": {
        "business_unit": BusinessUnit.COMAI,
        "name": "COMAI Ecommerce Automation",
        "description": "AI automation for ecommerce operations",
        "keywords": ["ecommerce automation", "automate ecommerce", "ecommerce ai"],
        "problem_solved": "Manual ecommerce processes, inefficient operations",
    },
    "comai_product_recs": {
        "business_unit": BusinessUnit.COMAI,
        "name": "COMAI Product Recommendations",
        "description": "AI-powered product recommendations",
        "keywords": ["product recommendations", "personalization", "product suggestions"],
        "problem_solved": "Low average order value, poor personalization",
    },
    "comai_cart_recovery": {
        "business_unit": BusinessUnit.COMAI,
        "name": "COMAI Cart Recovery",
        "description": "AI-powered abandoned cart recovery",
        "keywords": ["cart abandonment", "abandoned cart", "cart recovery", "checkout optimization"],
        "problem_solved": "High cart abandonment rate",
    },
    "comai_lead_capture": {
        "business_unit": BusinessUnit.COMAI,
        "name": "COMAI Lead Capture",
        "description": "AI-powered lead capture automation",
        "keywords": ["lead capture", "lead generation", "lead automation"],
        "problem_solved": "Poor lead capture, lost prospects",
    },
    "comai_follow_up": {
        "business_unit": BusinessUnit.COMAI,
        "name": "COMAI Follow-Up Automation",
        "description": "Automated customer follow-up sequences",
        "keywords": ["follow-up", "follow up automation", "customer follow-up", "sales follow-up"],
        "problem_solved": "Missed follow-ups, lost deals",
    },

    # --- SAAS DEVELOPMENT ---
    "saas_mvp": {
        "business_unit": BusinessUnit.SAAS_DEVELOPMENT,
        "name": "SaaS MVP Development",
        "description": "Build and launch SaaS MVP from scratch",
        "keywords": ["mvp", "mvp development", "minimum viable product", "build mvp", "saas mvp"],
        "problem_solved": "Need to validate SaaS idea quickly",
    },
    "saas_product": {
        "business_unit": BusinessUnit.SAAS_DEVELOPMENT,
        "name": "SaaS Product Development",
        "description": "Full SaaS product development",
        "keywords": ["saas product", "saas development", "saas platform", "build saas", "saas app"],
        "problem_solved": "Need to build or scale SaaS product",
    },
    "saas_dev_team": {
        "business_unit": BusinessUnit.SAAS_DEVELOPMENT,
        "name": "SaaS Development Team",
        "description": "Dedicated SaaS development team",
        "keywords": ["developers", "development team", "tech team", "engineering team", "hire developers"],
        "problem_solved": "Need technical team, can't hire fast enough",
    },
    "saas_backend": {
        "business_unit": BusinessUnit.SAAS_DEVELOPMENT,
        "name": "SaaS Backend Development",
        "description": "Backend infrastructure for SaaS",
        "keywords": ["backend", "api", "infrastructure", "architecture", "backend development"],
        "problem_solved": "Need robust backend architecture",
    },
    "saas_api": {
        "business_unit": BusinessUnit.SAAS_DEVELOPMENT,
        "name": "API Development",
        "description": "API design and development",
        "keywords": ["api", "api development", "api integration", "rest api"],
        "problem_solved": "Need API for product or integration",
    },
    "saas_cloud": {
        "business_unit": BusinessUnit.SAAS_DEVELOPMENT,
        "name": "Cloud Architecture",
        "description": "Cloud infrastructure and architecture",
        "keywords": ["cloud", "aws", "azure", "cloud architecture", "cloud migration", "devops"],
        "problem_solved": "Need cloud infrastructure or migration",
    },
    "saas_cto": {
        "business_unit": BusinessUnit.SAAS_DEVELOPMENT,
        "name": "CTO as a Service",
        "description": "Technical leadership for SaaS startups",
        "keywords": ["cto", "technical cofounder", "technical leadership", "technical advisor"],
        "problem_solved": "Need technical leadership without full-time CTO",
    },
    "saas_mobile_app": {
        "business_unit": BusinessUnit.SAAS_DEVELOPMENT,
        "name": "Mobile App Development",
        "description": "Native and cross-platform mobile apps",
        "keywords": ["mobile app", "android", "ios", "flutter", "react native", "mobile development"],
        "problem_solved": "Need mobile app for SaaS product",
    },
    "saas_scaling": {
        "business_unit": BusinessUnit.SAAS_DEVELOPMENT,
        "name": "SaaS Scaling",
        "description": "Scaling SaaS products and teams",
        "keywords": ["scaling", "scale", "growth", "performance", "optimization"],
        "problem_solved": "SaaS product needs to scale",
    },
    "saas_dedicated": {
        "business_unit": BusinessUnit.SAAS_DEVELOPMENT,
        "name": "Dedicated Development Team",
        "description": "Outsourced dedicated development team",
        "keywords": ["dedicated team", "outsourced team", "outsource", "dedicated developers"],
        "problem_solved": "Need dedicated team without hiring overhead",
    },

    # --- CUSTOM SOFTWARE ---
    "custom_software": {
        "business_unit": BusinessUnit.CUSTOM_SOFTWARE,
        "name": "Custom Software Development",
        "description": "Custom software solutions for specific business needs",
        "keywords": ["custom software", "software development", "custom application", "build software"],
        "problem_solved": "Need software tailored to specific business process",
    },
    "custom_erp": {
        "business_unit": BusinessUnit.CUSTOM_SOFTWARE,
        "name": "ERP Development",
        "description": "Enterprise Resource Planning systems",
        "keywords": ["erp", "erp system", "erp implementation", "enterprise resource planning"],
        "problem_solved": "Need integrated business operations system",
    },
    "custom_crm": {
        "business_unit": BusinessUnit.CUSTOM_SOFTWARE,
        "name": "CRM Development",
        "description": "Customer Relationship Management systems",
        "keywords": ["crm", "crm system", "crm implementation", "customer relationship"],
        "problem_solved": "Need customer management system",
    },
    "custom_ai_automation": {
        "business_unit": BusinessUnit.CUSTOM_SOFTWARE,
        "name": "AI Process Automation",
        "description": "AI-powered business process automation",
        "keywords": ["ai automation", "ai agents", "process automation", "workflow automation", "automate"],
        "problem_solved": "Manual processes that can be automated with AI",
    },
    "custom_modernization": {
        "business_unit": BusinessUnit.CUSTOM_SOFTWARE,
        "name": "Legacy Modernization",
        "description": "Modernizing legacy systems and applications",
        "keywords": ["legacy", "modernize", "legacy modernization", "digital transformation", "migration"],
        "problem_solved": "Outdated systems limiting growth",
    },
    "custom_dashboard": {
        "business_unit": BusinessUnit.CUSTOM_SOFTWARE,
        "name": "Dashboard & Reporting",
        "description": "Custom dashboards and reporting tools",
        "keywords": ["dashboard", "reporting", "analytics", "business intelligence", "data visualization"],
        "problem_solved": "Need data visibility and insights",
    },
    "custom_web_app": {
        "business_unit": BusinessUnit.CUSTOM_SOFTWARE,
        "name": "Web Application Development",
        "description": "Custom web applications and platforms",
        "keywords": ["web app", "web application", "web platform", "web development"],
        "problem_solved": "Need web-based application",
    },
    "custom_ai": {
        "business_unit": BusinessUnit.CUSTOM_SOFTWARE,
        "name": "AI Solutions",
        "description": "Custom AI and ML solutions",
        "keywords": ["ai", "artificial intelligence", "machine learning", "ai solution", "ai integration"],
        "problem_solved": "Need AI capability for business",
    },
    "custom_workflow": {
        "business_unit": BusinessUnit.CUSTOM_SOFTWARE,
        "name": "Workflow Automation",
        "description": "Custom workflow automation systems",
        "keywords": ["workflow", "workflow automation", "business automation", "automate workflow"],
        "problem_solved": "Manual workflows causing delays",
    },

    # --- CYBERSECURITY ---
    "cyber_web_vapt": {
        "business_unit": BusinessUnit.CYBERSECURITY,
        "name": "Web Application VAPT",
        "description": "Web application vulnerability assessment and penetration testing",
        "keywords": ["web application pentest", "web app vapt", "website pentest", "owasp", "web application penetration"],
        "problem_solved": "Need web application security testing",
    },
    "cyber_api_testing": {
        "business_unit": BusinessUnit.CYBERSECURITY,
        "name": "API Security Testing",
        "description": "API authentication, authorization, and injection testing",
        "keywords": ["api security", "api pentest", "api security testing"],
        "problem_solved": "Need API security testing",
    },
    "cyber_mobile_testing": {
        "business_unit": BusinessUnit.CYBERSECURITY,
        "name": "Mobile Application Security Testing",
        "description": "iOS and Android application security testing",
        "keywords": ["mobile app security", "mobile pentest", "ios security", "android security"],
        "problem_solved": "Need mobile application security testing",
    },
    "cyber_infra": {
        "business_unit": BusinessUnit.CYBERSECURITY,
        "name": "Infrastructure Security Assessment",
        "description": "Network and infrastructure security assessment",
        "keywords": ["infrastructure security", "network pentest", "internal network"],
        "problem_solved": "Need infrastructure security assessment",
    },
    "cyber_va": {
        "business_unit": BusinessUnit.CYBERSECURITY,
        "name": "Vulnerability Assessment",
        "description": "Prioritized vulnerability assessment",
        "keywords": ["vulnerability assessment", "va/pt", "va / pt"],
        "problem_solved": "Need a vulnerability assessment",
    },
    "cyber_pentest": {
        "business_unit": BusinessUnit.CYBERSECURITY,
        "name": "Penetration Testing",
        "description": "Scoped penetration testing with a commercial report",
        "keywords": ["penetration testing", "pentest", "pen test", "penetration test"],
        "problem_solved": "Need penetration testing",
    },
    "cyber_audit": {
        "business_unit": BusinessUnit.CYBERSECURITY,
        "name": "Security Audit",
        "description": "Independent security audit",
        "keywords": ["security audit", "security review"],
        "problem_solved": "Need a security audit",
    },
    "cyber_hardening": {
        "business_unit": BusinessUnit.CYBERSECURITY,
        "name": "Security Hardening",
        "description": "Hardening after verified findings",
        "keywords": ["security hardening", "harden our", "lock down"],
        "problem_solved": "Need help hardening after findings",
    },
    "cyber_remediation": {
        "business_unit": BusinessUnit.CYBERSECURITY,
        "name": "Vulnerability Remediation",
        "description": "Fix verified vulnerabilities",
        "keywords": ["fix a vulnerability", "vulnerability remediation", "security bug"],
        "problem_solved": "Need help remediating a verified vulnerability",
    },
    "cyber_code_review": {
        "business_unit": BusinessUnit.CYBERSECURITY,
        "name": "Secure Code Review",
        "description": "Review code for exploitable defects",
        "keywords": ["secure code review", "security code review", "sast"],
        "problem_solved": "Need secure code review",
    },
    "cyber_cloud": {
        "business_unit": BusinessUnit.CYBERSECURITY,
        "name": "Cloud Security Assessment",
        "description": "AWS/Azure/GCP security assessment",
        "keywords": ["cloud security", "aws security", "azure security", "gcp security"],
        "problem_solved": "Need cloud security assessment",
    },
    "cyber_compliance": {
        "business_unit": BusinessUnit.CYBERSECURITY,
        "name": "Compliance Security Testing",
        "description": "SOC 2 / ISO 27001 / PCI / HIPAA / GDPR testing evidence",
        "keywords": ["soc 2", "iso 27001", "pci dss", "hipaa security", "gdpr security"],
        "problem_solved": "Need compliance-driven security testing",
    },
    "cyber_prelaunch": {
        "business_unit": BusinessUnit.CYBERSECURITY,
        "name": "Pre-launch Security Assessment",
        "description": "Security validation before go-live",
        "keywords": ["before launch", "pre-launch security", "before production", "before going live"],
        "problem_solved": "Need security testing before launch",
    },
    "cyber_continuous": {
        "business_unit": BusinessUnit.CYBERSECURITY,
        "name": "Continuous Security Testing",
        "description": "Retainer / ongoing security testing",
        "keywords": ["continuous security", "ongoing pentest", "security retainer"],
        "problem_solved": "Need continuous / retainer security testing",
    },
}


def match_services(
    text: str,
    business_unit: str | None = None,
    top_n: int = 3,
) -> list[ServiceMatch]:
    """Match text content to Inowix services.

    Args:
        text: Lowercased text to match against.
        business_unit: Optional filter by BU.
        top_n: Maximum number of service matches to return.

    Returns:
        List of ServiceMatch sorted by confidence descending.
    """
    text_lower = text.lower()
    matches: list[ServiceMatch] = []

    for service_id, service_info in SERVICE_CATALOG.items():
        if business_unit and service_info["business_unit"].value != business_unit:
            continue

        matched_keywords = [
            kw for kw in service_info["keywords"] if kw in text_lower
        ]
        if not matched_keywords:
            continue

        confidence = min(len(matched_keywords) * 0.2 + 0.3, 1.0)

        match = ServiceMatch(
            business_unit=service_info["business_unit"],
            service_name=service_info["name"],
            service_description=service_info["description"],
            match_confidence=round(confidence, 2),
            match_reasons=[
                service_info["problem_solved"],
                f"Matched: {', '.join(matched_keywords[:3])}",
            ],
        )
        matches.append(match)

    matches.sort(key=lambda m: m.match_confidence, reverse=True)
    return matches[:top_n]
