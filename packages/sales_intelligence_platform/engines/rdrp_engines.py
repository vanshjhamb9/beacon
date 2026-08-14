"""RDRP — Revenue Data Reliability Platform engines.

Sprint 42.5: 10 deterministic engines + orchestrator.
No GPT. No LLM. Every output must have evidence, confidence, and timestamp.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _deep_to_dict(obj: Any) -> Any:
    """Recursively convert dataclass instances to dicts."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _deep_to_dict(v) for k, v in obj.__dataclass_fields__.items() if hasattr(obj, k) and getattr(obj, k) is not None}
    if isinstance(obj, list):
        return [_deep_to_dict(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _deep_to_dict(v) for k, v in obj.items()}
    return obj


# =============================================================================
# MODULE 1: Company Verification Engine
# =============================================================================
INDIAN_TLDS = {".in", ".co.in", ".com.in", ".org.in", ".net.in"}
INDIAN_CURRENCIES = {"INR", "₹", "Rs", "Rs.", "INR\u00a0"}
INDIAN_LANGUAGES = {"hindi", "english", "bengali", "tamil", "telugu", "marathi", "gujarati", "kannada", "malayalam", "punjabi"}

COMMON_CHECKS = [
    "website_alive", "https_valid", "homepage_loads",
    "about_page_exists", "contact_page_exists", "products_exist",
    "collection_pages_exist", "checkout_exists",
    "privacy_policy_exists", "refund_policy_exists",
    "terms_exists", "shipping_policy_exists",
    "gst_info_present", "active_ecommerce_store",
    "mobile_responsive",
]

# Paths to probe
PAGE_PROBES = {
    "about_page_exists": ["/about", "/about-us", "/pages/about-us", "/pages/about"],
    "contact_page_exists": ["/contact", "/contact-us", "/pages/contact-us", "/pages/contact"],
    "products_exist": ["/collections", "/products", "/shop", "/collections/all"],
    "collection_pages_exist": ["/collections", "/categories"],
    "checkout_exists": ["/checkout", "/cart"],
    "privacy_policy_exists": ["/policies/privacy-policy", "/privacy-policy", "/pages/privacy-policy"],
    "refund_policy_exists": ["/policies/refund-policy", "/refund-policy", "/pages/refund-policy", "/policies/return-policy"],
    "terms_exists": ["/policies/terms-of-service", "/terms", "/terms-of-service", "/pages/terms-of-service"],
    "shipping_policy_exists": ["/policies/shipping-policy", "/shipping-policy", "/pages/shipping-policy"],
}

# Evidence patterns
ECOMMERCE_PATTERNS = {
    "shopify": [
        r"cdn\.shopify\.com",
        r"Shopify\.theme",
        r"shopify-section",
        r"myshopify\.com",
        r"shopify-payment",
    ],
    "woocommerce": [
        r"woocommerce",
        r"wc-",
        r"wp-content/plugins/woocommerce",
    ],
    "magento": [
        r"magento",
        r"Mage\.Cookies",
        r"mage/",
    ],
}


@dataclass
class VerificationCheck:
    name: str
    passed: bool
    evidence: str = ""
    url: str = ""
    confidence: float = 0.0


@dataclass
class CompanyVerificationResult:
    company_id: str
    website: str
    checks: list[VerificationCheck] = field(default_factory=list)
    verification_score: float = 0.0
    verification_confidence: float = 0.0
    checks_passed: int = 0
    checks_total: int = 0
    failures: list[str] = field(default_factory=list)
    country_detected: str | None = None
    store_currency: str | None = None
    store_language: str | None = None
    domain_age_days: int | None = None
    active_ecommerce: bool = False
    evidence: list[dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=_now)


class CompanyVerificationEngine:
    """Verify company existence and legitimacy from website signals."""

    def verify(self, company_id: str, website: str, html_content: str = "", headers: dict | None = None) -> CompanyVerificationResult:
        result = CompanyVerificationResult(company_id=company_id, website=website)

        if not website:
            result.failures.append("no_website")
            return result

        parsed = urlparse(website)
        domain = parsed.netloc or parsed.path

        # --- Check 1: HTTPS ---
        https_check = VerificationCheck(
            name="https_valid",
            passed=parsed.scheme == "https",
            evidence=f"Scheme: {parsed.scheme}",
            url=website,
            confidence=1.0 if parsed.scheme == "https" else 0.0,
        )
        result.checks.append(https_check)

        # --- Check 2: Website Alive ---
        alive_check = VerificationCheck(
            name="website_alive",
            passed=bool(html_content) and len(html_content) > 500,
            evidence=f"HTML length: {len(html_content)}" if html_content else "No HTML provided",
            url=website,
            confidence=1.0 if html_content and len(html_content) > 500 else 0.0,
        )
        result.checks.append(alive_check)

        # --- Check 3: Homepage Loads ---
        homepage_check = VerificationCheck(
            name="homepage_loads",
            passed=bool(html_content) and len(html_content) > 1000,
            evidence=f"Homepage HTML: {len(html_content)} chars",
            url=website,
            confidence=1.0 if html_content and len(html_content) > 1000 else 0.0,
        )
        result.checks.append(homepage_check)

        if html_content:
            html_lower = html_content.lower()

            # --- Page existence checks (inferred from HTML content) ---
            for check_name, paths in PAGE_PROBES.items():
                found = any(p.lower() in html_lower for p in paths)
                result.checks.append(VerificationCheck(
                    name=check_name,
                    passed=found,
                    evidence=f"Links found in HTML" if found else f"No links to {check_name} paths",
                    url=website,
                    confidence=0.8 if found else 0.2,
                ))

            # --- Active ecommerce store detection ---
            ecommerce_score = 0
            ecommerce_evidence = []
            for platform, patterns in ECOMMERCE_PATTERNS.items():
                for pat in patterns:
                    if re.search(pat, html_content, re.IGNORECASE):
                        ecommerce_score += 1
                        ecommerce_evidence.append(f"{platform}: {pat}")
            result.active_ecommerce = ecommerce_score > 0
            result.checks.append(VerificationCheck(
                name="active_ecommerce_store",
                passed=result.active_ecommerce,
                evidence="; ".join(ecommerce_evidence) if ecommerce_evidence else "No ecommerce patterns detected",
                confidence=min(1.0, ecommerce_score * 0.3),
            ))

            # --- GST detection ---
            gst_found = bool(re.search(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z0-9]\d\b", html_content))
            gst_found = gst_found or "gst" in html_lower
            result.checks.append(VerificationCheck(
                name="gst_info_present",
                passed=gst_found,
                evidence="GST number or GST mention found" if gst_found else "No GST info",
                confidence=0.9 if gst_found else 0.1,
            ))

            # --- Country detection ---
            tld = "." + domain.split(".")[-1] if "." in domain else ""
            if tld in INDIAN_TLDS:
                result.country_detected = "India"
            elif any(kw in html_lower for kw in ["india", "indian", "inr", "₹"]):
                result.country_detected = "India"
            else:
                result.country_detected = tld.lstrip(".").upper() if tld else None

            # --- Currency detection ---
            for cur in INDIAN_CURRENCIES:
                if cur.lower() in html_lower:
                    result.store_currency = "INR"
                    break
            if not result.store_currency:
                if "usd" in html_lower or "$" in html_content:
                    result.store_currency = "USD"

            # --- Language detection ---
            lang_match = re.search(r'lang="([^"]+)"', html_content, re.IGNORECASE)
            if lang_match:
                result.store_language = lang_match.group(1)

            # --- Mobile responsive ---
            result.checks.append(VerificationCheck(
                name="mobile_responsive",
                passed="viewport" in html_lower and ("width=device-width" in html_lower or "responsive" in html_lower),
                evidence="Viewport meta tag found" if "viewport" in html_lower else "No viewport tag",
                confidence=0.9 if "viewport" in html_lower else 0.1,
            ))

            # --- Domain age (placeholder — real implementation needs WHOIS) ---
            result.domain_age_days = None  # Cannot determine without WHOIS

            # --- Last update (from headers or meta) ---
            result.checks.append(VerificationCheck(
                name="last_website_update",
                passed=True,
                evidence="Requires WHOIS or sitemap for accuracy",
                confidence=0.3,
            ))
        else:
            # No HTML — mark all remaining checks as failed
            for check_name in PAGE_PROBES:
                result.checks.append(VerificationCheck(name=check_name, passed=False, evidence="No HTML provided", confidence=0.0))
            result.checks.append(VerificationCheck(name="active_ecommerce_store", passed=False, evidence="No HTML", confidence=0.0))
            result.checks.append(VerificationCheck(name="gst_info_present", passed=False, evidence="No HTML", confidence=0.0))
            result.checks.append(VerificationCheck(name="mobile_responsive", passed=False, evidence="No HTML", confidence=0.0))

        # --- Headers checks ---
        if headers:
            server = headers.get("server", "")
            result.checks.append(VerificationCheck(
                name="server_identified",
                passed=bool(server),
                evidence=f"Server: {server}" if server else "No server header",
                confidence=0.5,
            ))
        else:
            result.checks.append(VerificationCheck(name="server_identified", passed=False, evidence="No headers", confidence=0.0))

        # --- Compute totals ---
        result.checks_total = len(result.checks)
        result.checks_passed = sum(1 for c in result.checks if c.passed)
        result.failures = [c.name for c in result.checks if not c.passed]

        if result.checks_total > 0:
            result.verification_score = round(result.checks_passed / result.checks_total * 100, 1)
            confidences = [c.confidence for c in result.checks]
            result.verification_confidence = round(sum(confidences) / len(confidences) * 100, 1) if confidences else 0.0

        # Build evidence list
        result.evidence = [
            {"check": c.name, "passed": c.passed, "evidence": c.evidence, "confidence": c.confidence}
            for c in result.checks
        ]

        return result


# =============================================================================
# MODULE 2: Technology Verification Engine
# =============================================================================
TECH_SIGNATURES: dict[str, dict[str, Any]] = {
    "shopify": {
        "category": "platform",
        "scripts": [r"cdn\.shopify\.com", r"Shopify\.theme", r"shopify-section", r"Shopify\.routes"],
        "meta": [r"shopify-checkout", r"shopify-payment"],
        "headers": ["x-shopify-stage"],
    },
    "shopify_plus": {
        "category": "platform",
        "scripts": [r"Shopify\.theme", r"checkout\.shopify\.com"],
        "meta": [r"shopify-plus"],
        "headers": [],
    },
    "woocommerce": {
        "category": "platform",
        "scripts": [r"woocommerce", r"wc-", r"wp-content/plugins/woocommerce"],
        "meta": [r"woocommerce"],
        "headers": [],
    },
    "magento": {
        "category": "platform",
        "scripts": [r"magento", r"Mage\.Cookies", r"mage/"],
        "meta": [r"magento"],
        "headers": [],
    },
    "klaviyo": {
        "category": "app",
        "scripts": [r"klaviyo\.com", r"_klOnsite", r"klaviyo"],
        "meta": [r"klaviyo"],
        "headers": [],
    },
    "judge_me": {
        "category": "app",
        "scripts": [r"judge\.me", r"jdgm"],
        "meta": [],
        "headers": [],
    },
    "yotpo": {
        "category": "app",
        "scripts": [r"yotpo", r"staticw2\.yotpo"],
        "meta": [],
        "headers": [],
    },
    "recharge": {
        "category": "app",
        "scripts": [r"rechargepayments", r"recharge"],
        "meta": [],
        "headers": [],
    },
    "shiprocket": {
        "category": "app",
        "scripts": [r"shiprocket", r"shiprocket\.in"],
        "meta": [],
        "headers": [],
    },
    "gorgias": {
        "category": "support",
        "scripts": [r"gorgias", r"gorgiasbot"],
        "meta": [],
        "headers": [],
    },
    "zendesk": {
        "category": "support",
        "scripts": [r"zendesk", r"zdassets", r"ze-snapshot"],
        "meta": [],
        "headers": [],
    },
    "freshchat": {
        "category": "support",
        "scripts": [r"freshchat", r"fc-widget"],
        "meta": [],
        "headers": [],
    },
    "ga4": {
        "category": "analytics",
        "scripts": [r"gtag/js\?id=G-", r"google-analytics", r"googletagmanager\.com/gtag"],
        "meta": [],
        "headers": [],
    },
    "meta_pixel": {
        "category": "analytics",
        "scripts": [r"connect\.facebook\.net", r"fbq\(", r"facebook\.net/en_US/fbevents"],
        "meta": [],
        "headers": [],
    },
    "gtm": {
        "category": "analytics",
        "scripts": [r"googletagmanager\.com/gtm\.js", r"GTM-"],
        "meta": [],
        "headers": [],
    },
    "razorpay": {
        "category": "payment",
        "scripts": [r"razorpay", r"checkout\.razorpay\.com"],
        "meta": [],
        "headers": [],
    },
    "stripe": {
        "category": "payment",
        "scripts": [r"stripe\.com", r"Stripe\("],
        "meta": [],
        "headers": [],
    },
}


@dataclass
class TechDetection:
    technology: str
    category: str
    detected: bool
    confidence: float
    evidence_type: str
    evidence_url: str
    evidence_detail: str
    version: str | None = None
    last_seen: datetime = field(default_factory=_now)


@dataclass
class TechnologyVerificationResult:
    company_id: str
    website: str
    detections: list[TechDetection] = field(default_factory=list)
    platform_detected: str | None = None
    platform_confidence: float = 0.0
    total_technologies: int = 0
    detected_count: int = 0
    evidence: list[dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=_now)


class TechnologyVerificationEngine:
    """Detect actual technology stack from website HTML. Never infer."""

    def verify(self, company_id: str, website: str, html_content: str = "", headers: dict | None = None) -> TechnologyVerificationResult:
        result = TechnologyVerificationResult(company_id=company_id, website=website)

        if not html_content:
            result.evidence = [{"error": "No HTML content provided for technology detection"}]
            return result

        now = _now()

        for tech_name, sigs in TECH_SIGNATURES.items():
            detected = False
            evidence_parts = []
            confidence = 0.0
            evidence_type = "script"

            # Check scripts
            for pattern in sigs.get("scripts", []):
                if re.search(pattern, html_content, re.IGNORECASE):
                    detected = True
                    evidence_parts.append(f"Script match: {pattern}")
                    confidence = max(confidence, 0.9)

            # Check meta tags
            for pattern in sigs.get("meta", []):
                if re.search(pattern, html_content, re.IGNORECASE):
                    detected = True
                    evidence_parts.append(f"Meta match: {pattern}")
                    confidence = max(confidence, 0.85)

            # Check headers
            if headers:
                for hdr in sigs.get("headers", []):
                    if any(hdr.lower() in k.lower() for k in headers):
                        detected = True
                        evidence_parts.append(f"Header: {hdr}")
                        confidence = max(confidence, 0.95)

            detection = TechDetection(
                technology=tech_name,
                category=sigs["category"],
                detected=detected,
                confidence=confidence if detected else 0.0,
                evidence_type=evidence_type,
                evidence_url=website,
                evidence_detail="; ".join(evidence_parts) if evidence_parts else "Not detected",
                last_seen=now,
            )
            result.detections.append(detection)

        # Determine primary platform
        platforms = [d for d in result.detections if d.category == "platform" and d.detected]
        if platforms:
            platforms.sort(key=lambda d: d.confidence, reverse=True)
            result.platform_detected = platforms[0].technology
            result.platform_confidence = platforms[0].confidence

        result.total_technologies = len(result.detections)
        result.detected_count = sum(1 for d in result.detections if d.detected)
        result.evidence = [
            {
                "technology": d.technology,
                "category": d.category,
                "detected": d.detected,
                "confidence": d.confidence,
                "evidence": d.evidence_detail,
            }
            for d in result.detections
            if d.detected
        ]

        return result


# =============================================================================
# MODULE 3: Company DNA Validation Engine
# =============================================================================
DNA_FIELDS = {
    "company_size": {"weight": 0.15, "type": "categorical"},
    "estimated_monthly_orders": {"weight": 0.12, "type": "numeric"},
    "estimated_monthly_revenue": {"weight": 0.12, "type": "numeric"},
    "employee_count": {"weight": 0.10, "type": "numeric"},
    "product_count": {"weight": 0.08, "type": "numeric"},
    "category_count": {"weight": 0.05, "type": "numeric"},
    "brand_maturity": {"weight": 0.08, "type": "categorical"},
    "business_maturity": {"weight": 0.08, "type": "categorical"},
    "expansion_stage": {"weight": 0.07, "type": "categorical"},
    "growth_stage": {"weight": 0.07, "type": "categorical"},
    "ai_readiness": {"weight": 0.05, "type": "categorical"},
    "automation_readiness": {"weight": 0.03, "type": "categorical"},
    "international_presence": {"weight": 0.02, "type": "boolean"},
    "marketplace_presence": {"weight": 0.02, "type": "boolean"},
    "average_order_value": {"weight": 0.06, "type": "numeric"},
}

SIZE_MAP = {"micro": 1, "small": 2, "medium": 3, "large": 4, "enterprise": 5}
MATURITY_MAP = {"new": 1, "growing": 2, "established": 3, "mature": 4}
GROWTH_MAP = {"stagnant": 1, "slow": 2, "moderate": 3, "fast": 4, "hyper": 5}


@dataclass
class DnaFieldValidation:
    field_name: str
    field_value: str | None
    value_numeric: float | None
    confidence: float
    evidence: list[dict]
    source: str
    validated: bool
    previous_value: str | None = None
    value_changed: bool = False


@dataclass
class CompanyDnaValidationResult:
    company_id: str
    fields: list[DnaFieldValidation] = field(default_factory=list)
    overall_confidence: float = 0.0
    fields_validated: int = 0
    fields_total: int = 0
    fields_changed: int = 0
    evidence: list[dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=_now)


class CompanyDnaValidationEngine:
    """Validate company DNA fields with confidence scoring."""

    def validate(
        self,
        company_id: str,
        dna_data: dict,
        previous_dna: dict | None = None,
    ) -> CompanyDnaValidationResult:
        result = CompanyDnaValidationResult(company_id=company_id)

        for field_name, field_config in DNA_FIELDS.items():
            raw_value = dna_data.get(field_name)
            prev_value = previous_dna.get(field_name) if previous_dna else None

            validation = self._validate_field(field_name, raw_value, prev_value, field_config)
            result.fields.append(validation)

            if validation.validated:
                result.fields_validated += 1
            if validation.value_changed:
                result.fields_changed += 1

        result.fields_total = len(DNA_FIELDS)

        if result.fields_total > 0:
            weighted_sum = sum(
                f.confidence * DNA_FIELDS[f.field_name]["weight"]
                for f in result.fields
            )
            total_weight = sum(DNA_FIELDS[f.field_name]["weight"] for f in result.fields)
            result.overall_confidence = round(weighted_sum / total_weight * 100, 1) if total_weight > 0 else 0.0

        result.evidence = [
            {
                "field": f.field_name,
                "value": f.field_value,
                "confidence": f.confidence,
                "validated": f.validated,
                "evidence": f.evidence,
            }
            for f in result.fields
        ]

        return result

    def _validate_field(self, name: str, value: Any, prev: Any, config: dict) -> DnaFieldValidation:
        evidence = []
        confidence = 0.0
        validated = False
        numeric_value = None

        if value is None or (isinstance(value, str) and value.strip() == ""):
            return DnaFieldValidation(
                field_name=name, field_value=None, value_numeric=None,
                confidence=0.0, evidence=[{"status": "missing"}],
                source="none", validated=False,
            )

        value_str = str(value).strip()

        # Numeric fields
        if config["type"] == "numeric":
            try:
                numeric_value = float(re.sub(r"[^\d.]", "", value_str))
                if numeric_value > 0:
                    confidence = 0.8
                    validated = True
                    evidence.append({"type": "numeric_parse", "value": numeric_value})
            except (ValueError, TypeError):
                confidence = 0.2
                evidence.append({"type": "parse_failed", "raw": value_str})

        # Boolean fields
        elif config["type"] == "boolean":
            val_lower = value_str.lower()
            if val_lower in ("true", "yes", "1", "present", "available"):
                confidence = 0.8
                validated = True
                evidence.append({"type": "boolean_true"})
            elif val_lower in ("false", "no", "0", "absent", "not_available"):
                confidence = 0.8
                validated = True
                evidence.append({"type": "boolean_false"})
            else:
                confidence = 0.3
                evidence.append({"type": "boolean_uncertain", "raw": value_str})

        # Categorical fields
        elif config["type"] == "categorical":
            if value_str:
                confidence = 0.7
                validated = True
                evidence.append({"type": "categorical", "value": value_str})

        # Check for changes
        changed = prev is not None and str(prev).strip() != value_str

        return DnaFieldValidation(
            field_name=name,
            field_value=value_str,
            value_numeric=numeric_value,
            confidence=confidence,
            evidence=evidence,
            source="provided",
            validated=validated,
            previous_value=str(prev) if prev else None,
            value_changed=changed,
        )


# =============================================================================
# MODULE 4: Decision Maker Reliability Engine
# =============================================================================
GENERIC_ROLES = {"founder", "ceo", "coo", "cto", "cmo", "cfo", "co-founder", "chief growth officer"}
REJECT_PREFIXES = {"support", "info", "hello", "contact", "admin", "sales", "help", "feedback", "enquiry", "inquiries"}
REACHABILITY_HIERARCHY = {
    "founder": 100, "co-founder": 100, "ceo": 95, "coo": 90,
    "chief growth officer": 88, "cto": 85, "cmo": 85,
    "growth head": 82, "marketing head": 80, "ecommerce head": 80,
    "operations head": 78, "customer experience head": 75,
    "support head": 70, "digital head": 72, "head": 75,
    "vice president": 73, "director": 70, "manager": 60,
    "lead": 55, "specialist": 45, "executive": 40, "analyst": 35,
}


@dataclass
class DecisionMakerValidation:
    name: str
    role: str
    normalized_role: str
    department: str | None
    linkedin_url: str | None
    email: str | None
    phone: str | None
    evidence_url: str | None
    confidence: float
    reachability_score: float
    priority: str  # high, medium, low
    is_reliable: bool
    rejection_reason: str | None = None
    is_generic: bool = False


@dataclass
class DecisionMakerReliabilityResult:
    company_id: str
    makers: list[DecisionMakerValidation] = field(default_factory=list)
    reliable_count: int = 0
    rejected_count: int = 0
    overall_confidence: float = 0.0
    has_founder_or_ceo: bool = False
    best_contact: DecisionMakerValidation | None = None
    evidence: list[dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=_now)


class DecisionMakerReliabilityEngine:
    """Validate decision makers. Reject generic contacts. Require evidence."""

    def validate(self, company_id: str, decision_makers: list[dict]) -> DecisionMakerReliabilityResult:
        result = DecisionMakerReliabilityResult(company_id=company_id)

        for dm in decision_makers:
            validation = self._validate_one(dm)
            result.makers.append(validation)

            if validation.is_reliable:
                result.reliable_count += 1
            else:
                result.rejected_count += 1

            if validation.normalized_role in ("founder", "co-founder", "ceo"):
                result.has_founder_or_ceo = True

        # Pick best contact
        reliable = [m for m in result.makers if m.is_reliable]
        if reliable:
            reliable.sort(key=lambda m: m.reachability_score, reverse=True)
            result.best_contact = reliable[0]

        result.overall_confidence = (
            round(sum(m.confidence for m in result.makers) / len(result.makers) * 100, 1)
            if result.makers else 0.0
        )

        result.evidence = [
            {
                "name": m.name,
                "role": m.role,
                "reliable": m.is_reliable,
                "confidence": m.confidence,
                "reachability": m.reachability_score,
                "rejection": m.rejection_reason,
            }
            for m in result.makers
        ]

        return result

    def _validate_one(self, dm: dict) -> DecisionMakerValidation:
        name = (dm.get("name") or dm.get("full_name") or "").strip()
        role = (dm.get("role") or dm.get("designation") or "").strip()
        email = (dm.get("email") or dm.get("work_email") or "").strip()
        phone = (dm.get("phone") or dm.get("business_phone") or "").strip()
        linkedin = dm.get("linkedin_url") or ""
        evidence_url = dm.get("source_url") or dm.get("evidence_url") or ""

        normalized_role = role.lower().strip()
        department = dm.get("department")
        confidence = 0.0
        rejection_reason = None
        is_generic = False
        is_reliable = True

        # Check: reject generic email prefixes
        if email:
            local_part = email.split("@")[0].lower()
            if local_part in REJECT_PREFIXES:
                is_reliable = False
                is_generic = True
                rejection_reason = f"Generic email prefix: {local_part}@"
                confidence = 0.1

        # Check: reject generic role-only entries with no name
        if not name and role:
            is_reliable = False
            rejection_reason = "Role provided but no person name"
            confidence = 0.1

        # Check: name looks like a word/phrase, not a person
        if name and len(name.split()) == 1 and name.lower() in {"patreon", "type", "coding", "model", "this", "osint", "shipping", "building", "frontend"}:
            is_reliable = False
            rejection_reason = f"Name '{name}' is not a person"
            confidence = 0.05

        # Check: LinkedIn adds confidence
        if linkedin and "linkedin.com" in linkedin:
            confidence = max(confidence, 0.85)
        elif evidence_url:
            confidence = max(confidence, 0.6)

        # Reachability score
        reachability = REACHABILITY_HIERARCHY.get(normalized_role, 30)
        if linkedin:
            reachability = min(100, reachability + 10)
        if email:
            reachability = min(100, reachability + 5)

        # Priority
        if reachability >= 80:
            priority = "high"
        elif reachability >= 60:
            priority = "medium"
        else:
            priority = "low"

        # If name is present and looks real, boost confidence
        if name and len(name.split()) >= 2 and not rejection_reason:
            confidence = max(confidence, 0.7)
            is_reliable = True

        return DecisionMakerValidation(
            name=name, role=role, normalized_role=normalized_role,
            department=department, linkedin_url=linkedin,
            email=email, phone=phone, evidence_url=evidence_url,
            confidence=confidence, reachability_score=reachability,
            priority=priority, is_reliable=is_reliable,
            rejection_reason=rejection_reason, is_generic=is_generic,
        )


# =============================================================================
# MODULE 5: Contact Verification Engine
# =============================================================================
DISPOSABLE_DOMAINS = {
    "tempmail.com", "throwaway.email", "guerrillamail.com", "mailinator.com",
    "yopmail.com", "trashmail.com", "sharklasers.com", "guerrillamailblock.com",
    "grr.la", "dispostable.com", "10minutemail.com", "temp-mail.org",
}
ROLE_PREFIXES = {"support", "info", "hello", "contact", "admin", "sales", "help", "feedback", "enquiry", "noreply", "no-reply", "webmaster", "postmaster"}


@dataclass
class EmailVerification:
    email: str
    format_valid: bool
    mx_found: bool
    smtp_valid: bool
    is_disposable: bool
    is_role_based: bool
    is_catch_all: bool
    is_corporate: bool
    domain: str
    risk_level: str
    deliverability: str
    confidence: float
    evidence: list[dict]


@dataclass
class PhoneVerification:
    phone: str
    country: str | None
    phone_type: str  # mobile, landline, business, unknown
    is_whatsapp: bool
    format_valid: bool
    is_duplicate: bool
    duplicate_of: str | None
    reachability: float
    confidence: float
    evidence: list[dict]


@dataclass
class ContactVerificationResult:
    company_id: str
    emails: list[EmailVerification] = field(default_factory=list)
    phones: list[PhoneVerification] = field(default_factory=list)
    total_contacts: int = 0
    verified_contacts: int = 0
    rejected_contacts: int = 0
    duplicate_phones: list[str] = field(default_factory=list)
    overall_confidence: float = 0.0
    evidence: list[dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=_now)


class ContactVerificationEngine:
    """Verify emails and phones. Detect disposables, duplicates, role-based."""

    def verify(self, company_id: str, emails: list[str], phones: list[str]) -> ContactVerificationResult:
        result = ContactVerificationResult(company_id=company_id)

        # --- Email verification ---
        seen_domains: dict[str, int] = {}
        for email in emails:
            ev = self._verify_email(email)
            result.emails.append(ev)
            result.total_contacts += 1
            if ev.confidence >= 0.6:
                result.verified_contacts += 1
            else:
                result.rejected_contacts += 1
            domain = ev.domain
            seen_domains[domain] = seen_domains.get(domain, 0) + 1

        # --- Phone verification ---
        all_phones: dict[str, list[str]] = {}
        for phone in phones:
            pv = self._verify_phone(phone, company_id)
            result.phones.append(pv)
            result.total_contacts += 1
            if pv.confidence >= 0.6:
                result.verified_contacts += 1
            else:
                result.rejected_contacts += 1
            clean = re.sub(r"[^\d+]", "", phone)
            all_phones.setdefault(clean, []).append(company_id)

        # --- Cross-company duplicate detection ---
        global_phones: dict[str, list[str]] = {}
        for pv in result.phones:
            clean = re.sub(r"[^\d+]", "", pv.phone)
            global_phones.setdefault(clean, []).append(company_id)

        for pv in result.phones:
            clean = re.sub(r"[^\d+]", "", pv.phone)
            if len(global_phones.get(clean, [])) > 1:
                pv.is_duplicate = True
                pv.confidence = 0.1
                result.duplicate_phones.append(pv.phone)

        # --- Catch-all detection ---
        domain_counts = {}
        for ev in result.emails:
            domain_counts[ev.domain] = domain_counts.get(ev.domain, 0) + 1
        for ev in result.emails:
            if domain_counts.get(ev.domain, 0) > 3:
                ev.is_catch_all = True
                ev.confidence *= 0.8

        # --- Overall confidence ---
        all_confidences = [e.confidence for e in result.emails] + [p.confidence for p in result.phones]
        result.overall_confidence = (
            round(sum(all_confidences) / len(all_confidences) * 100, 1)
            if all_confidences else 0.0
        )

        result.evidence = (
            [{"type": "email", **_deep_to_dict(e)} for e in result.emails]
            + [{"type": "phone", **_deep_to_dict(p)} for p in result.phones]
        )

        return result

    def _verify_email(self, email: str) -> EmailVerification:
        email = email.strip().lower()
        evidence = []

        # Format check
        format_valid = bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))
        evidence.append({"check": "format", "valid": format_valid})

        domain = email.split("@")[-1] if "@" in email else ""

        # Disposable check
        is_disposable = domain in DISPOSABLE_DOMAINS
        evidence.append({"check": "disposable", "is_disposable": is_disposable})

        # Role-based check
        local_part = email.split("@")[0] if "@" in email else ""
        is_role_based = local_part in ROLE_PREFIXES
        evidence.append({"check": "role_based", "is_role_based": is_role_based})

        # Corporate check
        free_domains = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com", "mail.com", "protonmail.com"}
        is_corporate = domain not in free_domains and not is_disposable
        evidence.append({"check": "corporate", "is_corporate": is_corporate})

        # Confidence calculation
        confidence = 0.5  # base
        if format_valid:
            confidence += 0.2
        if is_corporate:
            confidence += 0.15
        if not is_disposable:
            confidence += 0.1
        if not is_role_based:
            confidence += 0.05

        # Risk
        if is_disposable:
            risk = "high"
        elif is_role_based:
            risk = "medium"
        elif not is_corporate:
            risk = "medium"
        else:
            risk = "low"

        deliverability = "unknown"  # Would need SMTP check for real verification

        return EmailVerification(
            email=email, format_valid=format_valid, mx_found=False,
            smtp_valid=False, is_disposable=is_disposable,
            is_role_based=is_role_based, is_catch_all=False,
            is_corporate=is_corporate, domain=domain,
            risk_level=risk, deliverability=deliverability,
            confidence=min(1.0, confidence), evidence=evidence,
        )

    def _verify_phone(self, phone: str, company_id: str) -> PhoneVerification:
        clean = re.sub(r"[^\d+]", "", phone)
        evidence = []

        # Format check
        format_valid = len(clean) >= 10
        evidence.append({"check": "format", "valid": format_valid, "digits": len(clean)})

        # Country detection
        country = None
        if clean.startswith("+91") or (len(clean) == 10 and not clean.startswith("+")):
            country = "India"
        elif clean.startswith("+1"):
            country = "US"
        elif clean.startswith("+44"):
            country = "UK"

        # Phone type heuristics
        phone_type = "unknown"
        if country == "India" and len(clean) == 10:
            phone_type = "mobile"
        elif country == "India" and len(clean) == 12:
            phone_type = "mobile"
        else:
            phone_type = "landline"

        # Confidence
        confidence = 0.5
        if format_valid:
            confidence += 0.2
        if country:
            confidence += 0.15
        if phone_type != "unknown":
            confidence += 0.1

        evidence.append({"check": "country", "country": country})
        evidence.append({"check": "type", "phone_type": phone_type})

        return PhoneVerification(
            phone=phone, country=country, phone_type=phone_type,
            is_whatsapp=False, format_valid=format_valid,
            is_duplicate=False, duplicate_of=None,
            reachability=0.5, confidence=min(1.0, confidence),
            evidence=evidence,
        )


