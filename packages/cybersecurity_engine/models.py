"""Core data models for Cybersecurity Buyer Discovery Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ============================================================
# ENUMS
# ============================================================

class OpportunityPriority(Enum):
    P0 = "ACTIVE_BUYING_EVENT"
    P1 = "VERIFIED_SECURITY_PAIN"
    P2 = "HIGH_POTENTIAL_OUTBOUND"
    P3 = "GENERIC_ICP"
    UNKNOWN = "UNKNOWN"


class OpportunityType(Enum):
    CYBERSECURITY = "CYBERSECURITY"
    VPAT = "VPAT_ACCESSIBILITY"
    COMBINED = "COMBINED"


class ServiceLane(Enum):
    CYBERSECURITY = "CYBERSECURITY"
    VPAT = "VPAT_ACCESSIBILITY"


class OutreachClassification(Enum):
    ACTIVE_BUYING = "ACTIVE_BUYING_EVENT"
    PROBLEM_FIRST = "VERIFIED_SECURITY_PAIN"
    VPAT_OUTREACH = "VPAT_OUTREACH"
    PARTNER = "PARTNER_OPPORTUNITY"
    NURTURE = "P2_HIGH_POTENTIAL"
    NO_OUTREACH = "UNKNOWN"


class SalesReadiness(Enum):
    SALES_READY = "SALES_READY"
    MARKETING_READY = "MARKETING_READY"
    NOT_READY = "NOT_READY"


class EvidenceConfidence(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class SourceTier(Enum):
    TIER_1 = "TIER_1_DIRECT_BUYING_EVIDENCE"
    TIER_2 = "TIER_2_STRONG_SUPPORT"
    TIER_3 = "TIER_3_DISCOVERY_ONLY"


class CompanySize(Enum):
    UNKNOWN = "unknown"
    STARTUP = "startup"  # 1-10
    SMALL = "small"  # 11-50
    MEDIUM = "medium"  # 51-200
    LARGE = "large"  # 201-1000
    ENTERPRISE = "enterprise"  # 1000+


class ContactChannel(Enum):
    DECISION_MAKER_EMAIL = "decision_maker_business_email"
    DECISION_MAKER_LINKEDIN = "decision_maker_linkedin"
    PROCUREMENT_CONTACT = "procurement_contact"
    SECURITY_DEPARTMENT = "security_it_department"
    COMPANY_CONTACT = "official_company_contact"
    PHONE = "phone"


# ============================================================
# EVIDENCE
# ============================================================

@dataclass
class Evidence:
    """A single piece of evidence supporting a claim."""
    claim: str
    value: str
    source_name: str
    source_type: str  # "post", "article", "procurement", "announcement", etc.
    source_url: str
    source_status: str  # "verified", "accessible", "archived", "broken"
    published_at: datetime | None = None
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    method: str = ""  # "web_scrape", "api_fetch", "manual_verification"
    confidence: float = 0.0  # 0-100
    verified: bool = False
    verified_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "value": self.value,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "source_status": self.source_status,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "observed_at": self.observed_at.isoformat(),
            "method": self.method,
            "confidence": self.confidence,
            "verified": self.verified,
        }


# ============================================================
# CONTACT
# ============================================================

@dataclass
class Contact:
    """Contact information for a decision maker."""
    name: str = ""
    role: str = ""
    email: str = ""
    email_status: str = "unverified"  # "verified", "unverified", "guessed", "invalid"
    email_evidence: str = ""
    linkedin_url: str = ""
    linkedin_status: str = "unverified"  # "verified", "unverified", "not_found"
    phone: str = ""
    phone_status: str = "unverified"
    phone_evidence: str = ""
    identity_confidence: float = 0.0  # 0-100

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "email": self.email,
            "email_status": self.email_status,
            "email_evidence": self.email_evidence,
            "linkedin_url": self.linkedin_url,
            "linkedin_status": self.linkedin_status,
            "phone": self.phone,
            "phone_status": self.phone_status,
            "phone_evidence": self.phone_evidence,
            "identity_confidence": self.identity_confidence,
        }

    @property
    def has_reliable_contact(self) -> bool:
        """Has at least one verified contact channel."""
        return bool(
            (self.email_status == "verified" and self.email)
            or (self.linkedin_status == "verified" and self.linkedin_url)
            or (self.phone_status == "verified" and self.phone)
        )


# ============================================================
# COMPANY
# ============================================================

@dataclass
class Company:
    """Verified company profile."""
    name: str
    url: str
    country: str = ""
    industry: str = ""
    company_size: CompanySize = CompanySize.UNKNOWN
    employee_count: int = 0
    description: str = ""
    founded_year: int | None = None
    technologies: list[str] = field(default_factory=list)
    funding_stage: str = ""
    last_funding_date: str | None = None
    revenue_estimate: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "country": self.country,
            "industry": self.industry,
            "company_size": self.company_size.value,
            "employee_count": self.employee_count,
            "description": self.description,
            "founded_year": self.founded_year,
            "technologies": self.technologies,
            "funding_stage": self.funding_stage,
            "last_funding_date": self.last_funding_date,
            "revenue_estimate": self.revenue_estimate,
        }

    @property
    def is_icp_match(self) -> bool:
        """Check if company matches ICP criteria."""
        icp_industries = {
            "SaaS", "B2B SaaS", "Fintech", "Healthtech", "Ecommerce",
            "Marketplace", "AI", "EdTech", "HRTech", "InsurTech",
            "LegalTech", "PropTech", "Logistics", "Enterprise Software",
        }
        return self.industry in icp_industries


# ============================================================
# BUYING EVENT
# ============================================================

@dataclass
class BuyingEvent:
    """A detected buying event or security pain signal."""
    event_type: str  # "active_buying", "verified_pain", "outbound_signal"
    description: str
    service_match: str  # "HIGH", "MEDIUM", "LOW"
    service_lane: ServiceLane = ServiceLane.CYBERSECURITY
    services_needed: list[str] = field(default_factory=list)
    why_now: str = ""
    urgency: str = "normal"  # "urgent", "normal", "low"

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "description": self.description,
            "service_match": self.service_match,
            "service_lane": self.service_lane.value,
            "services_needed": self.services_needed,
            "why_now": self.why_now,
            "urgency": self.urgency,
        }


# ============================================================
# OUTREACH PREPARATION
# ============================================================

@dataclass
class OutreachPreparation:
    """Prepared outreach materials for a qualified opportunity."""
    buyer_name: str = ""
    buyer_role: str = ""
    company_name: str = ""
    problem_summary: str = ""
    evidence_summary: str = ""
    why_now: str = ""
    recommended_service: str = ""
    recommended_channel: str = ""
    personalization_points: list[str] = field(default_factory=list)
    outreach_angle: str = ""
    personalized_message: str = ""
    follow_up_sequence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "buyer_name": self.buyer_name,
            "buyer_role": self.buyer_role,
            "company_name": self.company_name,
            "problem_summary": self.problem_summary,
            "evidence_summary": self.evidence_summary,
            "why_now": self.why_now,
            "recommended_service": self.recommended_service,
            "recommended_channel": self.recommended_channel,
            "personalization_points": self.personalization_points,
            "outreach_angle": self.outreach_angle,
            "personalized_message": self.personalized_message,
            "follow_up_sequence": self.follow_up_sequence,
        }


# ============================================================
# CYBERSECURITY OPPORTUNITY (Main Entity)
# ============================================================

@dataclass
class CybersecurityOpportunity:
    """A verified cybersecurity opportunity ready for outreach."""

    # Identity
    opportunity_id: str = ""
    company: Company = field(default_factory=lambda: Company(name="", url=""))

    # Classification
    opportunity_type: OpportunityType = OpportunityType.CYBERSECURITY
    priority: OpportunityPriority = OpportunityPriority.UNKNOWN
    final_verdict: str = ""  # "SALES_READY", "MARKETING_READY", "NOT_READY"

    # Buying Event
    buying_event: BuyingEvent = field(default_factory=lambda: BuyingEvent(event_type="no_signal", description="", service_match="LOW"))

    # Contact
    contact: Contact = field(default_factory=Contact)

    # Evidence
    evidence_chain: list[Evidence] = field(default_factory=list)
    evidence_confidence: EvidenceConfidence = EvidenceConfidence.LOW

    # Outreach
    outreach_classification: OutreachClassification = OutreachClassification.NO_OUTREACH
    outreach_preparation: OutreachPreparation = field(default_factory=OutreachPreparation)

    # Source Tracking
    source_name: str = ""
    source_type: str = ""
    source_url: str = ""
    source_status: str = ""
    published_at: datetime | None = None
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Contactability
    contactability: str = "low"
    contactability_evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "company": self.company.to_dict(),
            "opportunity_type": self.opportunity_type.value,
            "priority": self.priority.value,
            "final_verdict": self.final_verdict,
            "buying_event": self.buying_event.to_dict(),
            "contact": self.contact.to_dict(),
            "evidence_chain": [e.to_dict() for e in self.evidence_chain],
            "evidence_confidence": self.evidence_confidence.value,
            "outreach_classification": self.outreach_classification.value,
            "outreach_preparation": self.outreach_preparation.to_dict(),
            "source_name": self.source_name,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "source_status": self.source_status,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "observed_at": self.observed_at.isoformat(),
            "contactability": self.contactability,
            "contactability_evidence": self.contactability_evidence,
        }

    @property
    def is_sales_ready(self) -> bool:
        """Final CTO test: Would a cybersecurity sales rep contact this company TODAY?"""
        return self.final_verdict == "SALES_READY"

    @property
    def evidence_count(self) -> int:
        return len(self.evidence_chain)

    @property
    def verified_evidence_count(self) -> int:
        return sum(1 for e in self.evidence_chain if e.verified)

    def add_evidence(
        self,
        claim: str,
        value: str,
        source_name: str,
        source_type: str,
        source_url: str,
        source_status: str = "accessible",
        method: str = "",
        confidence: float = 0.0,
        verified: bool = False,
        published_at: datetime | None = None,
    ) -> None:
        """Add a piece of evidence to the chain."""
        self.evidence_chain.append(
            Evidence(
                claim=claim,
                value=value,
                source_name=source_name,
                source_type=source_type,
                source_url=source_url,
                source_status=source_status,
                method=method,
                confidence=confidence,
                verified=verified,
                published_at=published_at,
            )
        )
