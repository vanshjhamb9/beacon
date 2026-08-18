"""COMAI B2B Partner Discovery Engine - Contactability Verification.

This module implements contact verification for partner qualification.
Ensures legitimate contact routes and decision maker identification.

COMAI B2B IS NOT AN AGENCY DIRECTORY.
WE ARE BUILDING A PARTNER ACQUISITION ENGINE.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.models.partner import (
    ContactabilityLevel,
    ContactabilityResult,
    EmailStatus,
    PartnerRecord,
)


# ============================================================
# EMAIL VALIDATION
# ============================================================

GENERIC_EMAIL_PREFIXES = {
    "support", "info", "hello", "sales", "care", "contact", "help",
    "feedback", "noreply", "no-reply", "admin", "office", "team",
    "billing", "careers", "jobs", "hr", "enquiry", "cs", "business",
    "name", "customercare", "orders", "returns", "marketing",
    "press", "media", "legal", "privacy", "abuse", "postmaster",
    "webmaster", "hostmaster", "root", "daemon", "mailer-daemon",
}

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "icloud.com", "mail.com", "protonmail.com", "zoho.com", "yandex.com",
    "163.com", "qq.com", "sina.com", "sohu.com",
}

INVALID_EMAIL_PATTERNS = {
    ".jpg", ".png", ".webp", ".gif", ".svg", "@2x", "assets", "cdn",
    "static", "media", "images", "files", "base64", "example.com",
    "test.com", "domain.com", "email.com", "your.com",
}

DECISION_MAKER_ROLES = {
    "founder", "co-founder", "cofounder", "ceo", "chief executive officer",
    "owner", "managing director", "head of partnerships",
    "business development director", "growth director",
    "client services director", "account director",
    "partner manager", "partnership manager", "business development manager",
}


# ============================================================
# CONTACTABILITY VERIFICATION ENGINE
# ============================================================

class ContactabilityVerificationEngine:
    """Contactability verification engine for partner qualification.
    
    This engine verifies:
    - Email validity and status
    - Decision maker identification
    - LinkedIn presence
    - Overall contactability level
    """
    
    def __init__(self):
        """Initialize the verification engine."""
        pass
    
    def verify_contactability(self, partner: PartnerRecord) -> ContactabilityResult:
        """Verify contactability for a partner.
        
        Args:
            partner: PartnerRecord to verify
            
        Returns:
            ContactabilityResult with verification results
        """
        result = ContactabilityResult()
        
        # Verify email
        result.email, result.email_status, result.email_evidence = (
            self._verify_email(partner.email, partner.agency_url)
        )
        
        # Verify decision maker
        result.decision_maker_name = partner.founder_name
        result.decision_maker_role = partner.founder_role
        result.decision_maker_identified = bool(partner.founder_name)
        
        # Verify LinkedIn
        result.linkedin_url = partner.linkedin_url
        result.linkedin_status = self._verify_linkedin(partner.linkedin_url)
        
        # Determine contactability level
        result.contactability_level, result.contactability_evidence = (
            self._determine_contactability_level(result)
        )
        
        return result
    
    def _verify_email(self, email: str, agency_url: str) -> tuple[str, str, str]:
        """Verify email validity and status."""
        if not email:
            return "", "UNKNOWN", "No email found"
        
        # Check for invalid patterns
        email_lower = email.lower()
        for pattern in INVALID_EMAIL_PATTERNS:
            if pattern in email_lower:
                return email, "INVALID", f"Email contains invalid pattern: {pattern}"
        
        # Check for free email domains
        domain = email.split("@")[-1] if "@" in email else ""
        if domain in FREE_EMAIL_DOMAINS:
            return email, "PUBLIC_UNVERIFIED", f"Free email domain: {domain}"
        
        # Check for generic prefix
        prefix = email.split("@")[0] if "@" in email else ""
        if prefix.lower() in GENERIC_EMAIL_PREFIXES:
            return email, "PUBLIC_UNVERIFIED", f"Generic email prefix: {prefix}"
        
        # Check email format
        if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
            return email, "INVALID", "Invalid email format"
        
        # Email looks valid but unverified
        return email, "PUBLIC_UNVERIFIED", "Email found on website"
    
    def _verify_linkedin(self, linkedin_url: str) -> str:
        """Verify LinkedIn URL."""
        if not linkedin_url:
            return "NOT_FOUND"
        
        # Check if it's a valid LinkedIn URL
        if re.match(r"https?://(?:www\.)?linkedin\.com/(?:company|in)/[a-zA-Z0-9\-]+", linkedin_url):
            return "FOUND"
        
        return "INVALID"
    
    def _determine_contactability_level(self, result: ContactabilityResult) -> tuple[str, str]:
        """Determine contactability level."""
        evidence_parts = []
        
        # HIGH: Verified email + LinkedIn + decision maker identified
        if (
            result.email_status == "VERIFIED"
            and result.linkedin_status == "FOUND"
            and result.decision_maker_identified
        ):
            evidence_parts.append("Verified email")
            evidence_parts.append("LinkedIn found")
            evidence_parts.append("Decision maker identified")
            return "HIGH", "; ".join(evidence_parts)
        
        # MEDIUM: Public unverified email + LinkedIn OR decision maker identified
        if (
            result.email_status == "PUBLIC_UNVERIFIED"
            and (result.linkedin_status == "FOUND" or result.decision_maker_identified)
        ):
            evidence_parts.append("Public unverified email")
            if result.linkedin_status == "FOUND":
                evidence_parts.append("LinkedIn found")
            if result.decision_maker_identified:
                evidence_parts.append("Decision maker identified")
            return "MEDIUM", "; ".join(evidence_parts)
        
        # LOW: Limited contact information
        if result.email or result.linkedin_status == "FOUND":
            if result.email:
                evidence_parts.append(f"Email status: {result.email_status}")
            if result.linkedin_status == "FOUND":
                evidence_parts.append("LinkedIn found")
            return "LOW", "; ".join(evidence_parts)
        
        # NONE: No contact route
        return "NONE", "No contact route found"
    
    def extract_decision_maker_from_html(self, html: str) -> tuple[str, str]:
        """Extract decision maker information from HTML."""
        name = ""
        role = ""
        
        # Try to extract founder/CEO name
        founder_patterns = [
            (r"(?:founder|co-founder|cofounder)[\s:]+([A-Z][a-z]+ [A-Z][a-z]+)", "Founder"),
            (r"(?:ceo|chief\s+executive\s+officer)[\s:]+([A-Z][a-z]+ [A-Z][a-z]+)", "CEO"),
            (r"(?:owner|managing\s+director)[\s:]+([A-Z][a-z]+ [A-Z][a-z]+)", "Owner"),
            (r"(?:head\s+of\s+partnerships?|partnership\s+manager)[\s:]+([A-Z][a-z]+ [A-Z][a-z]+)", "Head of Partnerships"),
            (r"(?:business\s+development\s+director|growth\s+director)[\s:]+([A-Z][a-z]+ [A-Z][a-z]+)", "Business Development Director"),
        ]
        
        for pattern, detected_role in founder_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                name = match.group(1)
                role = detected_role
                break
        
        return name, role
    
    def extract_contact_page_url(self, html: str, base_url: str) -> str:
        """Extract contact page URL from HTML."""
        contact_patterns = [
            r"href=[\"\'](https?://[^\"\']*contact[^\"\']*)[\"\']",
            r"href=[\"\'](/contact[^\"\']*)[\"\']",
            r"href=[\"\'](https?://[^\"\']*about[^\"\']*)[\"\']",
            r"href=[\"\'](/about[^\"\']*)[\"\']",
        ]
        
        for pattern in contact_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                url = match.group(1)
                if url.startswith("/"):
                    url = base_url.rstrip("/") + url
                return url
        
        return ""
    
    def extract_partnership_page_url(self, html: str, base_url: str) -> str:
        """Extract partnership page URL from HTML."""
        partnership_patterns = [
            r"href=[\"\'](https?://[^\"\']*partner[^\"\']*)[\"\']",
            r"href=[\"\'](/partner[^\"\']*)[\"\']",
            r"href=[\"\'](https?://[^\"\']*resell[^\"\']*)[\"\']",
            r"href=[\"\'](/resell[^\"\']*)[\"\']",
            r"href=[\"\'](https?://[^\"\']*affiliate[^\"\']*)[\"\']",
            r"href=[\"\'](/affiliate[^\"\']*)[\"\']",
        ]
        
        for pattern in partnership_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                url = match.group(1)
                if url.startswith("/"):
                    url = base_url.rstrip("/") + url
                return url
        
        return ""
