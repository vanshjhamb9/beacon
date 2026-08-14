"""Account Builder - Orchestrates full account creation from ecommerce lead.

Integrates web scraping, technology detection, pain point analysis,
COMAI opportunity scoring, sales intelligence, and call preparation.
"""

from __future__ import annotations

import logging

from packages.sales_intelligence_platform.models import Account
from packages.sales_intelligence_platform.engines.decision_maker_engine import (
    extract_decision_makers,
)
from packages.sales_intelligence_platform.engines.contact_discovery import (
    discover_contact_channels,
)
from packages.sales_intelligence_platform.engines.buying_committee import (
    build_buying_committee,
)
from packages.sales_intelligence_platform.engines.account_health import (
    calculate_account_health,
)
from packages.sales_intelligence_platform.engines.account_score import (
    calculate_account_score,
)
from packages.sales_intelligence_platform.engines.evidence_engine import (
    compile_evidence,
)
from packages.sales_intelligence_platform.engines.confidence_engine import (
    calculate_confidence,
)
from packages.sales_intelligence_platform.engines.web_scraper import WebScraper
from packages.sales_intelligence_platform.engines.technology_detector import TechnologyDetector
from packages.sales_intelligence_platform.engines.pain_point_detector import PainPointDetector
from packages.sales_intelligence_platform.engines.comai_opportunity_score import COMAIOpportunityScorer
from packages.sales_intelligence_platform.engines.sales_intel_summary import SalesIntelligenceGenerator
from packages.sales_intelligence_platform.engines.call_preparation import CallPreparationGenerator

logger = logging.getLogger(__name__)

# Shared engine instances
_scraper = WebScraper()
_tech_detector = TechnologyDetector()
_pain_detector = PainPointDetector()
_opportunity_scorer = COMAIOpportunityScorer()
_summary_generator = SalesIntelligenceGenerator()
_call_prep_generator = CallPreparationGenerator()


def build_account(lead_data: dict, *, scrape_website: bool = True) -> Account:
    """Build a complete sales account from ecommerce lead data.

    This is the main orchestrator. It:
    1. Scrapes website for real data (if scrape_website=True)
    2. Detects technology stack
    3. Extracts decision makers
    4. Discovers contact channels
    5. Detects pain points
    6. Scores COMAI opportunity
    7. Generates sales intelligence summary
    8. Generates call preparation materials
    9. Builds buying committee
    10. Compiles evidence
    11. Calculates confidence, health, score
    12. Determines status
    """
    account = _create_base_account(lead_data)

    # Step 1: Scrape website for real data
    website_data = {}
    if scrape_website and account.website:
        try:
            website_data = _scraper.scrape(account.website)
            account.website_data = website_data
            logger.info(f"Scraped {account.website}: {website_data.get('title', 'no title')}")
        except Exception as e:
            logger.error(f"Failed to scrape {account.website}: {e}")

    # Merge scraped data into lead_data for downstream engines
    merged_data = {**lead_data, **website_data}

    # Step 2: Detect technology stack
    tech_profile = _tech_detector.detect(
        platform=merged_data.get("platform", ""),
        support_tools=merged_data.get("support_tools", []),
        analytics_tools=merged_data.get("analytics_tools", []),
        chatbot_tool=merged_data.get("chatbot_tool", ""),
        has_whatsapp_widget=merged_data.get("has_whatsapp_widget", False),
        has_live_chat=merged_data.get("has_live_chat", False),
        has_crm=merged_data.get("has_crm", False),
        crm_tool=merged_data.get("crm_tool", ""),
    )
    account.technology_profile = tech_profile

    # Update account with detected tech
    account.platform = tech_profile.platform or account.platform
    account.chatbot_detected = bool(tech_profile.chatbot_tool)
    account.whatsapp_detected = tech_profile.has_whatsapp_widget
    account.crm_detected = tech_profile.has_crm

    # Step 3: Extract decision makers
    account.decision_makers = extract_decision_makers(merged_data)

    # Step 4: Discover contact channels
    account.contact_channels = discover_contact_channels(merged_data, account.decision_makers)

    # Step 5: Detect pain points
    pain_analysis = _pain_detector.analyze(
        has_chatbot=tech_profile.chatbot_tool != "",
        chatbot_tool=tech_profile.chatbot_tool,
        has_whatsapp_widget=tech_profile.has_whatsapp_widget,
        has_live_chat=tech_profile.has_live_chat,
        has_crm=tech_profile.has_crm,
        support_tools=tech_profile.support_tools,
        platform=account.platform,
        product_count=merged_data.get("product_count", 0),
        has_ecommerce=merged_data.get("has_ecommerce", True),
        category=account.category,
        instagram_url=merged_data.get("instagram_url", ""),
        facebook_url=merged_data.get("facebook_url", ""),
        phone=merged_data.get("phone", ""),
        email=merged_data.get("email", ""),
        description=merged_data.get("description", ""),
    )
    account.pain_analysis = pain_analysis

    # Step 6: Score COMAI opportunity
    opportunity_score = _opportunity_scorer.score(
        platform=account.platform,
        has_chatbot=tech_profile.chatbot_tool != "",
        chatbot_tool=tech_profile.chatbot_tool,
        has_whatsapp_widget=tech_profile.has_whatsapp_widget,
        has_live_chat=tech_profile.has_live_chat,
        product_count=merged_data.get("product_count", 0),
        has_ecommerce=merged_data.get("has_ecommerce", True),
        category=account.category,
        instagram_followers=merged_data.get("instagram_followers", 0),
        facebook_likes=merged_data.get("facebook_likes", 0),
        instagram_url=merged_data.get("instagram_url", ""),
        facebook_url=merged_data.get("facebook_url", ""),
        description=merged_data.get("description", ""),
        founded_year=merged_data.get("founded_year", 0),
        city=account.city,
    )
    account.opportunity_score = opportunity_score

    # Step 7: Generate sales intelligence summary
    sales_summary = _summary_generator.generate(
        company_name=account.company_name,
        category=account.category,
        platform=account.platform,
        pain_points=[{"category": p.category, "description": p.description, "severity": p.severity} for p in pain_analysis.pain_points],
        has_chatbot=tech_profile.chatbot_tool != "",
        chatbot_tool=tech_profile.chatbot_tool,
        has_whatsapp=tech_profile.has_whatsapp_widget,
        has_live_chat=tech_profile.has_live_chat,
        product_count=merged_data.get("product_count", 0),
        city=account.city,
        decision_maker_name=account.decision_makers[0].name if account.decision_makers else "",
        decision_maker_role=account.decision_makers[0].normalized_role if account.decision_makers else "",
    )
    account.sales_summary = sales_summary

    # Step 8: Generate call preparation materials
    call_prep = _call_prep_generator.generate(
        company_name=account.company_name,
        category=account.category,
        platform=account.platform,
        pain_points=[{"category": p.category, "description": p.description, "severity": p.severity} for p in pain_analysis.pain_points],
        has_chatbot=tech_profile.chatbot_tool != "",
        chatbot_tool=tech_profile.chatbot_tool,
        product_count=merged_data.get("product_count", 0),
        decision_maker_name=account.decision_makers[0].name if account.decision_makers else "",
        decision_maker_role=account.decision_makers[0].normalized_role if account.decision_makers else "",
        city=account.city,
        instagram_followers=merged_data.get("instagram_followers", 0),
        whatsapp_link=merged_data.get("whatsapp_link", ""),
        has_ecommerce=merged_data.get("has_ecommerce", True),
    )
    account.call_preparation = call_prep

    # Step 9: Build buying committee
    account.buying_committee = build_buying_committee(merged_data, account.decision_makers)

    # Step 10: Compile evidence
    account.evidence_records = compile_evidence(account)

    # Step 11: Calculate confidence, health, score
    confidence = calculate_confidence(account)
    account.health = calculate_account_health(account)
    account.score = calculate_account_score(account)

    # Step 12: Set primary contacts
    _set_primary_contacts(account)

    # Step 13: Determine status
    account.status = _determine_status(account)

    return account