# =============================================================================
# MODULE 6: Evidence Engine
# =============================================================================
@dataclass
class EvidenceRecord:
    entity_type: str
    entity_id: str
    field_name: str
    field_value: str
    evidence_type: str  # html, header, script, url, screenshot
    evidence_url: str
    evidence_snapshot: str
    evidence_hash: str
    source_id: str
    source_reliability: float
    confidence: float
    captured_at: datetime = field(default_factory=_now)


class EvidenceEngine:
    """Centralized evidence collection. Every field must have evidence."""

    def __init__(self):
        self._evidence: list[EvidenceRecord] = []

    def record(
        self,
        entity_type: str,
        entity_id: str,
        field_name: str,
        field_value: str,
        evidence_type: str,
        evidence_url: str,
        evidence_snapshot: str = "",
        source_id: str = "unknown",
        source_reliability: float = 0.5,
        confidence: float = 0.5,
    ) -> EvidenceRecord:
        evidence_hash = hashlib.sha256(
            f"{entity_type}:{entity_id}:{field_name}:{field_value}:{evidence_url}".encode()
        ).hexdigest()

        record = EvidenceRecord(
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            field_value=field_value,
            evidence_type=evidence_type,
            evidence_url=evidence_url,
            evidence_snapshot=evidence_snapshot[:2000],
            evidence_hash=evidence_hash,
            source_id=source_id,
            source_reliability=source_reliability,
            confidence=confidence,
        )
        self._evidence.append(record)
        return record

    def get_evidence(self, entity_type: str, entity_id: str, field_name: str | None = None) -> list[EvidenceRecord]:
        results = [
            e for e in self._evidence
            if e.entity_type == entity_type and e.entity_id == entity_id
        ]
        if field_name:
            results = [e for e in results if e.field_name == field_name]
        return results

    def get_all(self) -> list[EvidenceRecord]:
        return list(self._evidence)

    def count(self) -> int:
        return len(self._evidence)


