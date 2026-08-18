"""COMAI B2B Partner Discovery Engine - Scoring System.

This module implements the scoring system for partner qualification.
Includes client_access_score, comai_partner_fit, and partner tier classification.

COMAI B2B IS NOT AN AGENCY DIRECTORY.
WE ARE BUILDING A PARTNER ACQUISITION ENGINE.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.models.partner import (
    PartnerRecord,
    PartnerTier,
    FinalVerdict,
    ScoringResult,
)


# ============================================================
# CLIENT ACCESS SCORING SIGNALS
# ============================================================
# CLIENT ACCESS > PARTNER PROGRAM EXISTENCE
# DISTRIBUTION POTENTIAL > GENERIC COMPANY SIZE
# NON-COMPETITOR IS A HARD REQUIREMENT
# QUALITY > QUANTITY

CLIENT_ACCESS_SIGNALS: dict[str, dict[str, Any]] = {
    # ──── CLIENT COUNT SIGNALS (HIGHEST PRIORITY) ────
    "twenty_plus_identifiable_business_clients": {
        "points": 30,
        "evidence_required": "portfolio, case studies, client logos",
        "patterns": [
            r"(?:our|we)\s+(?:have|work\s+with|serve|partner\s+with|manage)\s+(?:\d{2,}\+?\s+)?(?:clients?|brands?|businesses?|companies?)",
            r"\d{2,}\+?\s+(?:clients?|brands?|businesses?|companies?)\s+(?:and\s+growing|worldwide|globally)",
            r"(?:trusted\s+by|working\s+with)\s+\d{2,}\+?\s+(?:clients?|brands?|businesses?)",
            r"\d{2,}\+\s+(?:brands?|clients?|businesses?|companies)\s+(?:scaled|managed|grown|worked)",
        ],
    },
    "ten_plus_identifiable_business_clients": {
        "points": 25,
        "evidence_required": "portfolio, case studies, client logos",
        "patterns": [
            r"(?:our|we)\s+(?:have|work\s+with|serve|partner\s+with|manage)\s+(?:1[0-9]\+?\s+)?(?:clients?|brands?|businesses?|companies?)",
            r"1[0-9]\+?\s+(?:clients?|brands?|businesses?|companies?)\s+(?:and\s+growing|worldwide|globally)",
            r"\d{2,}\+\s+(?:brands?|clients?|businesses?)",
        ],
    },
    "five_plus_identifiable_business_clients": {
        "points": 20,
        "evidence_required": "portfolio, case studies, client logos",
        "patterns": [
            r"(?:our|we)\s+(?:have|work\s+with|serve|partner\s+with|manage)\s+(?:[5-9]\+?\s+)?(?:clients?|brands?|businesses?|companies?)",
            r"[5-9]\+?\s+(?:clients?|brands?|businesses?|companies?)\s+(?:and\s+growing|worldwide|globally)",
        ],
    },
    
    # ──── ECOMMERCE/D2C SPECIALIZATION (HIGH PRIORITY) ────
    "ecommerce_d2c_specialization": {
        "points": 20,
        "evidence_required": "service descriptions, client examples",
        "patterns": [
            r"(?:we\s+)?(?:specialize|focus|work\s+with)\s+(?:in|on|with)\s+(?:ecommerce|d2c|dtc|online\s+store|shopify|woocommerce)",
            r"(?:ecommerce|d2c|dtc|online\s+store|shopify|woocommerce)\s+(?:agency|expert|specialist|partner)",
            r"(?:our|we)\s+(?:clients?|customers?|brands?)\s+(?:are|include|are\s+mainly)\s+(?:ecommerce|d2c|dtc|shopify|woocommerce)",
            r"(?:fashion|beauty|skincare|home\s+decor|jewellery|lifestyle)\s+(?:brand|client|business)",
        ],
    },
    
    # ──── SHOPIFY/WOOCOMMERCE SPECIALIZATION (HIGH PRIORITY) ────
    "shopify_woocommerce_specialization": {
        "points": 15,
        "evidence_required": "platform expertise evidence",
        "patterns": [
            r"(?:shopify|woocommerce)\s+(?:expert|partner|agency|development|design|specialist)",
            r"(?:we\s+)?(?:build|create|develop|design)\s+(?:shopify|woocommerce)\s+(?:stores?|websites?|sites?)",
            r"(?:certified|official|partner)\s+(?:shopify|woocommerce)",
            r"shopify\s+(?:plus|partner|expert|agency|developer)",
        ],
    },
    
    # ──── RECURRING CLIENT RELATIONSHIPS (HIGH PRIORITY) ────
    "recurring_marketing_technology_services": {
        "points": 15,
        "evidence_required": "retainer-based service model",
        "patterns": [
            r"(?:monthly|recurring|ongoing|retainer)\s+(?:services?|marketing|support|management)",
            r"(?:we\s+)?(?:offer|provide|deliver)\s+(?:monthly|recurring|ongoing)\s+(?:services?|marketing|support)",
            r"(?:long[\s-]?term|recurring|ongoing)\s+(?:clients?|relationships?|partnerships?)",
            r"retainer\s+(?:client|model|basis)",
        ],
    },
    
    # ──── CRM/AUTOMATION SERVICES (MEDIUM PRIORITY) ────
    "crm_automation_services": {
        "points": 10,
        "evidence_required": "automation implementation evidence",
        "patterns": [
            r"(?:we\s+)?(?:provide|offer|deliver|implement)\s+(?:crm|automation|workflow)\s+(?:services?|solutions?|implementation)",
            r"(?:crm|automation|workflow)\s+(?:agency|company|services?|implementation|integration)",
            r"(?:hubspot|salesforce|zoho|pipedrive|freshsales)\s+(?:implementation|integration|setup|configuration)",
        ],
    },
    
    # ──── RETENTION/CONVERSION SERVICES (MEDIUM PRIORITY) ────
    "retention_conversion_services": {
        "points": 10,
        "evidence_required": "retention marketing evidence",
        "patterns": [
            r"(?:we\s+)?(?:manage|handle|optimize|improve)\s+(?:customer\s+retention|retention|conversion|abandoned\s+cart)",
            r"(?:customer\s+retention|retention|conversion)\s+(?:agency|company|services?|strategy|optimization)",
            r"(?:abandoned\s+cart|cart\s+abandonment)\s+(?:recovery|email|campaign|automation)",
        ],
    },
}


# ============================================================
# COMAI FIT SCORING CRITERIA
# ============================================================

COMAI_FIT_CRITERIA: dict[str, dict[str, Any]] = {
    "client_overlap_with_comai_icp": {
        "weight": 20,
        "evidence_required": "ecommerce/d2c client examples",
        "keywords": [
            "ecommerce", "e-commerce", "d2c", "dtc", "shopify", "woocommerce",
            "online store", "ecommerce brand", "ecommerce business",
            "product brand", "consumer brand", "retail", "direct to consumer",
            "fashion", "beauty", "skincare", "jewellery", "home decor",
            "pets", "health", "supplements", "food", "beverage", "footwear",
            "electronics", "baby products", "grooming", "personal care",
            "lifestyle", "organic", "natural", "wellness",
        ],
    },
    "ecommerce_exposure": {
        "weight": 15,
        "evidence_required": "ecommerce service offerings",
        "keywords": [
            "ecommerce", "e-commerce", "online store", "online shop",
            "shopify", "woocommerce", "bigcommerce", "magento",
            "d2c", "dtc", "direct to consumer",
        ],
    },
    "smb_exposure": {
        "weight": 10,
        "evidence_required": "smb client evidence",
        "keywords": [
            "smb", "small business", "startup", "growing business",
            "small company", "local business", "entrepreneur",
        ],
    },
    "d2c_exposure": {
        "weight": 15,
        "evidence_required": "d2c client evidence",
        "keywords": [
            "d2c", "dtc", "direct to consumer", "consumer brand",
            "product brand", "online brand", "digital brand",
        ],
    },
    "shopify_woocommerce_exposure": {
        "weight": 15,
        "evidence_required": "platform specialization",
        "keywords": [
            "shopify", "woocommerce", "shopify expert", "shopify partner",
            "woocommerce expert", "woocommerce partner",
        ],
    },
    "marketing_relationship": {
        "weight": 10,
        "evidence_required": "marketing service offerings",
        "keywords": [
            "marketing", "digital marketing", "performance marketing",
            "social media marketing", "seo", "ppc", "google ads", "meta ads",
            "facebook ads", "lead generation", "email marketing",
            "content marketing", "growth marketing",
        ],
    },
    "technology_relationship": {
        "weight": 10,
        "evidence_required": "technology implementation work",
        "keywords": [
            "development", "web development", "software development",
            "saas", "mobile app", "ui/ux", "automation", "ai",
            "crm implementation", "technology", "tech",
        ],
    },
    "automation_relationship": {
        "weight": 5,
        "evidence_required": "automation services",
        "keywords": [
            "automation", "workflow automation", "process automation",
            "marketing automation", "crm automation", "email automation",
        ],
    },
}


# ============================================================
# PARTNER SCORING ENGINE
# ============================================================

class PartnerScoringEngine:
    """Scoring engine for partner qualification.
    
    This engine calculates:
    - client_access_score: 0-100
    - comai_partner_fit: 0-100
    - partner_intent: EXPLICIT/UNKNOWN
    - partner_tier: A/B/C
    - final_verdict: PARTNER_READY/NURTURE/REJECT
    """
    
    def __init__(self):
        """Initialize the scoring engine."""
        pass
    
    def score_partner(self, partner: PartnerRecord) -> ScoringResult:
        """Score a partner record.
        
        Args:
            partner: PartnerRecord to score
            
        Returns:
            ScoringResult with all scores and classifications
        """
        result = ScoringResult()
        
        # Calculate client access score
        result.client_access_score, result.client_access_evidence, result.client_access_signals = (
            self._calculate_client_access_score(partner)
        )
        
        # Calculate COMAI partner fit
        result.comai_partner_fit, result.comai_fit_evidence, result.comai_fit_signals = (
            self._calculate_comai_partner_fit(partner)
        )
        
        # Determine partner intent
        result.partner_intent = partner.partner_intent
        result.partner_intent_evidence = partner.partner_intent_evidence
        
        # Determine partner tier
        result.partner_tier = self._determine_partner_tier(
            partner,
            result.client_access_score,
            result.comai_partner_fit,
            result.partner_intent,
        )
        
        # Determine final verdict
        result.final_verdict = self._determine_final_verdict(
            partner,
            result.client_access_score,
            result.comai_partner_fit,
            result.partner_intent,
            result.partner_tier,
        )
        
        # Check partner ready gate
        result.partner_ready_gate_passed = self._check_partner_ready_gate(
            partner,
            result.client_access_score,
            result.comai_partner_fit,
            result.partner_intent,
        )
        
        # Check high priority partner
        result.high_priority_partner = self._check_high_priority_partner(
            result.client_access_score,
            result.comai_partner_fit,
            result.partner_intent,
        )
        
        # Generate rejection reasons if needed
        if result.final_verdict == "REJECT":
            result.rejection_reasons = self._generate_rejection_reasons(
                partner,
                result.client_access_score,
                result.comai_partner_fit,
            )
        
        return result
    
    def _calculate_client_access_score(self, partner: PartnerRecord) -> tuple[int, str, list[str]]:
        """Calculate client access score (0-100)."""
        score = 0
        evidence_parts = []
        signals = []
        
        # Check each signal
        for signal_name, signal_config in CLIENT_ACCESS_SIGNALS.items():
            for pattern in signal_config["patterns"]:
                # Check in client count evidence
                if re.search(pattern, partner.client_count_evidence, re.IGNORECASE):
                    score += signal_config["points"]
                    signals.append(signal_name)
                    evidence_parts.append(f"{signal_name}: {signal_config['evidence_required']}")
                    break
                
                # Check in services
                for service in partner.services:
                    if re.search(pattern, service, re.IGNORECASE):
                        score += signal_config["points"]
                        signals.append(signal_name)
                        evidence_parts.append(f"{signal_name}: {signal_config['evidence_required']}")
                        break
                
                # Check in client industries
                for industry in partner.client_industries:
                    if re.search(pattern, industry, re.IGNORECASE):
                        score += signal_config["points"]
                        signals.append(signal_name)
                        evidence_parts.append(f"{signal_name}: {signal_config['evidence_required']}")
                        break
        
        # Additional flexible scoring based on available data
        # If we have client count evidence but didn't match specific patterns
        if partner.client_count_evidence and "clients" in partner.client_count_evidence.lower():
            # Extract number from evidence
            num_match = re.search(r"(\d+)", partner.client_count_evidence)
            if num_match:
                num = int(num_match.group(1))
                if num >= 20 and "twenty_plus" not in signals:
                    score += 30
                    signals.append("twenty_plus_identifiable_business_clients")
                    evidence_parts.append("twenty_plus_identifiable_business_clients: portfolio, case studies, client logos")
                elif num >= 10 and "ten_plus" not in signals:
                    score += 25
                    signals.append("ten_plus_identifiable_business_clients")
                    evidence_parts.append("ten_plus_identifiable_business_clients: portfolio, case studies, client logos")
                elif num >= 5 and "five_plus" not in signals:
                    score += 20
                    signals.append("five_plus_identifiable_business_clients")
                    evidence_parts.append("five_plus_identifiable_business_clients: portfolio, case studies, client logos")
        
        # Check for portfolio/clients section evidence
        if partner.client_count_evidence and ("portfolio" in partner.client_count_evidence.lower() or "clients section" in partner.client_count_evidence.lower()):
            if "portfolio_found" not in signals:
                score += 15
                signals.append("portfolio_found")
                evidence_parts.append("portfolio_found: agency showcases client work")
        
        # Check for ecommerce/D2C specialization based on services
        ecommerce_services = ["ecommerce", "d2c", "shopify", "woocommerce", "online store"]
        for service in partner.services:
            for ecommerce_service in ecommerce_services:
                if ecommerce_service in service.lower():
                    if "ecommerce_d2c_specialization" not in signals:
                        score += 20
                        signals.append("ecommerce_d2c_specialization")
                        evidence_parts.append("ecommerce_d2c_specialization: service descriptions, client examples")
                    break
        
        # Check for marketing/technology services
        marketing_services = ["marketing", "seo", "ppc", "google ads", "meta ads", "lead generation"]
        for service in partner.services:
            for marketing_service in marketing_services:
                if marketing_service in service.lower():
                    if "marketing_service_found" not in signals:
                        score += 10
                        signals.append("marketing_service_found")
                        evidence_parts.append("marketing_service_found: marketing service offerings")
                    break
        
        # Cap at 100
        score = min(score, 100)
        
        # Build evidence string
        evidence = "; ".join(evidence_parts) if evidence_parts else "No client access evidence found"
        
        return score, evidence, signals
    
    def _calculate_comai_partner_fit(self, partner: PartnerRecord) -> tuple[int, str, list[str]]:
        """Calculate COMAI partner fit score (0-100)."""
        score = 0
        evidence_parts = []
        signals = []
        
        # Check each criterion
        for criterion_name, criterion_config in COMAI_FIT_CRITERIA.items():
            criterion_score = 0
            
            # Check in services
            for service in partner.services:
                for keyword in criterion_config["keywords"]:
                    if keyword in service.lower():
                        criterion_score += criterion_config["weight"]
                        break
            
            # Check in client industries
            for industry in partner.client_industries:
                for keyword in criterion_config["keywords"]:
                    if keyword in industry.lower():
                        criterion_score += criterion_config["weight"]
                        break
            
            # Check in client count evidence
            for keyword in criterion_config["keywords"]:
                if keyword in partner.client_count_evidence.lower():
                    criterion_score += criterion_config["weight"]
                    break
            
            # Add to total score (capped at weight)
            criterion_score = min(criterion_score, criterion_config["weight"])
            score += criterion_score
            
            if criterion_score > 0:
                signals.append(criterion_name)
                evidence_parts.append(f"{criterion_name}: {criterion_config['evidence_required']}")
        
        # Cap at 100
        score = min(score, 100)
        
        # Build evidence string
        evidence = "; ".join(evidence_parts) if evidence_parts else "No COMAI fit evidence found"
        
        return score, evidence, signals
    
    def _determine_partner_tier(
        self,
        partner: PartnerRecord,
        client_access_score: int,
        comai_partner_fit: int,
        partner_intent: str,
    ) -> str:
        """Determine partner tier (A/B/C)."""
        
        # TIER A — HOT PARTNER
        # Explicit partnership/tool/reseller intent
        # + strong client portfolio
        # + high COMAI fit
        # + decision maker
        # + verified contact
        if (
            partner_intent == "EXPLICIT"
            and client_access_score >= 70
            and comai_partner_fit >= 70
            and partner.founder_name
            and partner.email_status == "VERIFIED"
        ):
            return "A"
        
        # TIER B — HIGH POTENTIAL
        # No explicit partnership request
        # but strong agency/client ecosystem
        # + high COMAI fit
        # + decision maker/contact available
        if (
            client_access_score >= 60
            and comai_partner_fit >= 60
            and partner.founder_name
            and partner.email
        ):
            return "B"
        
        # TIER C — NURTURE
        # Relevant agency but insufficient evidence of partner potential
        return "C"
    
    def _determine_final_verdict(
        self,
        partner: PartnerRecord,
        client_access_score: int,
        comai_partner_fit: int,
        partner_intent: str,
        partner_tier: str,
    ) -> str:
        """Determine final verdict."""
        
        # Check partner ready gate
        if self._check_partner_ready_gate(partner, client_access_score, comai_partner_fit, partner_intent):
            return "PARTNER_READY"
        
        # Check if tier C (nurture)
        if partner_tier == "C":
            return "NURTURE"
        
        # Check if rejected
        if partner.competitor or not partner.safety_clear:
            return "REJECT"
        
        # Default to nurture
        return "NURTURE"
    
    def _check_partner_ready_gate(
        self,
        partner: PartnerRecord,
        client_access_score: int,
        comai_partner_fit: int,
        partner_intent: str,
    ) -> bool:
        """Check if partner passes the partner ready gate."""
        
        # All conditions must be TRUE
        conditions = [
            partner.agency_type != "",  # agency_verified
            partner.services,  # relevant_service
            partner.client_count_evidence or partner.client_examples,  # business_clients_verified
            comai_partner_fit >= 70,  # comai_partner_fit >= 70
            partner.founder_name != "",  # decision_maker_identified
            partner.contactability in ["HIGH", "MEDIUM"],  # contactability >= MEDIUM
            not partner.competitor,  # competitor = FALSE
            partner.safety_clear,  # safety_clear = TRUE
        ]
        
        return all(conditions)
    
    def _check_high_priority_partner(
        self,
        client_access_score: int,
        comai_partner_fit: int,
        partner_intent: str,
    ) -> bool:
        """Check if partner is high priority."""
        
        # EXPLICIT intent
        if partner_intent == "EXPLICIT":
            return True
        
        # client_access_score >= 80 AND comai_partner_fit >= 80
        if client_access_score >= 80 and comai_partner_fit >= 80:
            return True
        
        return False
    
    def _generate_rejection_reasons(
        self,
        partner: PartnerRecord,
        client_access_score: int,
        comai_partner_fit: int,
    ) -> list[str]:
        """Generate rejection reasons."""
        reasons = []
        
        if partner.competitor:
            reasons.append("Competitor")
        
        if not partner.safety_clear:
            reasons.append("Safety check failed")
        
        if not partner.services:
            reasons.append("No relevant services identified")
        
        if not partner.client_count_evidence and not partner.client_examples:
            reasons.append("No business client evidence")
        
        if client_access_score < 30:
            reasons.append(f"Low client access score: {client_access_score}")
        
        if comai_partner_fit < 30:
            reasons.append(f"Low COMAI partner fit: {comai_partner_fit}")
        
        if not partner.founder_name:
            reasons.append("No decision maker identified")
        
        if not partner.email:
            reasons.append("No contact email found")
        
        return reasons
