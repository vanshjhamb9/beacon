"""ARIE: Contact Verification Engine.

Every field contains: Value, Source, Confidence, Verification, Last Verified,
Verification Method, Evidence URL, Status.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VerifiedField:
    """A verified field with full metadata."""
    value: str
    source: str = ""
    confidence: float = 0.0
    verification_status: str = "unknown"  # verified, likely, unknown, rejected
    last_verified: datetime = field(default_factory=datetime.utcnow)
    verification_method: str = ""
    evidence_url: str = ""
    notes: str = ""


@dataclass
class VerifiedContact:
    """Complete verified contact information."""
    domain: str
    company_name: str = ""
    
    # Contact fields
    email: VerifiedField = field(default_factory=lambda: VerifiedField(""))
    phone: VerifiedField = field(default_factory=lambda: VerifiedField(""))
    linkedin_url: VerifiedField = field(default_factory=lambda: VerifiedField(""))
    
    # Decision maker
    founder_name: VerifiedField = field(default_factory=lambda: VerifiedField(""))
    founder_role: VerifiedField = field(default_factory=lambda: VerifiedField(""))
    
    # Social
    instagram: VerifiedField = field(default_factory=lambda: VerifiedField(""))
    facebook: VerifiedField = field(default_factory=lambda: VerifiedField(""))
    twitter: VerifiedField = field(default_factory=lambda: VerifiedField(""))
    
    # Overall
    overall_confidence: float = 0.0
    verification_score: float = 0.0  # 0-100
    data_completeness: float = 0.0  # 0-100
    
    # Issues
    issues: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


class ARIEVERificationEngine:
    """Contact Verification Engine - validates all contact data."""
    
    # Email validation patterns
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    
    # Phone validation patterns (Indian)
    PHONE_REGEX = re.compile(r"^(\+91|91|0)?[6-9]\d{9}$")
    
    # Known valid email domains
    VALID_EMAIL_DOMAINS = {
        "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
        "rediffmail.com", "ymail.com", "live.com",
    }
    
    # Known invalid email patterns
    INVALID_EMAIL_PATTERNS = [
        r"test@",
        r"example@",
        r"noreply@",
        r"no-reply@",
        r"donotreply@",
        r"mailer-daemon@",
        r"postmaster@",
        r"abuse@",
        r"webmaster@",
    ]
    
    # Third-party domains (not company's own)
    THIRD_PARTY_DOMAINS = {
        "sentry.io", "glood.ai", "stagheaddesigns.com", "shopify.com",
        "google.com", "facebook.com", "twitter.com", "instagram.com",
        "linkedin.com", "youtube.com", "googleapis.com", "cloudfront.net",
        "amazonaws.com", "bootstrapcdn.com", "jquery.com", "w3.org",
        "schema.org", "ogp.me", "apple.com", "microsoft.com",
    }
    
    def verify_contact(
        self,
        contact_data: dict[str, Any],
        company_data: dict[str, Any] = None,
    ) -> VerifiedContact:
        """Verify all contact information for a company.
        
        Args:
            contact_data: Raw contact information
            company_data: Company information for cross-validation
            
        Returns:
            VerifiedContact with verification status for all fields
        """
        domain = contact_data.get("domain", "")
        company_name = contact_data.get("company_name", "")
        
        verified = VerifiedContact(
            domain=domain,
            company_name=company_name,
        )
        
        # Verify email
        verified.email = self._verify_email(
            contact_data.get("email", ""),
            domain,
            contact_data.get("email_source", ""),
        )
        
        # Verify phone
        verified.phone = self._verify_phone(
            contact_data.get("phone", ""),
            contact_data.get("phone_source", ""),
        )
        
        # Verify LinkedIn
        verified.linkedin_url = self._verify_linkedin(
            contact_data.get("linkedin_url", ""),
            contact_data.get("linkedin_source", ""),
        )
        
        # Verify founder name
        verified.founder_name = self._verify_founder_name(
            contact_data.get("founder_name", ""),
            contact_data.get("founder_source", ""),
        )
        
        # Verify founder role
        verified.founder_role = self._verify_founder_role(
            contact_data.get("founder_role", ""),
        )
        
        # Verify social
        verified.instagram = self._verify_social(
            contact_data.get("instagram", ""),
            "instagram",
        )
        verified.facebook = self._verify_social(
            contact_data.get("facebook", ""),
            "facebook",
        )
        verified.twitter = self._verify_social(
            contact_data.get("twitter", ""),
            "twitter",
        )
        
        # Calculate overall metrics
        verified.overall_confidence = self._calculate_overall_confidence(verified)
        verified.verification_score = self._calculate_verification_score(verified)
        verified.data_completeness = self._calculate_data_completeness(verified)
        
        # Check for issues
        verified.issues = self._check_issues(verified, company_data)
        verified.warnings = self._check_warnings(verified, company_data)
        
        return verified
    
    def _verify_email(self, email: str, domain: str, source: str) -> VerifiedField:
        """Verify email address."""
        if not email:
            return VerifiedField(
                value="",
                source=source,
                confidence=0.0,
                verification_status="unknown",
                notes="No email provided",
            )
        
        # Basic format validation
        if not self.EMAIL_REGEX.match(email):
            return VerifiedField(
                value=email,
                source=source,
                confidence=0.0,
                verification_status="rejected",
                notes="Invalid email format",
            )
        
        # Check invalid patterns
        for pattern in self.INVALID_EMAIL_PATTERNS:
            if re.match(pattern, email.lower()):
                return VerifiedField(
                    value=email,
                    source=source,
                    confidence=0.1,
                    verification_status="rejected",
                    notes="Generic/automated email address",
                )
        
        # Check third-party domains
        email_domain = email.split("@")[1].lower()
        if email_domain in self.THIRD_PARTY_DOMAINS:
            return VerifiedField(
                value=email,
                source=source,
                confidence=0.2,
                verification_status="rejected",
                notes=f"Third-party domain: {email_domain}",
            )
        
        # Check if email domain matches company domain
        if domain and email_domain == domain.lower():
            confidence = 0.9
            status = "verified"
            notes = "Email domain matches company domain"
        elif domain and email_domain.endswith(f".{domain.lower()}"):
            confidence = 0.85
            status = "verified"
            notes = "Email subdomain matches company domain"
        else:
            confidence = 0.5
            status = "likely"
            notes = f"Email domain ({email_domain}) differs from company domain ({domain})"
        
        return VerifiedField(
            value=email,
            source=source,
            confidence=confidence,
            verification_status=status,
            verification_method="domain_match",
            notes=notes,
        )
    
    def _verify_phone(self, phone: str, source: str) -> VerifiedField:
        """Verify phone number."""
        if not phone:
            return VerifiedField(
                value="",
                source=source,
                confidence=0.0,
                verification_status="unknown",
                notes="No phone provided",
            )
        
        # Clean phone number
        clean_phone = re.sub(r"[\s\-\(\)]", "", phone)
        
        # Check Indian phone format
        if self.PHONE_REGEX.match(clean_phone):
            # Check if it's a valid mobile prefix
            if clean_phone.startswith("+91"):
                number = clean_phone[3:]
            elif clean_phone.startswith("91"):
                number = clean_phone[2:]
            elif clean_phone.startswith("0"):
                number = clean_phone[1:]
            else:
                number = clean_phone
            
            if number.startswith("6") or number.startswith("7") or number.startswith("8") or number.startswith("9"):
                confidence = 0.8
                status = "verified"
                notes = "Valid Indian mobile number format"
            else:
                confidence = 0.4
                status = "likely"
                notes = "Phone number format valid but prefix unusual"
        else:
            confidence = 0.3
            status = "unknown"
            notes = "Phone number format not recognized as Indian"
        
        return VerifiedField(
            value=phone,
            source=source,
            confidence=confidence,
            verification_status=status,
            verification_method="format_validation",
            notes=notes,
        )
    
    def _verify_linkedin(self, linkedin_url: str, source: str) -> VerifiedField:
        """Verify LinkedIn URL."""
        if not linkedin_url:
            return VerifiedField(
                value="",
                source=source,
                confidence=0.0,
                verification_status="unknown",
                notes="No LinkedIn provided",
            )
        
        # Validate LinkedIn URL format
        linkedin_patterns = [
            r"linkedin\.com/in/[a-zA-Z0-9\-]+",
            r"linkedin\.com/company/[a-zA-Z0-9\-]+",
        ]
        
        for pattern in linkedin_patterns:
            if re.search(pattern, linkedin_url):
                return VerifiedField(
                    value=linkedin_url,
                    source=source,
                    confidence=0.9,
                    verification_status="verified",
                    verification_method="url_validation",
                    notes="Valid LinkedIn URL format",
                )
        
        return VerifiedField(
            value=linkedin_url,
            source=source,
            confidence=0.3,
            verification_status="unknown",
            notes="LinkedIn URL format not recognized",
        )
    
    def _verify_founder_name(self, name: str, source: str) -> VerifiedField:
        """Verify founder name."""
        if not name:
            return VerifiedField(
                value="",
                source=source,
                confidence=0.0,
                verification_status="unknown",
                notes="No founder name provided",
            )
        
        # Check if it looks like a real name (not company name)
        if len(name.split()) >= 2 and not name.isupper():
            confidence = 0.8
            status = "verified"
            notes = "Name appears to be a person's name"
        elif len(name.split()) == 1:
            confidence = 0.5
            status = "likely"
            notes = "Single name - may be nickname or incomplete"
        else:
            confidence = 0.3
            status = "unknown"
            notes = "Name may be a company name rather than person"
        
        return VerifiedField(
            value=name,
            source=source,
            confidence=confidence,
            verification_status=status,
            verification_method="name_analysis",
            notes=notes,
        )
    
    def _verify_founder_role(self, role: str) -> VerifiedField:
        """Verify founder role."""
        if not role:
            return VerifiedField(
                value="",
                confidence=0.0,
                verification_status="unknown",
                notes="No role provided",
            )
        
        valid_roles = [
            "founder", "ceo", "cto", "cmo", "coo", "cfo",
            "managing director", "director", "head", "vp", "vice president",
        ]
        
        role_lower = role.lower()
        for valid_role in valid_roles:
            if valid_role in role_lower:
                return VerifiedField(
                    value=role,
                    confidence=0.9,
                    verification_status="verified",
                    verification_method="role_validation",
                    notes=f"Valid executive role: {valid_role}",
                )
        
        return VerifiedField(
            value=role,
            confidence=0.5,
            verification_status="likely",
            notes="Role not in recognized executive list",
        )
    
    def _verify_social(self, url: str, platform: str) -> VerifiedField:
        """Verify social media URL."""
        if not url:
            return VerifiedField(
                value="",
                confidence=0.0,
                verification_status="unknown",
                notes=f"No {platform} URL provided",
            )
        
        # Validate URL format
        if url.startswith("http") and platform in url.lower():
            return VerifiedField(
                value=url,
                confidence=0.9,
                verification_status="verified",
                verification_method="url_validation",
                notes=f"Valid {platform} URL format",
            )
        
        return VerifiedField(
            value=url,
            confidence=0.4,
            verification_status="unknown",
            notes=f"{platform} URL format not recognized",
        )
    
    def _calculate_overall_confidence(self, verified: VerifiedContact) -> float:
        """Calculate overall confidence score."""
        fields = [
            verified.email,
            verified.phone,
            verified.linkedin_url,
            verified.founder_name,
        ]
        
        confidences = [f.confidence for f in fields if f.value]
        if not confidences:
            return 0.0
        
        return sum(confidences) / len(confidences)
    
    def _calculate_verification_score(self, verified: VerifiedContact) -> float:
        """Calculate verification score (0-100)."""
        score = 0.0
        
        # Email verification
        if verified.email.verification_status == "verified":
            score += 30
        elif verified.email.verification_status == "likely":
            score += 15
        
        # Phone verification
        if verified.phone.verification_status == "verified":
            score += 25
        elif verified.phone.verification_status == "likely":
            score += 12
        
        # LinkedIn verification
        if verified.linkedin_url.verification_status == "verified":
            score += 20
        
        # Founder verification
        if verified.founder_name.verification_status == "verified":
            score += 15
        
        # Social verification
        social_verified = sum(1 for s in [verified.instagram, verified.facebook, verified.twitter]
                           if s.verification_status == "verified")
        score += social_verified * 5
        
        return min(100.0, score)
    
    def _calculate_data_completeness(self, verified: VerifiedContact) -> float:
        """Calculate data completeness score (0-100)."""
        fields = [
            bool(verified.email.value),
            bool(verified.phone.value),
            bool(verified.linkedin_url.value),
            bool(verified.founder_name.value),
            bool(verified.founder_role.value),
            bool(verified.instagram.value),
            bool(verified.facebook.value),
            bool(verified.twitter.value),
        ]
        
        return (sum(fields) / len(fields)) * 100
    
    def _check_issues(self, verified: VerifiedContact, company_data: dict = None) -> list:
        """Check for critical issues."""
        issues = []
        
        if not verified.email.value and not verified.phone.value:
            issues.append({
                "severity": "critical",
                "type": "no_contact",
                "message": "No email or phone available",
            })
        
        if verified.email.verification_status == "rejected":
            issues.append({
                "severity": "high",
                "type": "invalid_email",
                "message": f"Email rejected: {verified.email.notes}",
            })
        
        if verified.phone.verification_status == "rejected":
            issues.append({
                "severity": "high",
                "type": "invalid_phone",
                "message": f"Phone rejected: {verified.phone.notes}",
            })
        
        return issues
    
    def _check_warnings(self, verified: VerifiedContact, company_data: dict = None) -> list:
        """Check for warnings."""
        warnings = []
        
        if verified.email.value and verified.email.confidence < 0.5:
            warnings.append({
                "severity": "medium",
                "type": "low_email_confidence",
                "message": f"Email confidence low: {verified.email.confidence:.0%}",
            })
        
        if verified.phone.value and verified.phone.confidence < 0.5:
            warnings.append({
                "severity": "medium",
                "type": "low_phone_confidence",
                "message": f"Phone confidence low: {verified.phone.confidence:.0%}",
            })
        
        if not verified.linkedin_url.value:
            warnings.append({
                "severity": "low",
                "type": "no_linkedin",
                "message": "No LinkedIn profile found",
            })
        
        if not verified.founder_name.value:
            warnings.append({
                "severity": "medium",
                "type": "no_founder",
                "message": "No decision maker identified",
            })
        
        return warnings