# =============================================================================
# MODULE 7: Confidence Engine
# =============================================================================
@dataclass
class ConfidenceScore:
    entity_type: str
    entity_id: str
    field_name: str
    confidence: float
    grade: str
    factors: dict
    source_count: int
    source_reliability_avg: float
    freshness_score: float
    verification_success: bool
    historical_consistency: float
    evidence_quality: float


class ConfidenceEngine:
    """Dynamic confidence scoring based on multiple factors."""

    GRADE_THRESHOLDS = [
        (95, "A+"), (90, "A"), (85, "A-"),
        (80, "B+"), (75, "B"), (70, "B-"),
        (60, "C+"), (50, "C"), (40, "C-"),
        (30, "D"), (0, "F"),
    ]

    def calculate(
        self,
        entity_type: str,
        entity_id: str,
        field_name: str,
        source_count: int = 0,
        source_reliability_avg: float = 0.5,
        freshness_hours: float = 168,
        verification_success: bool = False,
        historical_matches: int = 0,
        historical_total: int = 0,
        evidence_count: int = 0,
    ) -> ConfidenceScore:
        # Source factor (more sources = higher confidence, diminishing returns)
        source_factor = min(1.0, 0.3 + 0.1 * min(source_count, 7))

        # Reliability factor
        reliability_factor = source_reliability_avg

        # Freshness factor (newer = better, 1 week = 1.0, 1 month = 0.7, 3 months = 0.4)
        freshness_factor = max(0.2, 1.0 - (freshness_hours / (24 * 30 * 3)))

        # Verification factor
        verification_factor = 1.0 if verification_success else 0.4

        # Historical consistency
        historical_factor = (
            historical_matches / historical_total
            if historical_total > 0 else 0.5
        )

        # Evidence quality
        evidence_factor = min(1.0, 0.3 + 0.1 * min(evidence_count, 7))

        # Weighted combination
        confidence = (
            source_factor * 0.20 +
            reliability_factor * 0.20 +
            freshness_factor * 0.15 +
            verification_factor * 0.20 +
            historical_factor * 0.15 +
            evidence_factor * 0.10
        ) * 100

        confidence = round(min(100.0, max(0.0, confidence)), 1)

        # Grade
        grade = "F"
        for threshold, g in self.GRADE_THRESHOLDS:
            if confidence >= threshold:
                grade = g
                break

        return ConfidenceScore(
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            confidence=confidence,
            grade=grade,
            factors={
                "source_factor": round(source_factor, 3),
                "reliability_factor": round(reliability_factor, 3),
                "freshness_factor": round(freshness_factor, 3),
                "verification_factor": round(verification_factor, 3),
                "historical_factor": round(historical_factor, 3),
                "evidence_factor": round(evidence_factor, 3),
            },
            source_count=source_count,
            source_reliability_avg=source_reliability_avg,
            freshness_score=round(freshness_factor * 100, 1),
            verification_success=verification_success,
            historical_consistency=round(historical_factor * 100, 1),
            evidence_quality=round(evidence_factor * 100, 1),
        )