def _create_base_account(lead_data: dict) -> Account:
    """Create base account from lead data."""
    return Account(
        ecommerce_lead_id=str(lead_data.get("id", "")),
        company_name=lead_data.get("company_name", ""),
        website=lead_data.get("website", ""),
        domain=lead_data.get("domain", ""),
        platform=lead_data.get("platform", ""),
        category=lead_data.get("category", ""),
        country=lead_data.get("country", "India"),
        city=lead_data.get("city", ""),
        state=lead_data.get("state", ""),
        shopify_detected=lead_data.get("shopify_detected", False),
        woocommerce_detected=lead_data.get("woocommerce_detected", False),
        chatbot_detected=lead_data.get("chatbot_detected", False),
        whatsapp_detected=lead_data.get("whatsapp_detected", False),
        crm_detected=lead_data.get("crm_detected", False),
        pain_score=lead_data.get("comai_score", 0.0),
        growth_score=lead_data.get("comai_score", 0.0) * 0.3,
    )


def _set_primary_contacts(account: Account) -> None:
    """Set primary decision maker and contact info."""
    if account.decision_makers:
        primary = max(account.decision_makers, key=lambda dm: dm.confidence)
        account.primary_decision_maker = primary.name

    for ch in account.contact_channels:
        if ch.kind in ("founder_email", "executive_email") and not account.primary_email:
            account.primary_email = ch.value
        elif ch.kind in ("business_phone", "founder_phone") and not account.primary_phone:
            account.primary_phone = ch.value
        elif ch.kind == "linkedin_company" and not account.primary_linkedin:
            account.primary_linkedin = ch.value


def _determine_status(account: Account) -> str:
    """Determine account status based on completeness."""
    has_dm = len(account.decision_makers) > 0
    has_email = bool(account.primary_email)
    has_phone = bool(account.primary_phone)
    has_linkedin = bool(account.primary_linkedin)
    has_opportunity = hasattr(account, 'opportunity_score') and account.opportunity_score and account.opportunity_score.total_score >= 70

    if has_dm and (has_email or has_phone) and has_linkedin and has_opportunity:
        return "SALES_READY"
    elif has_dm and (has_email or has_phone):
        return "NEEDS_ENRICHMENT"
    elif has_dm:
        return "NEEDS_ENRICHMENT"
    else:
        return "MANUAL_REVIEW"
