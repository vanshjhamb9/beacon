"""Enhanced Technology Detection for ecommerce stacks.

Detects the full technology stack of Indian D2C ecommerce companies.
Every detection must have a confidence score and evidence URL.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TechHit:
    """Single technology detection hit."""

    name: str
    category: str
    confidence: float  # 0-1
    evidence: str  # What was detected
    evidence_url: str  # Where it was detected

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "confidence": round(self.confidence, 3),
            "evidence": self.evidence,
            "evidence_url": self.evidence_url,
        }


@dataclass
class TechStack:
    """Complete detected technology stack."""

    platform: str
    platform_confidence: float
    technologies: list[TechHit]
    ecommerce_platform: str
    email_marketing: str
    review_platform: str
    support_tool: str
    payment_gateway: str
    shipping_provider: str
    analytics: str
    whatsapp_tool: str
    ai_chatbot: str
    crm: str
    has_chatbot: bool
    has_whatsapp: bool
    has_ai: bool
    automation_maturity: str  # "none", "basic", "moderate", "advanced"

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "platform_confidence": round(self.platform_confidence, 3),
            "technologies": [t.to_dict() for t in self.technologies],
            "ecommerce_platform": self.ecommerce_platform,
            "email_marketing": self.email_marketing,
            "review_platform": self.review_platform,
            "support_tool": self.support_tool,
            "payment_gateway": self.payment_gateway,
            "shipping_provider": self.shipping_provider,
            "analytics": self.analytics,
            "whatsapp_tool": self.whatsapp_tool,
            "ai_chatbot": self.ai_chatbot,
            "crm": self.crm,
            "has_chatbot": self.has_chatbot,
            "has_whatsapp": self.has_whatsapp,
            "has_ai": self.has_ai,
            "automation_maturity": self.automation_maturity,
        }


class COMAITechDetector:
    """Enhanced technology detection for ecommerce stacks.

    Detects 40+ technologies across 12 categories.
    Each detection returns confidence and evidence.
    """

    # --- Ecommerce Platforms ---
    ECOMMERCE_PLATFORMS: dict[str, dict[str, Any]] = {
        "shopify": {
            "patterns": [
                r"cdn\.shopify\.com",
                r"shopify[a-z_]*",
                r"Shopify\.theme",
                r"myshopify\.com",
                r"assets\.shopifycdn\.com",
                r"shopify-section",
                r"liquid",
                r"shop\.json",
                r"products\.json\?limit",
            ],
            "weight": 1.0,
        },
        "shopify_plus": {
            "patterns": [
                r"shopify-plus",
                r"Shopify\.shop",
                r"enterprise.*shopify",
            ],
            "weight": 1.0,
        },
        "woocommerce": {
            "patterns": [
                r"woocommerce",
                r"wc[-_]ajax",
                r"wp-content/plugins/woocommerce",
                r"woocommerce-session",
                r"add[-_]to[-_]cart.*woocommerce",
            ],
            "weight": 0.9,
        },
        "magento": {
            "patterns": [
                r"magento",
                r"Mage\.",
                r"skin/frontend",
                r"catalog/product",
                r"checkout/cart",
            ],
            "weight": 0.8,
        },
        "bigcommerce": {
            "patterns": [
                r"bigcommerce",
                r"bc-sell-widget",
                r"bigcommercetheme",
            ],
            "weight": 0.6,
        },
        "prestashop": {
            "patterns": [
                r"prestashop",
                r"prestaShop",
                r"themes/prestashop",
            ],
            "weight": 0.5,
        },
    }

    # --- Email Marketing ---
    EMAIL_MARKETING: dict[str, list[str]] = {
        "klaviyo": [r"klaviyo", r"klaviyo\.com", r"_klOnsite"],
        "mailchimp": [r"mailchimp", r"list-manage\.com", r"mc\.us"],
        "sendgrid": [r"sendgrid", r"sendgrid\.net", r"sglick"],
        "drip": [r"drip\.com", r"drip-email"],
        "activecampaign": [r"activecampaign", r"track\.active"],
        "omnisend": [r"omnisend", r"omnisend\.com"],
    }

    # --- Review Platforms ---
    REVIEW_PLATFORMS: dict[str, list[str]] = {
        "judge.me": [r"judge\.me", r"judge\.me/reviews", r"jdgm"],
        "yotpo": [r"yotpo", r"yotpo\.com", r"yotpo-widget"],
        "stamped": [r"stamped\.io", r"stamped-reviews"],
        "trustpilot": [r"trustpilot", r"trustpilot\.com"],
        "loox": [r"loox\.app", r"loox-reviews"],
        "okendo": [r"okendo", r"okendo\.io"],
    }

    # --- Support Tools ---
    SUPPORT_TOOLS: dict[str, list[str]] = {
        "zendesk": [r"zendesk", r"zdassets\.com", r"zendesk\.com"],
        "freshdesk": [r"freshdesk", r"freshworks\.com", r"freshdesk\.com"],
        "intercom": [r"intercom", r"intercomcdn\.com", r"intercom\.io"],
        "gorgias": [r"gorgias", r"gorgias\.io", r"gorgias\.com"],
        "tidio": [r"tidio", r"tidio\.co", r"tidio\.com"],
        "tawkto": [r"tawk\.to", r"tawkto"],
        "crisp": [r"crisp\.chat", r"crisp-chat"],
        "livechat": [r"livechat", r"livechatinc\.com"],
        "helpscout": [r"helpscout", r"helpscout\.com"],
    }

    # --- Payment Gateways ---
    PAYMENT_GATEWAYS: dict[str, list[str]] = {
        "razorpay": [r"razorpay", r"razorpay\.com", r"rzp\.io"],
        "cashfree": [r"cashfree", r"cashfree\.com"],
        "payu": [r"payu", r"payu\.com", r"payu\.in"],
        "stripe": [r"stripe\.com", r"stripe\.js", r"Stripe\("],
        "paypal": [r"paypal", r"paypalobjects\.com"],
        "instamojo": [r"instamojo", r"instamojo\.com"],
        "ccavenue": [r"ccavenue", r"ccavenue\.com"],
        "billdesk": [r"billdesk", r"billdesk\.com"],
    }

    # --- Shipping Providers ---
    SHIPPING_PROVIDERS: dict[str, list[str]] = {
        "shiprocket": [r"shiprocket", r"shiprocket\.in", r"shiprocket\.io"],
        "delhivery": [r"delhivery", r"delhivery\.com"],
        "bluedart": [r"bluedart", r"bluedart\.com"],
        "dhl": [r"dhl\.com", r"dhl-express"],
        "fedex": [r"fedex", r"fedex\.com"],
        "shipway": [r"shipway", r"shipway\.com"],
        "shippobo": [r"shippobo", r"shippobo\.com"],
    }

    # --- Analytics ---
    ANALYTICS_TOOLS: dict[str, list[str]] = {
        "google_analytics": [r"google-analytics\.com", r"gtag", r"GA_MEASUREMENT_ID"],
        "ga4": [r"gtag/js/G-", r"GA4", r"google_tag_manager"],
        "hotjar": [r"hotjar", r"hotjar\.com", r"hj\("],
        "mixpanel": [r"mixpanel", r"mixpanel\.com"],
        "amplitude": [r"amplitude", r"amplitude\.com"],
        "segment": [r"segment\.com/analytics", r"analytics\.js"],
        "clarity": [r"clarity\.ms", r"microsoft\.com/clarity"],
    }

    # --- WhatsApp Tools ---
    WHATSAPP_TOOLS: dict[str, list[str]] = {
        "whatsapp_business_api": [r"api\.whatsapp\.com", r"wa\.me"],
        "wati": [r"wati\.io", r"wati\.in"],
        "aisensy": [r"aisensy", r"aisensy\.com"],
        "interakt": [r"interakt\.shop", r"interakt"],
        "whatsapp_widget": [r"whatsapp.*widget", r"wa-button"],
    }

    # --- AI Chatbots (competitors) ---
    AI_CHATBOTS: dict[str, list[str]] = {
        "gorgias_ai": [r"gorgias.*ai", r"auto-reply"],
        "tidio_ai": [r"tidio.*ai", r"lyro"],
        "intercom_fin": [r"intercom.*fin", r"fin\.ai"],
        "drift": [r"drift\.com", r"drift-chat"],
        "zendesk_ai": [r"zendesk.*ai", r"answer bot"],
        "freshdesk_freddy": [r"freddy\.ai", r"freshdesk.*ai"],
        "zendesk_chat": [r"zendesk-chat", r"zopim"],
        "crisp_chatbot": [r"crisp.*bot", r"crisp.*ai"],
        "chatgpt_widget": [r"chatgpt", r"openai.*widget"],
        "custom_ai": [r"ai.*chatbot", r"chatbot.*ai", r"powered by ai"],
    }

    # --- CRM ---
    CRM_TOOLS: dict[str, list[str]] = {
        "hubspot": [r"hubspot", r"hs-scripts", r"hubspot\.com"],
        "salesforce": [r"salesforce", r"sforce\.com"],
        "zoho": [r"zoho\.com", r"zohocrm"],
        "freshsales": [r"freshsales", r"freshworks.*crm"],
        "pipedrive": [r"pipedrive", r"pipedrive\.com"],
    }

    # --- Marketing Automation ---
    MARKETING_AUTOMATION: dict[str, list[str]] = {
        "zapier": [r"zapier", r"zapier\.com"],
        "make": [r"make\.com", r"integromat"],
        "pabbly": [r"pabbly", r"pabbly\.com"],
    }

    # --- Other Tools ---
    OTHER_TOOLS: dict[str, list[str]] = {
        "google_tag_manager": [r"googletagmanager\.com", r"GTM-"],
        "meta_pixel": [r"fbevents\.js", r"fbq\(", r"facebook.*pixel"],
        "tiktok_pixel": [r"analytics\.tiktok\.com", r"tiktok.*pixel"],
        "snapchat_pixel": [r"tr\.snapchat\.com", r"snap.*pixel"],
        "pinterest_tag": [r"pintrk\(", r"pinterest.*tag"],
        "loyalty_program": [r"loyalty", r"reward.*program", r"smile\.io", r"loyaltylion"],
        "upsell_tool": [r"upsell", r"rebuy", r"in-cart"],
        "bundle_app": [r"bundle", r"bundle.*app"],
        "tracking_page": [r"tracking.*page", r"aftership", r"parcelpanel", r"tracktor"],
        "knowledge_base": [r"knowledge.*base", r"help.*center", r"faq.*page"],
    }

    def detect_all(self, html: str, url: str) -> TechStack:
        """Detect entire technology stack from website HTML.

        Args:
            html: Full HTML content of the website.
            url: Website URL for evidence tracking.

        Returns:
            TechStack with all detected technologies.
        """
        hits: list[TechHit] = []

        # Detect ecommerce platform
        platform, platform_conf = self._detect_platform(html, url, hits)

        # Detect all other categories
        email_mkt = self._detect_category(html, url, self.EMAIL_MARKETING, "email_marketing", hits)
        reviews = self._detect_category(html, url, self.REVIEW_PLATFORMS, "review_platform", hits)
        support = self._detect_category(html, url, self.SUPPORT_TOOLS, "support_tool", hits)
        payments = self._detect_category(html, url, self.PAYMENT_GATEWAYS, "payment_gateway", hits)
        shipping = self._detect_category(html, url, self.SHIPPING_PROVIDERS, "shipping_provider", hits)
        analytics = self._detect_category(html, url, self.ANALYTICS_TOOLS, "analytics", hits)
        whatsapp = self._detect_category(html, url, self.WHATSAPP_TOOLS, "whatsapp_tool", hits)
        ai_chatbot = self._detect_category(html, url, self.AI_CHATBOTS, "ai_chatbot", hits)
        crm = self._detect_category(html, url, self.CRM_TOOLS, "crm", hits)
        self._detect_category(html, url, self.MARKETING_AUTOMATION, "marketing_automation", hits)
        self._detect_category(html, url, self.OTHER_TOOLS, "other", hits)

        # Determine boolean flags
        has_chatbot = any(h.category == "ai_chatbot" for h in hits) or support != "none"
        has_whatsapp = whatsapp != "none"
        has_ai = ai_chatbot != "none"

        # Determine automation maturity
        maturity = self._assess_maturity(hits)

        return TechStack(
            platform=platform,
            platform_confidence=platform_conf,
            technologies=hits,
            ecommerce_platform=platform,
            email_marketing=email_mkt,
            review_platform=reviews,
            support_tool=support,
            payment_gateway=payments,
            shipping_provider=shipping,
            analytics=analytics,
            whatsapp_tool=whatsapp,
            ai_chatbot=ai_chatbot,
            crm=crm,
            has_chatbot=has_chatbot,
            has_whatsapp=has_whatsapp,
            has_ai=has_ai,
            automation_maturity=maturity,
        )

    def _detect_platform(
        self, html: str, url: str, hits: list[TechHit]
    ) -> tuple[str, float]:
        """Detect ecommerce platform. Returns (platform, confidence)."""
        best_platform = "unknown"
        best_confidence = 0.0

        for platform, config in self.ECOMMERCE_PLATFORMS.items():
            matches = 0
            for pattern in config["patterns"]:
                if re.search(pattern, html, re.IGNORECASE):
                    matches += 1
            if matches > 0:
                confidence = min(matches * 0.3, 1.0) * config["weight"]
                if confidence > best_confidence:
                    best_platform = platform
                    best_confidence = confidence
                hits.append(TechHit(
                    name=platform,
                    category="ecommerce_platform",
                    confidence=confidence,
                    evidence=f"{matches} pattern(s) matched",
                    evidence_url=url,
                ))

        return best_platform, best_confidence

    def _detect_category(
        self,
        html: str,
        url: str,
        patterns: dict[str, list[str]],
        category: str,
        hits: list[TechHit],
    ) -> str:
        """Detect tools in a category. Returns the best match name or 'none'."""
        best_name = "none"
        best_confidence = 0.0

        for name, regexes in patterns.items():
            matches = 0
            for pattern in regexes:
                if re.search(pattern, html, re.IGNORECASE):
                    matches += 1
            if matches > 0:
                confidence = min(matches * 0.35, 1.0)
                if confidence > best_confidence:
                    best_name = name
                    best_confidence = confidence
                hits.append(TechHit(
                    name=name,
                    category=category,
                    confidence=confidence,
                    evidence=f"{matches} pattern(s) matched",
                    evidence_url=url,
                ))

        return best_name

    def _assess_maturity(self, hits: list[TechHit]) -> str:
        """Assess overall automation maturity."""
        categories_found = set(h.category for h in hits)
        high_confidence = sum(1 for h in hits if h.confidence >= 0.7)

        if len(categories_found) >= 6 and high_confidence >= 4:
            return "advanced"
        if len(categories_found) >= 4 and high_confidence >= 2:
            return "moderate"
        if len(categories_found) >= 2:
            return "basic"
        return "none"