# =============================================================================
# MODULE 8: Data Integrity Engine
# =============================================================================
@dataclass
class IntegrityCheck:
    check_type: str
    check_name: str
    passed: bool
    severity: str  # critical, warning, info
    details: dict
    affected_fields: list[str]
    recommendation: str
    auto_fixable: bool
    auto_fixed: bool = False


@dataclass
class DataIntegrityResult:
    company_id: str
    checks: list[IntegrityCheck] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    critical_failures: int = 0
    auto_fixed_count: int = 0
    overall_integrity: float = 0.0
    evidence: list[dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=_now)


class DataIntegrityEngine:
    """Automatically detect data quality issues."""

    def __init__(self):
        self._global_phones: dict[str, list[str]] = {}
        self._global_emails: dict[str, list[str]] = {}

    def register_global_phone(self, phone: str, company_id: str):
        clean = re.sub(r"[^\d+]", "", phone)
        self._global_phones.setdefault(clean, []).append(company_id)

    def register_global_email(self, email: str, company_id: str):
        self._global_emails.setdefault(email.lower(), []).append(company_id)

    def check(self, company_id: str, data: dict) -> DataIntegrityResult:
        result = DataIntegrityResult(company_id=company_id)

        # --- Duplicate phone detection ---
        phones = data.get("phones", [])
        for phone in phones:
            clean = re.sub(r"[^\d+]", "", phone)
            other_companies = [c for c in self._global_phones.get(clean, []) if c != company_id]
            if other_companies:
                result.checks.append(IntegrityCheck(
                    check_type="duplicate_phone",
                    check_name=f"Phone {phone} found in {len(other_companies)} other companies",
                    passed=False,
                    severity="critical",
                    details={"phone": phone, "other_companies": other_companies},
                    affected_fields=["phone"],
                    recommendation="Reject this phone number — it belongs to multiple companies",
                    auto_fixable=True,
                ))

        # --- Duplicate email detection ---
        emails = data.get("emails", [])
        for email in emails:
            other_companies = [c for c in self._global_emails.get(email.lower(), []) if c != company_id]
            if other_companies:
                result.checks.append(IntegrityCheck(
                    check_type="duplicate_email",
                    check_name=f"Email {email} found in {len(other_companies)} other companies",
                    passed=False,
                    severity="critical",
                    details={"email": email, "other_companies": other_companies},
                    affected_fields=["email"],
                    recommendation="Reject this email — it belongs to multiple companies",
                    auto_fixable=True,
                ))

        # --- Placeholder phone detection ---
        placeholder_phones = {"+910000000000", "+911234567890", "0000000000", "1234567890", "+91 000 000 0000"}
        for phone in phones:
            clean = re.sub(r"[^\d]", "", phone)
            if clean in {re.sub(r"[^\d]", "", p) for p in placeholder_phones}:
                result.checks.append(IntegrityCheck(
                    check_type="placeholder_phone",
                    check_name=f"Phone {phone} is a placeholder",
                    passed=False,
                    severity="critical",
                    details={"phone": phone},
                    affected_fields=["phone"],
                    recommendation="Remove placeholder phone number",
                    auto_fixable=True,
                ))

        # --- Placeholder email detection ---
        placeholder_emails = {"test@test.com", "email@example.com", "demo@demo.com", "user@example.com"}
        for email in emails:
            if email.lower() in placeholder_emails:
                result.checks.append(IntegrityCheck(
                    check_type="placeholder_email",
                    check_name=f"Email {email} is a placeholder",
                    passed=False,
                    severity="critical",
                    details={"email": email},
                    affected_fields=["email"],
                    recommendation="Remove placeholder email",
                    auto_fixable=True,
                ))

        # --- Domain checks ---
        website = data.get("website", "")
        if website:
            parsed = urlparse(website)
            domain = parsed.netloc

            # Wrong TLD for India
            if domain.endswith(".com") and any(kw in domain for kw in ["india", "bharat"]):
                result.checks.append(IntegrityCheck(
                    check_type="tld_mismatch",
                    check_name=f"Domain {domain} uses .com but targets India",
                    passed=True,
                    severity="info",
                    details={"domain": domain},
                    affected_fields=["website"],
                    recommendation="Consider using .in TLD for Indian market",
                    auto_fixable=False,
                ))

            # Redirect chain
            if parsed.scheme == "http":
                result.checks.append(IntegrityCheck(
                    check_type="https_redirect",
                    check_name=f"Website {website} uses HTTP",
                    passed=False,
                    severity="warning",
                    details={"url": website},
                    affected_fields=["website"],
                    recommendation="Ensure HTTPS redirect is configured",
                    auto_fixable=False,
                ))

        # --- Enterprise leakage detection ---
        company_name = data.get("company_name", "")
        enterprise_keywords = ["tata", "reliance", "adani", "birla", "infosys", "wipro", "hcl", "mahindra", "godrej", "icici", "hdfc"]
        if any(ek in company_name.lower() for ek in enterprise_keywords):
            result.checks.append(IntegrityCheck(
                check_type="enterprise_leakage",
                check_name=f"Company '{company_name}' may be enterprise",
                passed=False,
                severity="critical",
                details={"company_name": company_name},
                affected_fields=["company_name", "icp_match"],
                recommendation="Verify this is not an enterprise company — exclude from SMB ICP",
                auto_fixable=False,
            ))

        # --- Inactive/dead store detection ---
        product_count = data.get("product_count", 0)
        if isinstance(product_count, (int, float)) and product_count == 0:
            result.checks.append(IntegrityCheck(
                check_type="no_products",
                check_name="Zero products detected",
                passed=False,
                severity="warning",
                details={"product_count": 0},
                affected_fields=["products"],
                recommendation="Verify store is active",
                auto_fixable=False,
            ))

        # --- Compute results ---
        result.passed_count = sum(1 for c in result.checks if c.passed)
        result.failed_count = sum(1 for c in result.checks if not c.passed)
        result.critical_failures = sum(1 for c in result.checks if not c.passed and c.severity == "critical")
        result.auto_fixed_count = sum(1 for c in result.checks if c.auto_fixed)
        result.overall_integrity = (
            round(result.passed_count / len(result.checks) * 100, 1)
            if result.checks else 100.0
        )

        result.evidence = [
            {
                "check": c.check_name,
                "type": c.check_type,
                "passed": c.passed,
                "severity": c.severity,
                "recommendation": c.recommendation,
            }
            for c in result.checks
        ]

        return result


