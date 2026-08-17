"""COMAI B2B Partner Discovery Engine - Core Service.

This module implements the core partner discovery engine for finding agencies,
consultants, creators, and service providers that can become COMAI partners/resellers.

SEPARATE from:
- COMAI direct ecommerce leads
- INOWIX software-development leads
- Cybersecurity leads

COMAI B2B IS NOT AN AGENCY DIRECTORY.
WE ARE BUILDING A PARTNER ACQUISITION ENGINE.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

from app.models.partner import (
    AgencyType,
    ContactabilityLevel,
    ContactabilityResult,
    DiscoveryResult,
    EmailStatus,
    Evidence,
    ExportData,
    FinalVerdict,
    PartnerIntent,
    PartnerPotential,
    PartnerRecord,
    PartnerTier,
    ScoringResult,
)

logger = logging.getLogger(__name__)


# ============================================================
# AGENCY TYPE DETECTION — COMAI B2B PARTNER TARGETS
# ============================================================
# FIND companies that already have BUSINESS CLIENTS and can introduce,
# recommend, resell or bundle COMAI with their existing services.
#
# TARGET:
# - MARKETING AGENCIES (digital, performance, social media, SEO, PPC, Meta Ads, D2C, growth)
# - CREATIVE AGENCIES (video, content, branding, influencer)
# - WEBSITE DEVELOPMENT AGENCIES (Shopify, WooCommerce, ecommerce, web design, UI/UX)
# - APP DEVELOPMENT AGENCIES (mobile, software, AI, automation)
# - ECOMMERCE CONSULTANTS (D2C, growth, marketing, Shopify)
#
# REJECT:
# - WhatsApp/chatbot/white-label SaaS providers (competitors)
# ============================================================

AGENCY_TYPE_KEYWORDS: dict[str, list[str]] = {
    # ──── MARKETING AGENCIES ────
    "marketing": [
        "marketing", "digital marketing", "performance marketing",
        "social media marketing", "seo", "ppc", "google ads", "meta ads",
        "facebook ads", "instagram ads", "growth marketing", "d2c marketing",
        "ecommerce marketing", "lead generation", "email marketing",
        "sms marketing", "advertising", "media buying", "paid media",
        "paid social", "content marketing", "influencer marketing",
        "meta marketing", "google marketing", "d2c agency", "ecommerce agency",
    ],
    # ──── CREATIVE AGENCIES ────
    "creative": [
        "creative", "design", "branding", "video production", "video marketing",
        "content production", "content creation", "creative agency",
        "ad creative", "visual design", "motion graphics", "animation",
        "social content", "influencer marketing", "ugc", "branding agency",
        "creative studio", "content studio", "social studio",
    ],
    # ──── WEBSITE DEVELOPMENT AGENCIES ────
    "technology": [
        "web development", "website development", "shopify development",
        "shopify expert", "shopify partner", "woocommerce development",
        "ecommerce development", "ecommerce website", "web design",
        "ui/ux", "frontend development", "full stack development",
        "software development", "app development", "mobile app",
        "automation", "crm implementation", "digital transformation",
    ],
    # ──── ECOMMERCE CONSULTANTS ────
    "consultant": [
        "consultant", "consulting", "advisory", "strategy",
        "ecommerce consultant", "d2c consultant", "growth consultant",
        "marketing consultant", "shopify consultant", "business consultant",
        "ecommerce consulting", "d2c consulting", "growth consulting",
    ],
}

# ============================================================
# HIGH-INTENT PARTNER SIGNALS
# ============================================================

HIGH_INTENT_PATTERNS: dict[str, list[str]] = {
    "looking_for_saas_partners": [
        r"looking\s+(?:for|to)\s+(?:saas|software)\s+partners?",
        r"seeking\s+(?:saas|software)\s+partners?",
        r"need\s+(?:saas|software)\s+partners?",
    ],
    "looking_for_technology_partners": [
        r"looking\s+(?:for|to)\s+(?:technology|tech)\s+partners?",
        r"seeking\s+(?:technology|tech)\s+partners?",
        r"need\s+(?:technology|tech)\s+partners?",
    ],
    "looking_for_tools_for_clients": [
        r"looking\s+(?:for|to)\s+(?:tools?|solutions?)\s+(?:for|to)\s+(?:our|their|the)\s+clients?",
        r"need\s+(?:tools?|solutions?)\s+(?:for|to)\s+(?:our|their|the)\s+clients?",
        r"seeking\s+(?:tools?|solutions?)\s+(?:for|to)\s+(?:our|their|the)\s+clients?",
    ],
    "looking_for_white_label_solutions": [
        r"looking\s+(?:for|to)\s+white[\s-]?label",
        r"seeking\s+white[\s-]?label",
        r"need\s+white[\s-]?label",
        r"white[\s-]?label\s+(?:opportunity|program|solution)",
    ],
    "looking_for_reseller_opportunities": [
        r"looking\s+(?:for|to)\s+(?:resell|reseller)",
        r"seeking\s+(?:resell|reseller)",
        r"need\s+(?:resell|reseller)",
        r"reseller\s+(?:opportunity|program)",
    ],
    "looking_for_referral_partners": [
        r"looking\s+(?:for|to)\s+referral\s+partners?",
        r"seeking\s+referral\s+partners?",
        r"referral\s+(?:opportunity|program|partnership)",
    ],
    "looking_for_ecommerce_tools_for_clients": [
        r"looking\s+(?:for|to)\s+ecommerce\s+tools?\s+(?:for|to)\s+(?:our|their|the)\s+clients?",
        r"need\s+ecommerce\s+tools?\s+(?:for|to)\s+(?:our|their|the)\s+clients?",
    ],
    "need_whatsapp_solution_for_clients": [
        r"need\s+whatsapp\s+(?:solution|tool|bot|automation)\s+(?:for|to)\s+(?:our|their|the)\s+clients?",
        r"looking\s+(?:for|to)\s+whatsapp\s+(?:solution|tool|bot|automation)\s+(?:for|to)\s+(?:our|their|the)\s+clients?",
    ],
    "need_chatbot_solution_for_clients": [
        r"need\s+chatbot\s+(?:solution|tool|bot|automation)\s+(?:for|to)\s+(?:our|their|the)\s+clients?",
        r"looking\s+(?:for|to)\s+chatbot\s+(?:solution|tool|bot|automation)\s+(?:for|to)\s+(?:our|their|the)\s+clients?",
    ],
    "looking_for_automation_tools_for_clients": [
        r"looking\s+(?:for|to)\s+automation\s+tools?\s+(?:for|to)\s+(?:our|their|the)\s+clients?",
        r"need\s+automation\s+tools?\s+(?:for|to)\s+(?:our|their|the)\s+clients?",
    ],
    "looking_for_additional_services_to_offer_clients": [
        r"looking\s+(?:for|to)\s+(?:add|offer|provide)\s+(?:additional|new|more)\s+services?\s+(?:to|for)\s+(?:our|their|the)\s+clients?",
        r"want\s+to\s+(?:add|offer|provide)\s+(?:additional|new|more)\s+services?",
    ],
    "looking_for_complementary_saas_products": [
        r"looking\s+(?:for|to)\s+complementary\s+saas\s+products?",
        r"seeking\s+complementary\s+saas\s+products?",
    ],
    "want_to_expand_service_offering": [
        r"want\s+to\s+expand\s+(?:our|their)\s+service\s+offering",
        r"looking\s+(?:for|to)\s+expand\s+(?:our|their)\s+service\s+offering",
    ],
    "looking_for_agencies_tools_to_partner_with": [
        r"looking\s+(?:for|to)\s+(?:agencies?|tools?)\s+to\s+partner\s+with",
        r"seeking\s+(?:agencies?|tools?)\s+to\s+partner\s+with",
    ],
    "looking_for_software_we_can_resell": [
        r"looking\s+(?:for|to)\s+software\s+(?:we|they)\s+can\s+resell",
        r"seeking\s+software\s+(?:we|they)\s+can\s+resell",
    ],
    "looking_for_solutions_we_can_offer_clients": [
        r"looking\s+(?:for|to)\s+solutions?\s+(?:we|they)\s+can\s+offer\s+(?:our|their|the)\s+clients?",
        r"seeking\s+solutions?\s+(?:we|they)\s+can\s+offer\s+(?:our|their|the)\s+clients?",
    ],
}

# ============================================================
# INDIRECT PARTNER SIGNALS
# ============================================================

INDIRECT_SIGNAL_PATTERNS: dict[str, list[str]] = {
    "publicly_showcase_10_plus_business_clients": [
        r"(?:our|we)\s+(?:have|work\s+with|serve|partner\s+with)\s+\d{2,}\+?\s+(?:clients?|brands?|businesses?|companies?)",
        r"\d{2,}\+?\s+(?:clients?|brands?|businesses?|companies?)\s+(?:and\s+growing|worldwide|globally)",
    ],
    "manage_shopify_stores": [
        r"(?:we\s+)?(?:manage|run|handle|build|create|develop)\s+shopify\s+stores?",
        r"shopify\s+(?:expert|partner|agency|development|design)",
    ],
    "manage_ecommerce_marketing_campaigns": [
        r"(?:we\s+)?(?:manage|run|handle)\s+ecommerce\s+(?:marketing|advertising|campaigns?)",
        r"ecommerce\s+(?:marketing|advertising)\s+(?:agency|company|services?)",
    ],
    "manage_whatsapp_marketing_for_clients": [
        r"(?:we\s+)?(?:manage|run|handle)\s+whatsapp\s+(?:marketing|campaigns?|automation)\s+(?:for|with)\s+(?:our|their|the)\s+clients?",
        r"whatsapp\s+(?:marketing|automation)\s+(?:for|with)\s+(?:ecommerce|d2c|brands?)",
    ],
    "build_ecommerce_websites": [
        r"(?:we\s+)?(?:build|create|develop|design)\s+ecommerce\s+websites?",
        r"ecommerce\s+(?:website|web)\s+(?:development|design|agency)",
    ],
    "run_meta_google_ads_for_d2c_brands": [
        r"(?:we\s+)?(?:run|manage|handle)\s+(?:meta|facebook|google)\s+(?:ads?|advertising)\s+(?:for|with)\s+(?:d2c|ecommerce|brands?)",
        r"(?:meta|facebook|google)\s+(?:ads?|advertising)\s+(?:for|with)\s+(?:d2c|ecommerce|brands?)",
    ],
    "provide_crm_automation_implementation": [
        r"(?:we\s+)?(?:provide|offer|deliver|implement)\s+crm\s+(?:automation|implementation|integration)",
        r"crm\s+(?:automation|implementation|integration)\s+(?:agency|company|services?)",
    ],
    "manage_customer_retention": [
        r"(?:we\s+)?(?:manage|handle|optimize|improve)\s+customer\s+retention",
        r"customer\s+retention\s+(?:agency|company|services?|strategy)",
    ],
    "offer_ecommerce_growth_services": [
        r"(?:we\s+)?(?:offer|provide|deliver)\s+ecommerce\s+growth\s+(?:services?|strategies?|solutions?)",
        r"ecommerce\s+growth\s+(?:agency|company|consultant)",
    ],
    "repeatedly_work_with_smb_d2c_brands": [
        r"(?:we\s+)?(?:work\s+with|serve|partner\s+with)\s+(?:smb|d2c|small\s+business|startup)\s+(?:brands?|clients?|businesses?)",
        r"(?:smb|d2c|small\s+business|startup)\s+(?:brands?|clients?|businesses?)\s+(?:are|is)\s+(?:our|the)\s+(?:focus|specialty|niche)",
    ],
    "already_resell_saas_technology_products": [
        r"(?:we\s+)?(?:resell|white[\s-]?label|partner)\s+(?:with|for)\s+(?:saas|software|technology)\s+(?:products?|tools?|solutions?)",
        r"(?:resell|white[\s-]?label|partner)\s+(?:program|arrangement|partnership)",
    ],
}

# ============================================================
# CLIENT EVIDENCE PATTERNS
# ============================================================

CLIENT_EVIDENCE_PATTERNS: dict[str, list[str]] = {
    "multiple_business_clients": [
        r"(?:our|we)\s+(?:have|work\s+with|serve|partner\s+with|manage)\s+(?:\d+\+?\s+)?(?:clients?|brands?|businesses?|companies?)",
        r"\d+\+?\s+(?:clients?|brands?|businesses?|companies?)\s+(?:and\s+growing|worldwide|globally)",
        r"(?:trusted\s+by|working\s+with)\s+\d+\+?\s+(?:clients?|brands?|businesses?)",
    ],
    "ecommerce_d2c_clients": [
        r"(?:our|we)\s+(?:clients?|customers?|brands?)\s+(?:are|include|are\s+mainly)\s+(?:ecommerce|d2c|shopify|online\s+stores?)",
        r"(?:we\s+)?(?:work\s+with|serve|partner\s+with)\s+(?:ecommerce|d2c|shopify|online\s+store)\s+(?:brands?|clients?|businesses?)",
    ],
    "shopify_woocommerce_clients": [
        r"(?:our|we)\s+(?:clients?|customers?|brands?)\s+(?:are|include)\s+(?:shopify|woocommerce)\s+(?:stores?|brands?|businesses?)",
        r"(?:we\s+)?(?:work\s+with|serve|partner\s+with)\s+(?:shopify|woocommerce)\s+(?:stores?|brands?|businesses?)",
    ],
    "smb_startup_clients": [
        r"(?:our|we)\s+(?:clients?|customers?|brands?)\s+(?:are|include)\s+(?:smb|startup|small\s+business|growing)\s+(?:businesses?|companies?)",
        r"(?:we\s+)?(?:work\s+with|serve|partner\s+with)\s+(?:smb|startup|small\s+business|growing)\s+(?:businesses?|companies?)",
    ],
    "brands_they_manage": [
        r"(?:we\s+)?(?:manage|handle|work\s+with|serve)\s+(?:brands?|clients?|businesses?)\s+(?:like|such\s+as|including)\s+",
        r"(?:our|we)\s+(?:portfolio|client\s+list|brands?)\s+(?:includes?|features?|showcases?)",
    ],
    "recurring_client_relationships": [
        r"(?:long[\s-]?term|recurring|ongoing|retainer)\s+(?:clients?|relationships?|partnerships?)",
        r"(?:we\s+)?(?:have|maintain)\s+(?:long[\s-]?term|recurring|ongoing)\s+(?:clients?|relationships?)",
    ],
}

# ============================================================
# REJECT PATTERNS
# ============================================================

REJECT_PATTERNS: list[str] = [
    r"(?:we\s+)?(?:are|'?re)\s+a\s+(?:freelancer|individual|solo)",
    r"(?:looking\s+for|seeking)\s+(?:job|position|role|opportunity|work)",
    r"(?:we\s+)?(?:sell|selling|selling\s+products?)\s+(?:directly|on\s+amazon|on\s+flipkart)",
    r"(?:we\s+)?(?:are|'?re)\s+a\s+(?:competitor|competing)",
    r"(?:amazon|flipkart|myntra|meesho)\s+(?:seller|vendor|supplier)",
]

# ============================================================
# COMAI ICP KEYWORDS
# ============================================================

COMAI_ICP_KEYWORDS: list[str] = [
    "ecommerce", "e-commerce", "d2c", "dtc", "shopify", "woocommerce",
    "online store", "ecommerce brand", "ecommerce business",
    "product brand", "consumer brand", "retail", "direct to consumer",
    "fashion", "beauty", "skincare", "jewellery", "home decor",
    "pets", "health", "supplements", "food", "beverage", "footwear",
    "electronics", "baby products", "grooming", "personal care",
    "lifestyle", "organic", "natural", "wellness",
]


# ============================================================
# PARTNER DISCOVERY ENGINE
# ============================================================

class PartnerDiscoveryEngine:
    """Core partner discovery engine for COMAI B2B.
    
    This engine discovers agencies, consultants, creators, and service
    providers that can become COMAI partners/resellers.
    
    SEPARATE from direct ecommerce leads.
    """
    
    def __init__(self):
        """Initialize the partner discovery engine."""
        self.evidence_trail: list[Evidence] = []
        
    async def discover_partner(
        self,
        url: str,
        company_name: str = "",
        source: str = "website",
    ) -> DiscoveryResult:
        """Discover a potential partner from a URL.
        
        Args:
            url: Agency website URL
            company_name: Company name (optional)
            source: Discovery source
            
        Returns:
            DiscoveryResult with partner qualification
        """
        start_time = time.time()
        result = DiscoveryResult(
            input_url=url,
            input_company_name=company_name,
            input_source=source,
            discovered_at=datetime.now(timezone.utc).isoformat(),
        )
        
        try:
            # Step 1: Fetch and analyze website
            html, headers = await self._fetch_website(url)
            if not html:
                result.rejection_reasons.append("Could not fetch website")
                result.classification = "REJECT"
                return result
            
            # Step 2: Detect agency type
            agency_type = self._detect_agency_type(html, url)
            if not agency_type:
                result.rejection_reasons.append("Not an agency or service provider")
                result.classification = "REJECT"
                return result
            
            result.is_agency = True
            result.agency_verified = True
            
            # Step 3: Check for reject patterns
            if self._check_reject_patterns(html, url):
                result.rejection_reasons.append("Matches reject pattern")
                result.classification = "REJECT"
                return result
            
            # Step 4: Check for competitor
            is_competitor = self._check_competitor(html, url)
            
            # Step 5: Extract partner information
            partner_record = await self._extract_partner_info(
                url=url,
                company_name=company_name,
                html=html,
                headers=headers,
                agency_type=agency_type,
                source=source,
            )
            
            # Step 6: Check for relevant service
            result.relevant_service = self._check_relevant_service(html, partner_record)
            
            # Step 7: Check for business clients
            result.business_clients_verified = self._check_business_clients(html, partner_record)
            
            # Step 8: Set competitor flag
            if partner_record:
                partner_record.competitor = is_competitor
            
            # Step 9: Classify
            result.classification = self._classify_partner(
                result.is_agency,
                result.agency_verified,
                result.relevant_service,
                result.business_clients_verified,
                is_competitor,
                partner_record,
            )
            
            # Step 10: Set partner record
            result.partner_record = partner_record
            
            # Step 11: Generate rejection reasons if needed
            if result.classification == "REJECT":
                if not result.rejection_reasons:
                    result.rejection_reasons.append("Did not meet partner qualification criteria")
            
        except Exception as e:
            logger.error(f"Error discovering partner from {url}: {e}")
            result.rejection_reasons.append(f"Processing error: {str(e)}")
            result.classification = "REJECT"
        
        # Set timing
        result.processing_time_ms = int((time.time() - start_time) * 1000)
        
        return result
    
    async def _fetch_website(self, url: str) -> tuple[str, dict]:
        """Fetch website HTML and headers."""
        try:
            async with httpx.AsyncClient(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                follow_redirects=True,
                timeout=httpx.Timeout(10.0),
            ) as client:
                resp = await client.get(url, timeout=8.0, follow_redirects=True)
                if resp.status_code == 200:
                    return resp.text[:100000], dict(resp.headers)
                else:
                    return "", {}
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return "", {}
    
    def _detect_agency_type(self, html: str, url: str) -> str | None:
        """Detect agency type from HTML content."""
        html_lower = html.lower()
        
        for agency_type, keywords in AGENCY_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in html_lower:
                    return agency_type
        
        return None
    
    def _check_reject_patterns(self, html: str, url: str) -> bool:
        """Check for reject patterns."""
        html_lower = html.lower()
        
        for pattern in REJECT_PATTERNS:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _check_competitor(self, html: str, url: str) -> bool:
        """Check if this is a competitor — HARD REJECT for WhatsApp/chatbot/white-label SaaS.
        
        COMAI B2B PARTNER DISCOVERY MUST FIND POTENTIAL DISTRIBUTION PARTNERS.
        WE ARE NOT LOOKING FOR COMPANIES THAT ALREADY SELL WHATSAPP CHATBOTS,
        AI CHATBOTS, WHATSAPP AUTOMATION, CONVERSATIONAL AI OR WHITE-LABEL
        CHATBOT SOFTWARE.
        
        Those companies are COMPETITORS and MUST be rejected.
        """
        html_lower = html.lower()
        
        # HARD COMPETITOR REJECTION PATTERNS
        # If ANY of these patterns match the company's core product/service → REJECT
        COMPETITOR_REJECTION_PATTERNS = [
            # WhatsApp/Chatbot SaaS
            r"whatsapp\s+(?:chatbot|automation|api|marketing|software|platform|reseller)",
            r"(?:chatbot|conversational\s+ai)\s+(?:saas|platform|builder|provider)",
            r"white[\s-]?label\s+(?:chatbot|whatsapp|messaging)",
            r"(?:customer\s+support|sales)\s+chatbot\s+(?:saas|platform|software)",
            r"cpaas|messaging\s+api\s+platform",
            r"conversational\s+commerce\s+platform",
            r"(?:ai|virtual)\s+(?:assistant|agent)\s+saas",
            # Specific competitor names (from CTO list)
            r"texnity",
            r"sendwo",
            r"sendseven",
            r"botpenguin",
            r"wassenger",
            r"zoko",
            r"wati\.io",
            r"aisensy",
            r"botlinkd",
            r"aishopix",
            r"ominiflow",
            r"whatsteam",
            r"easysocial",
            r"msgkart",
            r"inaiwazhi",
            r"kanal\.io",
            r"zefir\.com",
            r"chabo\.ai",
        ]
        
        # Check if they sell similar products
        for pattern in COMPETITOR_REJECTION_PATTERNS:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return True
        
        # Additional competitor detection: check for core product/service selling chatbot/WhatsApp SaaS
        competitor_core_signals = [
            "sell whatsapp",
            "sell chatbot",
            "sell conversational",
            "sell messaging platform",
            "sell white-label",
            "sell reseller platform",
            "sell cpaas",
            "chatbot platform",
            "chatbot provider",
            "chatbot builder",
            "whatsapp platform",
            "whatsapp provider",
            "messaging platform",
            "conversational platform",
            "customer engagement platform",
            "customer communication platform",
        ]
        
        competitor_count = sum(1 for signal in competitor_core_signals if signal in html_lower)
        if competitor_count >= 2:
            return True
        
        return False
    
    def _check_relevant_service(self, html: str, partner_record: PartnerRecord | None) -> bool:
        """Check if agency offers relevant services."""
        if not partner_record:
            return False
        
        html_lower = html.lower()
        
        relevant_services = [
            "marketing", "advertising", "ecommerce", "shopify", "woocommerce",
            "digital", "social media", "seo", "ppc", "google ads", "meta ads",
            "lead generation", "crm", "automation", "email marketing",
            "content", "branding", "creative", "consulting", "development",
        ]
        
        for service in relevant_services:
            if service in html_lower:
                return True
        
        return False
    
    def _check_business_clients(self, html: str, partner_record: PartnerRecord | None) -> bool:
        """Check if agency has business clients."""
        if not partner_record:
            return False
        
        html_lower = html.lower()
        
        # Check for client evidence patterns
        for signal_type, patterns in CLIENT_EVIDENCE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, html_lower, re.IGNORECASE):
                    return True
        
        # Check for client logos or portfolio
        if "client" in html_lower and ("logo" in html_lower or "portfolio" in html_lower):
            return True
        
        # Check for case studies
        if "case study" in html_lower or "case studies" in html_lower:
            return True
        
        # Check for client count evidence (more flexible)
        client_count_patterns = [
            r"(\d+)\+?\s+(?:clients?|brands?|businesses?|companies|partners?)",
            r"(?:work|client|partner|brand|business)\s+(?:list|section|page|portfolio)",
            r"(?:our|we)\s+(?:client|partner|brand|business)",
            r"(?:trusted|working|partnering)\s+(?:with|by)",
            r"(?:help|serve|support|manage)\s+(?:\d+\+?\s+)?(?:businesses?|companies|clients?|brands?)",
            r"(?:growing|scaling|helping)\s+(?:businesses?|companies|clients?|brands?)",
            r"(?:ecommerce|d2c|shopify|online\s+store)\s+(?:businesses?|companies|clients?|brands?|stores?)",
            r"(?:brands?|businesses?|companies|clients?)\s+(?:like|such\s+as|including)",
        ]
        
        for pattern in client_count_patterns:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return True
        
        # Check for service pages that imply client work
        service_implications = [
            "our process", "how we work", "our approach", "what we do",
            "services", "solutions", "what we offer", "our expertise",
        ]
        
        for implication in service_implications:
            if implication in html_lower:
                return True
        
        return False
    
    async def _extract_partner_info(
        self,
        url: str,
        company_name: str,
        html: str,
        headers: dict,
        agency_type: str,
        source: str,
    ) -> PartnerRecord:
        """Extract partner information from HTML."""
        partner = PartnerRecord(
            opportunity_id=str(uuid.uuid4()),
            agency_url=url,
            country=self._extract_country(html, url),
            city=self._extract_city(html, url),
            agency_type=agency_type,
            discovered_at=datetime.now(timezone.utc).isoformat(),
            last_updated=datetime.now(timezone.utc).isoformat(),
            discovery_source=source,
        )
        
        # Extract agency name
        if company_name:
            partner.agency_name = company_name
        else:
            partner.agency_name = self._extract_company_name(html, url)
        
        # Extract services
        partner.services = self._extract_services(html, agency_type)
        
        # Extract client evidence
        partner.client_count_evidence = self._extract_client_count_evidence(html)
        partner.client_examples = self._extract_client_examples(html)
        partner.client_industries = self._extract_client_industries(html)
        
        # Extract contact information
        await self._extract_contact_info(html, url, partner)
        
        # Extract partner intent
        partner.partner_intent, partner.partner_intent_evidence = self._extract_partner_intent(html)
        
        return partner
    
    def _extract_country(self, html: str, url: str) -> str:
        """Extract country from HTML or URL."""
        html_lower = html.lower()
        
        country_indicators = {
            "usa": ["united states", "usa", "us", "american", "new york", "los angeles", "san francisco", "chicago", "boston", "seattle", "austin", "miami"],
            "uk": ["united kingdom", "uk", "british", "london", "manchester", "birmingham", "leeds", "glasgow", "edinburgh"],
            "canada": ["canada", "canadian", "toronto", "vancouver", "montreal", "calgary", "ottawa"],
            "australia": ["australia", "australian", "sydney", "melbourne", "brisbane", "perth", "adelaide"],
            "uae": ["uae", "dubai", "abu dhabi", "sharjah", "emirates", "dubai, uae"],
            "singapore": ["singapore", "sg"],
            "germany": ["germany", "german", "berlin", "munich", "hamburg", "frankfurt", "cologne"],
            "netherlands": ["netherlands", "dutch", "amsterdam", "rotterdam", "the hague", "utrecht"],
            "ireland": ["ireland", "irish", "dublin", "cork", "galway"],
            "new_zealand": ["new zealand", "nz", "auckland", "wellington", "christchurch"],
            "india": ["india", "indian", "mumbai", "delhi", "bangalore", "bengaluru", "chennai", "hyderabad", "pune", "kolkata", "ahmedabad", "gurugram"],
        }
        
        for country, indicators in country_indicators.items():
            for indicator in indicators:
                if indicator in html_lower:
                    return country.upper()
        
        return "UNKNOWN"
    
    def _extract_city(self, html: str, url: str) -> str:
        """Extract city from HTML or URL."""
        html_lower = html.lower()
        
        cities = [
            "new york", "los angeles", "san francisco", "chicago", "boston", "seattle", "austin", "miami",
            "london", "manchester", "birmingham", "leeds", "glasgow", "edinburgh",
            "toronto", "vancouver", "montreal", "calgary", "ottawa",
            "sydney", "melbourne", "brisbane", "perth", "adelaide",
            "dubai", "abu dhabi", "sharjah",
            "singapore",
            "berlin", "munich", "hamburg", "frankfurt", "cologne",
            "amsterdam", "rotterdam", "the hague", "utrecht",
            "dublin", "cork", "galway",
            "auckland", "wellington", "christchurch",
            "mumbai", "delhi", "bangalore", "bengaluru", "chennai", "hyderabad", "pune", "kolkata", "ahmedabad", "gurugram",
        ]
        
        for city in cities:
            if city in html_lower:
                return city.title()
        
        return "UNKNOWN"
    
    def _extract_company_name(self, html: str, url: str) -> str:
        """Extract company name from HTML."""
        # Try to extract from title tag
        title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            # Remove common suffixes
            for suffix in [" | Home", " | About", " | Contact", " | Services", " - Home", " - About", " - Contact", " - Services"]:
                if suffix.lower() in title.lower():
                    title = title[:title.lower().index(suffix.lower())]
            return title[:100]
        
        # Try to extract from h1 tag
        h1_match = re.search(r"<h1[^>]*>([^<]+)</h1>", html, re.IGNORECASE)
        if h1_match:
            return h1_match.group(1).strip()[:100]
        
        # Extract from URL
        url_parts = url.rstrip("/").split("/")
        if len(url_parts) >= 3:
            domain = url_parts[2]
            # Remove www. and common TLDs
            for prefix in ["www.", "app.", "api."]:
                if domain.startswith(prefix):
                    domain = domain[len(prefix):]
            for tld in [".com", ".co", ".io", ".agency", ".digital", ".marketing"]:
                if domain.endswith(tld):
                    domain = domain[:-len(tld)]
            return domain.replace("-", " ").title()
        
        return "Unknown Agency"
    
    def _extract_services(self, html: str, agency_type: str) -> list[str]:
        """Extract services from HTML."""
        services = []
        html_lower = html.lower()
        
        service_keywords = {
            "marketing": ["digital marketing", "performance marketing", "social media marketing", "seo", "ppc", "google ads", "meta ads", "facebook ads", "lead generation", "email marketing", "sms marketing", "content marketing"],
            "technology": ["web development", "website development", "shopify development", "woocommerce development", "ecommerce development", "mobile app development", "saas development", "software development", "ui/ux design", "automation", "ai solutions", "crm implementation"],
            "creative": ["video production", "content creation", "creative design", "branding", "influencer marketing", "social media content", "graphic design", "motion graphics", "animation"],
            "consultant": ["ecommerce consulting", "d2c consulting", "growth consulting", "sales consulting", "business consulting", "marketing consulting", "shopify consulting", "technology consulting"],
        }
        
        keywords = service_keywords.get(agency_type, [])
        for keyword in keywords:
            if keyword in html_lower:
                services.append(keyword)
        
        return services[:10]  # Limit to 10 services
    
    def _extract_client_count_evidence(self, html: str) -> str:
        """Extract client count evidence from HTML."""
        html_lower = html.lower()
        
        # Look for client count patterns (more flexible)
        patterns = [
            r"(\d+)\+?\s+(?:clients?|brands?|businesses?|companies|partners?)",
            r"(?:over|more\s+than|than|about|around|over)\s+(\d+)\+?\s+(?:clients?|brands?|businesses?|companies|partners?)",
            r"(?:we\s+)?(?:have|work\s+with|serve|partner\s+with|help|support|manage)\s+(\d+)\+?\s+(?:clients?|brands?|businesses?|companies|partners?)",
            r"(?:trusted\s+by|working\s+with|serving)\s+(\d+)\+?\s+(?:clients?|brands?|businesses?|companies|partners?)",
            r"(\d+)\+?\s+(?:happy|satisfied|global|active)\s+(?:clients?|brands?|businesses?|companies|partners?)",
            r"(?:portfolio|case\s*studies?|work)\s+(?:of|with|includes?)\s+(\d+)\+?\s+",
            r"(\d{2,})\+?\s+(?:projects?|campaigns?|brands?|businesses?)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_lower)
            if match:
                count = match.group(1)
                return f"{count}+ clients"
        
        # Check for portfolio/client sections
        portfolio_indicators = [
            "our clients", "client list", "our work", "case studies",
            "portfolio", "brands we work with", "trusted by",
            "our portfolio", "client logos", "partner logos",
        ]
        
        for indicator in portfolio_indicators:
            if indicator in html_lower:
                return "Portfolio/clients section found"
        
        return ""
    
    def _extract_client_examples(self, html: str) -> list[str]:
        """Extract client examples from HTML."""
        # This would require more sophisticated parsing
        # For now, return empty list
        return []
    
    def _extract_client_industries(self, html: str) -> list[str]:
        """Extract client industries from HTML."""
        industries = []
        html_lower = html.lower()
        
        industry_keywords = {
            "ecommerce": ["ecommerce", "e-commerce", "online store", "online shop"],
            "d2c": ["d2c", "dtc", "direct to consumer"],
            "fashion": ["fashion", "clothing", "apparel", "wear"],
            "beauty": ["beauty", "skincare", "cosmetics", "makeup"],
            "jewellery": ["jewellery", "jewelry", "accessories"],
            "home decor": ["home decor", "home goods", "furniture"],
            "food & beverage": ["food", "beverage", "restaurant", "cafe"],
            "health": ["health", "wellness", "fitness", "supplements"],
            "technology": ["technology", "software", "saas", "tech"],
            "retail": ["retail", "store", "shop"],
        }
        
        for industry, keywords in industry_keywords.items():
            for keyword in keywords:
                if keyword in html_lower:
                    industries.append(industry)
                    break
        
        return list(set(industries))[:5]  # Limit to 5 industries
    
    async def _extract_contact_info(self, html: str, url: str, partner: PartnerRecord):
        """Extract contact information from HTML."""
        # Extract emails from mailto: links (preferred)
        mailto_pattern = re.compile(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})')
        mailto_emails = mailto_pattern.findall(html)
        
        # Also extract emails from text
        email_pattern = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
        text_emails = email_pattern.findall(html)
        
        # Combine and filter valid emails
        all_emails = list(dict.fromkeys(mailto_emails + text_emails))  # dedupe preserving order
        valid_emails = []
        for email in all_emails:
            email_lower = email.lower()
            # Skip image files and invalid patterns
            if any(ext in email_lower for ext in [".jpg", ".png", ".gif", ".svg", ".webp", "@2x", "assets", "cdn", "static", "media", "images", "files", "base64", "sentry", "webpack"]):
                continue
            # Skip free email providers for business emails
            free_email = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com"}
            domain = email.split("@")[-1] if "@" in email else ""
            if domain in free_email:
                continue
            valid_emails.append(email)
        
        if valid_emails:
            partner.email = valid_emails[0]
            partner.email_status = "PUBLIC_UNVERIFIED"
            partner.email_evidence = "Found on website (mailto/text)"
        
        # Extract phone numbers from tel: links
        tel_pattern = re.compile(r'tel:([+\d()-]+)')
        tel_phones = tel_pattern.findall(html)
        
        # Also extract phone numbers from text (US format)
        phone_pattern = re.compile(r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        text_phones = phone_pattern.findall(html)
        
        all_phones = list(dict.fromkeys(tel_phones + text_phones))
        if all_phones and not partner.business_phone:
            partner.business_phone = all_phones[0]
        
        # Extract LinkedIn from social links
        linkedin_pattern = re.compile(r'linkedin\.com/(?:company|in)/[a-zA-Z0-9\-]+')
        linkedin_matches = linkedin_pattern.findall(html)
        if linkedin_matches:
            partner.linkedin_url = f"https://{linkedin_matches[0]}"
            partner.linkedin_status = "FOUND"
        
        # Extract founder/CEO name
        founder_patterns = [
            r"(?:founder|ceo|co-founder|cofounder|owner|managing\s+director)[\s:]+([A-Z][a-z]+ [A-Z][a-z]+)",
            r"(?:founder|ceo|co-founder|cofounder|owner|managing\s+director)[\s:]+([A-Z][a-z]+)",
        ]
        
        for pattern in founder_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                partner.founder_name = match.group(1)
                partner.founder_role = "Founder"
                partner.identity_confidence = 0.7
                break
        
        # Extract contact page URL
        contact_patterns = [
            r'href=["\']([^"\']*contact[^"\']*)["\']',
            r'href=["\']([^"\']*about[^"\']*)["\']',
        ]
        
        for pattern in contact_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                contact_url = match.group(1)
                if contact_url.startswith("/"):
                    contact_url = url.rstrip("/") + contact_url
                partner.contactability_evidence = f"Contact page: {contact_url}"
                break
    
    def _extract_partner_intent(self, html: str) -> tuple[str, str]:
        """Extract partner intent from HTML."""
        html_lower = html.lower()
        
        # Check for high-intent signals
        for signal_type, patterns in HIGH_INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, html_lower, re.IGNORECASE):
                    return "EXPLICIT", f"Signal: {signal_type}"
        
        return "UNKNOWN", ""
    
    def _classify_partner(
        self,
        is_agency: bool,
        agency_verified: bool,
        relevant_service: bool,
        business_clients_verified: bool,
        is_competitor: bool,
        partner_record: PartnerRecord | None,
    ) -> str:
        """Classify partner based on verification results."""
        if is_competitor:
            return "REJECT"
        
        if not is_agency or not agency_verified:
            return "REJECT"
        
        if not relevant_service:
            return "REJECT"
        
        if not business_clients_verified:
            return "REJECT"
        
        return "QUALIFIED"
