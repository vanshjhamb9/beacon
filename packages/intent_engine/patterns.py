"""Intent detection patterns and classification rules.

Each pattern maps to:
- A business unit it matches
- An intent level
- A base intent score
- Service(s) it implies
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IntentPattern:
    """A pattern that detects buying intent."""
    keywords: list[str]
    business_unit: str  # COMAI, SAAS_DEVELOPMENT, CUSTOM_SOFTWARE
    services: list[str]
    intent_level: str  # ACTIVE_REQUIREMENT, EVALUATION, EARLY_INTENT
    base_score: float  # 0-100
    description: str


# ============================================================
# ACTIVE REQUIREMENT PATTERNS (score 80-100)
# ============================================================
# These are explicit statements of need. Highest priority.

ACTIVE_REQUIREMENT_PATTERNS: list[IntentPattern] = [
    # --- HIRING SIGNALS (highest priority — explicit need) ---
    IntentPattern(
        keywords=["hiring chatbot developer", "hiring ai chatbot", "hiring whatsapp developer",
                   "hiring whatsapp automation", "hiring conversational ai",
                   "chatbot developer", "ai chatbot developer", "conversational ai developer",
                   "hiring ai conversational"],
        business_unit="COMAI",
        services=["comai_chatbot", "comai_whatsapp"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=98,
        description="Hiring for chatbot/WhatsApp automation roles",
    ),
    IntentPattern(
        keywords=["hiring full stack", "hiring full-stack", "hiring backend developer",
                   "hiring frontend developer", "hiring react native", "hiring mobile developer",
                   "hiring software engineer", "full stack engineer", "full-stack engineer",
                   "hiring ai developer"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_dev_team", "saas_product"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=96,
        description="Hiring for software development roles",
    ),
    IntentPattern(
        keywords=["hiring ai developer", "hiring machine learning", "hiring data scientist",
                   "hiring python developer", "hiring devops"],
        business_unit="CUSTOM_SOFTWARE",
        services=["custom_ai", "custom_ai_automation"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=94,
        description="Hiring for AI/ML/data roles",
    ),
    IntentPattern(
        keywords=["hiring erp developer", "hiring crm developer", "hiring java developer",
                   "hiring .net developer", "hiring salesforce"],
        business_unit="CUSTOM_SOFTWARE",
        services=["custom_erp", "custom_crm"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=92,
        description="Hiring for ERP/CRM/enterprise roles",
    ),

    # --- COMAI ---
    IntentPattern(
        keywords=["looking for whatsapp automation", "need whatsapp bot", "whatsapp automation for ecommerce",
                   "automate whatsapp", "whatsapp customer support", "whatsapp sales bot"],
        business_unit="COMAI",
        services=["comai_whatsapp", "comai_chatbot"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=95,
        description="Explicit WhatsApp automation need",
    ),
    IntentPattern(
        keywords=["need chatbot", "looking for chatbot", "ai chatbot for ecommerce",
                   "customer support automation", "automate customer support",
                   "need ecommerce chatbot", "chatbot for shopify"],
        business_unit="COMAI",
        services=["comai_chatbot", "comai_customer_support"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=95,
        description="Explicit chatbot/customer support automation need",
    ),
    IntentPattern(
        keywords=["need shopify automation", "shopify ai", "automate shopify",
                   "shopify chatbot", "shopify whatsapp", "woocommerce automation"],
        business_unit="COMAI",
        services=["comai_shopify", "comai_chatbot", "comai_whatsapp"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=92,
        description="Explicit Shopify/WooCommerce automation need",
    ),
    IntentPattern(
        keywords=["ecommerce automation", "automate ecommerce", "ecommerce ai",
                   "product recommendations ai", "abandoned cart recovery",
                   "lead capture automation"],
        business_unit="COMAI",
        services=["comai_automation", "comai_chatbot", "comai_whatsapp"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=90,
        description="Explicit ecommerce automation need",
    ),
    IntentPattern(
        keywords=["customer follow-up automation", "automate follow-ups",
                   "sales follow-up bot", "lead nurturing automation"],
        business_unit="COMAI",
        services=["comai_follow_up", "comai_automation"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=88,
        description="Explicit follow-up automation need",
    ),

    # --- SAAS DEVELOPMENT ---
    IntentPattern(
        keywords=["looking for developers", "need developers", "need development team",
                   "looking for development team", "need technical team",
                   "hire developers", "hire development team"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_dev_team", "saas_mvp", "saas_product"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=98,
        description="Explicit developer/team hiring need",
    ),
    IntentPattern(
        keywords=["need saas mvp", "build saas mvp", "saas mvp development",
                   "need mvp built", "mvp for saas", "minimum viable product",
                   "need to build mvp"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_mvp", "saas_product"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=96,
        description="Explicit SaaS MVP build need",
    ),
    IntentPattern(
        keywords=["need saas product", "build saas product", "saas product development",
                   "need product built", "building a saas", "saas platform",
                   "need saas platform"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_product", "saas_scaling"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=94,
        description="Explicit SaaS product development need",
    ),
    IntentPattern(
        keywords=["need technical cofounder", "looking for technical cofounder",
                   "cto as a service", "need cto", "technical leadership"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_cto", "saas_dev_team"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=92,
        description="Explicit technical leadership need",
    ),
    IntentPattern(
        keywords=["need android developer", "need ios developer", "need mobile app",
                   "build mobile app", "mobile app development", "need app developed"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_mobile_app", "saas_product"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=90,
        description="Explicit mobile app development need",
    ),
    IntentPattern(
        keywords=["need api development", "need backend", "backend development",
                   "api integration", "need cloud architecture", "cloud migration"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_backend", "saas_api", "saas_cloud"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=88,
        description="Explicit backend/API/cloud need",
    ),
    IntentPattern(
        keywords=["looking for software agency", "looking for development company",
                   "need software agency", "need development partner",
                   "looking for tech partner"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_dev_team", "saas_product", "saas_mvp"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=88,
        description="Explicit agency/company search",
    ),
    IntentPattern(
        keywords=["need dedicated developers", "dedicated development team",
                   "outsource development", "need outsourced team"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_dev_team", "saas_dedicated"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=86,
        description="Explicit dedicated team need",
    ),

    # --- CUSTOM SOFTWARE ---
    IntentPattern(
        keywords=["need custom software", "custom software development",
                   "need software to automate", "build custom software",
                   "need internal software", "business software"],
        business_unit="CUSTOM_SOFTWARE",
        services=["custom_software", "custom_automation"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=94,
        description="Explicit custom software need",
    ),
    IntentPattern(
        keywords=["need erp", "need crm", "erp implementation", "crm implementation",
                   "need erp system", "need crm system", "erp for business"],
        business_unit="CUSTOM_SOFTWARE",
        services=["custom_erp", "custom_crm"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=92,
        description="Explicit ERP/CRM need",
    ),
    IntentPattern(
        keywords=["need ai automation", "ai agents", "automate operations",
                   "business process automation", "workflow automation",
                   "need automation", "automate manual processes"],
        business_unit="CUSTOM_SOFTWARE",
        services=["custom_ai_automation", "custom_workflow"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=90,
        description="Explicit AI/automation need",
    ),
    IntentPattern(
        keywords=["legacy modernization", "modernize legacy", "legacy system migration",
                   "need to modernize", "digital transformation"],
        business_unit="CUSTOM_SOFTWARE",
        services=["custom_modernization", "custom_software"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=88,
        description="Explicit legacy modernization need",
    ),
    IntentPattern(
        keywords=["need dashboard", "build dashboard", "analytics dashboard",
                   "business intelligence", "need reporting tool"],
        business_unit="CUSTOM_SOFTWARE",
        services=["custom_dashboard", "custom_software"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=85,
        description="Explicit dashboard/reporting need",
    ),
    IntentPattern(
        keywords=["need web application", "build web app", "web app development",
                   "need web platform", "build web platform"],
        business_unit="CUSTOM_SOFTWARE",
        services=["custom_web_app", "custom_software"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=88,
        description="Explicit web application need",
    ),
    IntentPattern(
        keywords=["need ai solution", "ai for business", "machine learning for",
                   "ai integration", "need ai agent", "need ai chatbot"],
        business_unit="CUSTOM_SOFTWARE",
        services=["custom_ai", "custom_ai_automation"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=90,
        description="Explicit AI solution need",
    ),

    # --- CTO DIRECTIVE: DIRECT REQUIREMENT PATTERNS (score 90-100) ---
    # These patterns are for people who have explicitly stated they need technical services.
    IntentPattern(
        keywords=["looking for developer", "need developer", "need developers",
                   "looking for developers", "seeking developer", "searching for developer"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_dev_team", "saas_mvp", "saas_product"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=98,
        description="Explicitly looking for developer(s)",
    ),
    IntentPattern(
        keywords=["looking for development team", "need development team",
                   "seeking development team", "looking for tech team"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_dev_team", "saas_mvp"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=98,
        description="Explicitly looking for development team",
    ),
    IntentPattern(
        keywords=["need technical cofounder", "looking for technical cofounder",
                   "seeking technical cofounder", "need CTO", "looking for CTO"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_cto", "saas_mvp"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=97,
        description="Looking for technical leadership",
    ),
    IntentPattern(
        keywords=["need MVP developer", "build my MVP", "building MVP",
                   "need MVP built", "looking for MVP developer"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_mvp"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=96,
        description="Explicitly needs MVP development",
    ),
    IntentPattern(
        keywords=["looking for software agency", "need agency",
                   "looking for development company", "need development company"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_dev_team", "saas_mvp"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=95,
        description="Looking for agency/services company",
    ),
    IntentPattern(
        keywords=["looking for app developer", "need app developer",
                   "need mobile app developer", "looking for mobile developer"],
        business_unit="CUSTOM_SOFTWARE",
        services=["custom_web_app", "custom_software"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=95,
        description="Looking for mobile app developer",
    ),
    IntentPattern(
        keywords=["need SaaS developer", "looking for SaaS developer",
                   "need SaaS developer", "looking for SaaS developer"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_mvp", "saas_product"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=95,
        description="Looking for SaaS developer",
    ),
    IntentPattern(
        keywords=["need AI developer", "looking for AI developer",
                   "need machine learning developer", "looking for ML developer"],
        business_unit="CUSTOM_SOFTWARE",
        services=["custom_ai", "custom_ai_automation"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=94,
        description="Looking for AI developer",
    ),
    IntentPattern(
        keywords=["need automation", "looking for automation",
                   "need business automation", "looking for automation solution"],
        business_unit="CUSTOM_SOFTWARE",
        services=["custom_ai_automation", "custom_workflow"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=93,
        description="Needs automation solution",
    ),
    IntentPattern(
        keywords=["technical team needed", "need technical team",
                   "looking for technical team", "seeking technical team"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_dev_team", "saas_product"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=93,
        description="Needs technical team",
    ),
    IntentPattern(
        keywords=["development partner", "looking for partner",
                   "need development partner", "seeking tech partner"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_dev_team", "saas_cto"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=92,
        description="Looking for development partner",
    ),
    IntentPattern(
        keywords=["need help building", "help me build",
                   "need someone to build", "looking for someone to build"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_mvp", "saas_product"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=92,
        description="Needs help building something",
    ),
    IntentPattern(
        keywords=["RFP", "request for proposal", "project requirement",
                   "looking for proposals", "need proposal"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_mvp", "custom_software", "saas_product"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=90,
        description="Has posted RFP/project requirement",
    ),
    IntentPattern(
        keywords=["product specification", "have specification",
                   "have product spec", "ready to build"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_mvp", "saas_product"],
        intent_level="ACTIVE_REQUIREMENT",
        base_score=90,
        description="Has product spec, needs implementation",
    ),
]


# ============================================================
# EVALUATION PATTERNS (score 50-79)
# ============================================================
# Company is actively evaluating or comparing solutions.

EVALUATION_PATTERNS: list[IntentPattern] = [
    IntentPattern(
        keywords=["comparing", "evaluating", "reviewing", "shortlisting",
                   "which platform", "best tool for", "alternative to"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_product", "saas_mvp"],
        intent_level="EVALUATION",
        base_score=70,
        description="Active evaluation signal",
    ),
    IntentPattern(
        keywords=["pricing", "how much does", "cost of development",
                   "budget for", "investment in"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_mvp", "saas_product"],
        intent_level="EVALUATION",
        base_score=65,
        description="Budget/pricing evaluation signal",
    ),
    IntentPattern(
        keywords=["request for proposal", "rfp", "rfq", "quotation",
                   "request for quote", "proposal needed"],
        business_unit="CUSTOM_SOFTWARE",
        services=["custom_software", "custom_automation"],
        intent_level="EVALUATION",
        base_score=75,
        description="Formal procurement signal",
    ),
]


# ============================================================
# EARLY INTENT PATTERNS (score 30-49)
# ============================================================
# Company shows problem awareness but isn't solution seeking yet.

EARLY_INTENT_PATTERNS: list[IntentPattern] = [
    IntentPattern(
        keywords=["struggling with", "problem with", "challenge with",
                   "issue with", "difficulty with", "pain point"],
        business_unit="COMAI",
        services=["comai_chatbot", "comai_automation"],
        intent_level="EARLY_INTENT",
        base_score=45,
        description="Problem awareness signal",
    ),
    IntentPattern(
        keywords=["scaling challenge", "growing pain", "bottleneck",
                   "manual process", "inefficient", "time-consuming"],
        business_unit="CUSTOM_SOFTWARE",
        services=["custom_automation", "custom_software"],
        intent_level="EARLY_INTENT",
        base_score=42,
        description="Operational challenge signal",
    ),
    IntentPattern(
        keywords=["hiring engineer", "hiring developer", "hiring cto",
                   "hiring tech", "hiring product"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_dev_team", "saas_cto"],
        intent_level="EARLY_INTENT",
        base_score=40,
        description="Technical hiring signal (may need outsourced team instead)",
    ),
]


# ============================================================
# COMPANY OPPORTUNITY PATTERNS (score 10-29)
# ============================================================
# Generic signals that match ICP but show no explicit intent.

COMPANY_OPPORTUNITY_PATTERNS: list[IntentPattern] = [
    IntentPattern(
        keywords=["funded", "raised", "series a", "series b", "seed round"],
        business_unit="COMAI",
        services=["comai_chatbot", "comai_automation"],
        intent_level="COMPANY_OPPORTUNITY",
        base_score=25,
        description="Funding signal (discovery, not intent)",
    ),
    IntentPattern(
        keywords=["d2c brand", "ecommerce brand", "shopify store", "online store"],
        business_unit="COMAI",
        services=["comai_chatbot", "comai_whatsapp"],
        intent_level="COMPANY_OPPORTUNITY",
        base_score=20,
        description="Ecommerce presence (discovery, not intent)",
    ),
    IntentPattern(
        keywords=["startup", "founded", "launching", "new brand"],
        business_unit="SAAS_DEVELOPMENT",
        services=["saas_mvp", "saas_product"],
        intent_level="COMPANY_OPPORTUNITY",
        base_score=18,
        description="Startup signal (discovery, not intent)",
    ),
]