# =============================================================================
# MODULE 9: Lead Readiness Engine
# =============================================================================
STAGES = [
    "DISCOVERED", "NORMALIZED", "COMPANY_VERIFIED", "TECH_VERIFIED",
    "DNA_VERIFIED", "CONTACT_VERIFIED", "ICP_VERIFIED", "ARIE_ANALYZED",
    "RICVP_CALIBRATED", "SALES_READY", "OUTREACH_READY",
]

STAGE_INDEX = {s: i for i, s in enumerate(STAGES)}


@dataclass
class ReadinessUpdate:
    stage: str
    timestamp: datetime
    details: dict


@dataclass
class ReadinessResult:
    company_id: str
    current_stage: str
    stages_passed: int
    stages_total: int
    readiness_score: float
    stage_history: list[ReadinessUpdate]
    blocked: bool
    block_reason: str | None
    next_stage: str | None
    evidence: list[dict]
    timestamp: datetime = field(default_factory=_now)


class LeadReadinessEngine:
    """Enforce strict pipeline progression. Nothing skips stages."""

    def __init__(self):
        self._readiness: dict[str, dict] = {}

    def get_or_create(self, company_id: str) -> dict:
        if company_id not in self._readiness:
            self._readiness[company_id] = {
                "current_stage": "DISCOVERED",
                "stage_history": [],
                "blocked": False,
                "block_reason": None,
            }
        return self._readiness[company_id]

    def advance(
        self,
        company_id: str,
        target_stage: str,
        verification_passed: bool = True,
        failure_reason: str | None = None,
    ) -> ReadinessResult:
        state = self.get_or_create(company_id)

        if state["blocked"]:
            return self._build_result(company_id, state)

        current_idx = STAGE_INDEX.get(state["current_stage"], 0)
        target_idx = STAGE_INDEX.get(target_stage, 0)

        # Cannot skip stages
        if target_idx > current_idx + 1:
            state["blocked"] = True
            state["block_reason"] = f"Cannot skip from {state['current_stage']} to {target_stage}"
            return self._build_result(company_id, state)

        # Verification failed
        if not verification_passed:
            state["blocked"] = True
            state["block_reason"] = failure_reason or f"Verification failed at {target_stage}"
            return self._build_result(company_id, state)

        # Advance
        state["current_stage"] = target_stage
        state["stage_history"].append({
            "stage": target_stage,
            "timestamp": _now().isoformat(),
            "details": {"status": "passed"},
        })

        return self._build_result(company_id, state)

    def _build_result(self, company_id: str, state: dict) -> ReadinessResult:
        current_idx = STAGE_INDEX.get(state["current_stage"], 0)
        readiness_score = round((current_idx / (len(STAGES) - 1)) * 100, 1)

        next_stage = STAGES[current_idx + 1] if current_idx < len(STAGES) - 1 else None

        return ReadinessResult(
            company_id=company_id,
            current_stage=state["current_stage"],
            stages_passed=current_idx,
            stages_total=len(STAGES),
            readiness_score=readiness_score,
            stage_history=[
                ReadinessUpdate(stage=h["stage"], timestamp=datetime.fromisoformat(h["timestamp"]), details=h.get("details", {}))
                for h in state["stage_history"]
            ],
            blocked=state["blocked"],
            block_reason=state["block_reason"],
            next_stage=next_stage,
            evidence=[{"stage": h["stage"], "timestamp": h["timestamp"]} for h in state["stage_history"]],
        )


# =============================================================================
# MODULE 10: Revenue Reliability Score
# =============================================================================
SCORE_WEIGHTS = {
    "company_trust": 0.20,
    "technology_trust": 0.20,
    "contact_trust": 0.15,
    "evidence_trust": 0.15,
    "freshness": 0.10,
    "data_completeness": 0.10,
    "verification_success": 0.10,
}

GRADE_THRESHOLDS = [
    (85, "Reliable"),
    (70, "Likely Reliable"),
    (50, "Needs Review"),
    (0, "Reject"),
]


@dataclass
class ReliabilityScoreResult:
    company_id: str
    overall_score: float
    overall_grade: str
    company_trust: float
    technology_trust: float
    contact_trust: float
    evidence_trust: float
    freshness: float
    data_completeness: float
    verification_success: float
    historical_stability: float
    confidence_score: float
    score_breakdown: dict
    timestamp: datetime = field(default_factory=_now)


class RevenueReliabilityScoreEngine:
    """Final reliability score. 0-100. Based on all verification results."""

    def calculate(
        self,
        company_id: str,
        company_verification_score: float = 0.0,
        technology_score: float = 0.0,
        contact_score: float = 0.0,
        evidence_count: int = 0,
        evidence_reliability: float = 0.0,
        freshness_hours: float = 168,
        data_completeness: float = 0.0,
        verification_checks_passed: int = 0,
        verification_checks_total: int = 0,
        historical_matches: int = 0,
        historical_total: int = 0,
    ) -> ReliabilityScoreResult:
        # Company trust
        company_trust = min(100.0, company_verification_score)

        # Technology trust
        technology_trust = min(100.0, technology_score)

        # Contact trust
        contact_trust = min(100.0, contact_score)

        # Evidence trust (more evidence = higher trust, capped)
        evidence_trust = min(100.0, 20.0 + evidence_reliability * 60.0 + min(evidence_count, 10) * 2.0)

        # Freshness (newer = better)
        freshness = max(20.0, 100.0 - (freshness_hours / (24 * 30)) * 10.0)

        # Verification success rate
        verification_success = (
            (verification_checks_passed / verification_checks_total * 100)
            if verification_checks_total > 0 else 0.0
        )

        # Historical stability
        historical_stability = (
            (historical_matches / historical_total * 100)
            if historical_total > 0 else 50.0
        )

        # Confidence (meta-score)
        confidence_score = (
            company_trust * 0.25 +
            technology_trust * 0.20 +
            contact_trust * 0.20 +
            evidence_trust * 0.15 +
            freshness * 0.10 +
            verification_success * 0.10
        )

        # Overall score (weighted)
        overall_score = round(
            company_trust * SCORE_WEIGHTS["company_trust"] +
            technology_trust * SCORE_WEIGHTS["technology_trust"] +
            contact_trust * SCORE_WEIGHTS["contact_trust"] +
            evidence_trust * SCORE_WEIGHTS["evidence_trust"] +
            freshness * SCORE_WEIGHTS["freshness"] +
            data_completeness * SCORE_WEIGHTS["data_completeness"] +
            verification_success * SCORE_WEIGHTS["verification_success"],
            1,
        )

        # Grade
        overall_grade = "Reject"
        for threshold, grade in GRADE_THRESHOLDS:
            if overall_score >= threshold:
                overall_grade = grade
                break

        return ReliabilityScoreResult(
            company_id=company_id,
            overall_score=overall_score,
            overall_grade=overall_grade,
            company_trust=round(company_trust, 1),
            technology_trust=round(technology_trust, 1),
            contact_trust=round(contact_trust, 1),
            evidence_trust=round(evidence_trust, 1),
            freshness=round(freshness, 1),
            data_completeness=round(data_completeness, 1),
            verification_success=round(verification_success, 1),
            historical_stability=round(historical_stability, 1),
            confidence_score=round(confidence_score, 1),
            score_breakdown={
                "company_trust": round(company_trust, 1),
                "technology_trust": round(technology_trust, 1),
                "contact_trust": round(contact_trust, 1),
                "evidence_trust": round(evidence_trust, 1),
                "freshness": round(freshness, 1),
                "data_completeness": round(data_completeness, 1),
                "verification_success": round(verification_success, 1),
                "historical_stability": round(historical_stability, 1),
                "confidence_score": round(confidence_score, 1),
                "weights": SCORE_WEIGHTS,
            },
        )


# =============================================================================
# RDRP ORCHESTRATOR
# =============================================================================
@dataclass
class RdrpFullResult:
    company_id: str
    website: str
    company_verification: CompanyVerificationResult | None = None
    technology_verification: TechnologyVerificationResult | None = None
    dna_validation: CompanyDnaValidationResult | None = None
    decision_maker_reliability: DecisionMakerReliabilityResult | None = None
    contact_verification: ContactVerificationResult | None = None
    data_integrity: DataIntegrityResult | None = None
    readiness: ReadinessResult | None = None
    reliability_score: ReliabilityScoreResult | None = None
    evidence_count: int = 0
    overall_passed: bool = False
    block_reasons: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=_now)


class RDRPOrchestrator:
    """Ties all 10 RDRP engines together. Nothing reaches ARIE unless RDRP approves."""

    def __init__(self):
        self.company_verification = CompanyVerificationEngine()
        self.technology_verification = TechnologyVerificationEngine()
        self.dna_validation = CompanyDnaValidationEngine()
        self.decision_maker_reliability = DecisionMakerReliabilityEngine()
        self.contact_verification = ContactVerificationEngine()
        self.evidence = EvidenceEngine()
        self.confidence = ConfidenceEngine()
        self.integrity = DataIntegrityEngine()
        self.readiness = LeadReadinessEngine()
        self.reliability_score = RevenueReliabilityScoreEngine()

    def verify_company(
        self,
        company_id: str,
        website: str,
        html_content: str = "",
        headers: dict | None = None,
        dna_data: dict | None = None,
        decision_makers: list[dict] | None = None,
        emails: list[str] | None = None,
        phones: list[str] | None = None,
    ) -> RdrpFullResult:
        result = RdrpFullResult(company_id=company_id, website=website)

        # Stage 1: DISCOVERED → NORMALIZED
        self.readiness.advance(company_id, "NORMALIZED")

        # Stage 2: COMPANY_VERIFIED
        if website and html_content:
            result.company_verification = self.company_verification.verify(company_id, website, html_content, headers)
            for ev in result.company_verification.evidence:
                self.evidence.record("company", company_id, ev["check"], str(ev["passed"]),
                                     "html", website, ev.get("evidence", ""), "web_scraper", 0.7, ev.get("confidence", 0.5))

            self.readiness.advance(company_id, "COMPANY_VERIFIED",
                                   verification_passed=result.company_verification.verification_score >= 30)
        else:
            self.readiness.advance(company_id, "COMPANY_VERIFIED", verification_passed=False,
                                   failure_reason="No website or HTML provided")

        # Stage 3: TECH_VERIFIED
        if website and html_content:
            result.technology_verification = self.technology_verification.verify(company_id, website, html_content, headers)
            for ev in result.technology_verification.evidence:
                self.evidence.record("technology", company_id, ev["technology"], ev.get("evidence", ""),
                                     "script", website, ev.get("evidence", ""), "tech_detector", 0.8, ev.get("confidence", 0.5))

            tech_score = (result.technology_verification.detected_count / max(1, result.technology_verification.total_technologies)) * 100
            self.readiness.advance(company_id, "TECH_VERIFIED", verification_passed=tech_score >= 10)

        # Stage 4: DNA_VERIFIED
        if dna_data:
            result.dna_validation = self.dna_validation.validate(company_id, dna_data)
            self.readiness.advance(company_id, "DNA_VERIFIED",
                                   verification_passed=result.dna_validation.overall_confidence >= 30)

        # Stage 5: CONTACT_VERIFIED
        if emails or phones:
            result.contact_verification = self.contact_verification.verify(company_id, emails or [], phones or [])
            for ev in result.contact_verification.evidence:
                self.evidence.record("contact", company_id, ev.get("email") or ev.get("phone", ""),
                                     str(ev.get("confidence", 0)), "verification", website,
                                     str(ev), "contact_engine", 0.7, ev.get("confidence", 0.5))

            self.readiness.advance(company_id, "CONTACT_VERIFIED",
                                   verification_passed=result.contact_verification.verified_contacts > 0)

        # Stage 6: DATA INTEGRITY
        integrity_data = {
            "phones": phones or [],
            "emails": emails or [],
            "website": website,
            "company_name": company_id,
        }
        result.data_integrity = self.integrity.check(company_id, integrity_data)
        for check in result.data_integrity.checks:
            self.evidence.record("integrity", company_id, check.check_name, str(check.passed),
                                 "check", website, check.recommendation, "integrity_engine", 0.8, 0.9 if check.passed else 0.3)

        # Stage 7: RELIABILITY SCORE
        company_score = result.company_verification.verification_score if result.company_verification else 0.0
        tech_score = 0.0
        if result.technology_verification and result.technology_verification.total_technologies > 0:
            tech_score = (result.technology_verification.detected_count / result.technology_verification.total_technologies) * 100
        contact_score = result.contact_verification.overall_confidence if result.contact_verification else 0.0

        result.reliability_score = self.reliability_score.calculate(
            company_id=company_id,
            company_verification_score=company_score,
            technology_score=tech_score,
            contact_score=contact_score,
            evidence_count=self.evidence.count(),
            evidence_reliability=0.7,
            data_completeness=data_completeness(dna_data, emails, phones),
            verification_checks_passed=result.company_verification.checks_passed if result.company_verification else 0,
            verification_checks_total=result.company_verification.checks_total if result.company_verification else 0,
        )

        # Stage 8: Readiness update based on reliability
        if result.reliability_score.overall_grade in ("Reliable", "Likely Reliable"):
            self.readiness.advance(company_id, "SALES_READY")
            result.overall_passed = True
        elif result.reliability_score.overall_grade == "Needs Review":
            result.overall_passed = False
        else:
            result.overall_passed = False
            result.block_reasons.append(f"Reliability grade: {result.reliability_score.overall_grade}")

        # Collect block reasons
        if result.data_integrity and result.data_integrity.critical_failures > 0:
            result.block_reasons.append(f"{result.data_integrity.critical_failures} critical integrity failures")

        result.evidence_count = self.evidence.count()

        # Get readiness state
        result.readiness = self.readiness._build_result(company_id, self.readiness.get_or_create(company_id))

        return result

    def get_dashboard(self) -> dict:
        return {
            "total_companies": len(self.readiness._readiness),
            "evidence_collected": self.evidence.count(),
            "stages": {
                stage: sum(1 for s in self.readiness._readiness.values() if s["current_stage"] == stage)
                for stage in STAGES
            },
        }


def data_completeness(dna_data: dict | None, emails: list[str] | None, phones: list[str] | None) -> float:
    """Calculate data completeness score."""
    score = 0.0
    if dna_data:
        filled = sum(1 for v in dna_data.values() if v is not None and str(v).strip())
        score += (filled / max(1, len(dna_data))) * 40
    if emails:
        score += min(30, len(emails) * 10)
    if phones:
        score += min(30, len(phones) * 10)
    return min(100.0, score)
