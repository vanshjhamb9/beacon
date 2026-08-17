"""COMAI B2B Partner Discovery Engine - Data Models.

This module defines the data structures for the partner discovery lane.
Separate from direct ecommerce leads, INOWIX software-development leads,
and cybersecurity leads.

COMAI B2B IS NOT AN AGENCY DIRECTORY.
WE ARE BUILDING A PARTNER ACQUISITION ENGINE.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ============================================================
# ENUMS
# ============================================================

class PartnerIntent(str, Enum):
    """Partner intent classification."""
    EXPLICIT = "EXPLICIT"
    UNKNOWN = "UNKNOWN"


class PartnerPotential(str, Enum):
    """Partner potential classification."""
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PartnerTier(str, Enum):
    """Partner tier classification."""
    A = "A"  # HOT PARTNER
    B = "B"  # HIGH POTENTIAL
    C = "C"  # NURTURE


class FinalVerdict(str, Enum):
    """Final verdict for partner qualification."""
    PARTNER_READY = "PARTNER_READY"
    NURTURE = "NURTURE"
    REJECT = "REJECT"


class EmailStatus(str, Enum):
    """Email verification status."""
    VERIFIED = "VERIFIED"
    PUBLIC_UNVERIFIED = "PUBLIC_UNVERIFIED"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"


class ContactabilityLevel(str, Enum):
    """Contactability level."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class AgencyType(str, Enum):
    """Agency type classification."""
    MARKETING = "marketing"
    TECHNOLOGY = "technology"
    CREATIVE = "creative"
    CONSULTANT = "consultant"


# ============================================================
# EVIDENCE
# ============================================================

@dataclass
class Evidence:
    """Evidence for any claim."""
    claim: str
    value: str
    source: str
    url: str
    method: str
    confidence: float  # 0-100
    verified: bool = False
    verified_at: str = ""

    def to_dict(self) -> dict:
        return {
            "claim": self.claim,
            "value": self.value,
            "source": self.source,
            "url": self.url,
            "method": self.method,
            "confidence": self.confidence,
            "verified": self.verified,
        }


# ============================================================
# PARTNER RECORD
# ============================================================

@dataclass
class PartnerRecord:
    """Complete partner record for COMAI B2B Partner Discovery."""
    
    # Identity
    opportunity_id: str = ""
    agency_name: str = ""
    agency_url: str = ""
    country: str = ""
    city: str = ""
    agency_type: str = ""  # marketing, technology, creative, consultant
    
    # Decision Maker
    founder_name: str = ""
    founder_role: str = ""
    linkedin_url: str = ""
    identity_confidence: float = 0.0
    
    # Services & Clients
    services: list[str] = field(default_factory=list)
    client_count_evidence: str = ""
    client_examples: list[str] = field(default_factory=list)
    client_industries: list[str] = field(default_factory=list)
    
    # Partner Intent
    partner_intent: str = "UNKNOWN"  # EXPLICIT, UNKNOWN
    partner_intent_evidence: str = ""
    
    # Scoring
    client_access_score: int = 0  # 0-100
    client_access_evidence: str = ""
    comai_partner_fit: int = 0  # 0-100
    comai_fit_evidence: str = ""
    
    # Contact
    business_phone: str = ""
    
    # Outreach
    recommended_pitch_angle: str = ""
    why_this_agency: str = ""
    
    # Contactability
    email: str = ""
    email_status: str = "UNKNOWN"  # VERIFIED, PUBLIC_UNVERIFIED, INVALID, UNKNOWN
    email_evidence: str = ""
    linkedin_status: str = ""
    contactability: str = "NONE"  # HIGH, MEDIUM, LOW, NONE
    contactability_evidence: str = ""
    
    # Safety
    competitor: bool = False
    safety_clear: bool = True
    
    # Classification
    partner_tier: str = "C"  # A, B, C
    final_verdict: str = "NURTURE"  # PARTNER_READY, NURTURE, REJECT
    rejection_reason: str = ""
    
    # Evidence Trail
    evidence: list[Evidence] = field(default_factory=list)
    
    # Metadata
    discovered_at: str = ""
    last_updated: str = ""
    discovery_source: str = ""

    def add_evidence(self, claim: str, value: str, source: str, url: str, method: str, confidence: float):
        """Add evidence for a claim."""
        self.evidence.append(Evidence(claim, value, source, url, method, confidence))

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "opportunity_id": self.opportunity_id,
            "agency_name": self.agency_name,
            "agency_url": self.agency_url,
            "country": self.country,
            "city": self.city,
            "agency_type": self.agency_type,
            "founder_name": self.founder_name,
            "founder_role": self.founder_role,
            "linkedin_url": self.linkedin_url,
            "identity_confidence": self.identity_confidence,
            "services": self.services,
            "client_count_evidence": self.client_count_evidence,
            "client_examples": self.client_examples,
            "client_industries": self.client_industries,
            "partner_intent": self.partner_intent,
            "partner_intent_evidence": self.partner_intent_evidence,
            "client_access_score": self.client_access_score,
            "client_access_evidence": self.client_access_evidence,
            "comai_partner_fit": self.comai_partner_fit,
            "comai_fit_evidence": self.comai_fit_evidence,
            "recommended_pitch_angle": self.recommended_pitch_angle,
            "why_this_agency": self.why_this_agency,
            "email": self.email,
            "email_status": self.email_status,
            "email_evidence": self.email_evidence,
            "linkedin_status": self.linkedin_status,
            "contactability": self.contactability,
            "contactability_evidence": self.contactability_evidence,
            "competitor": self.competitor,
            "safety_clear": self.safety_clear,
            "partner_tier": self.partner_tier,
            "final_verdict": self.final_verdict,
            "rejection_reason": self.rejection_reason,
            "evidence": [e.to_dict() for e in self.evidence],
            "discovered_at": self.discovered_at,
            "last_updated": self.last_updated,
            "discovery_source": self.discovery_source,
        }


# ============================================================
# DISCOVERY RESULT
# ============================================================

@dataclass
class DiscoveryResult:
    """Result of partner discovery process."""
    
    # Input
    input_url: str = ""
    input_company_name: str = ""
    input_source: str = ""
    
    # Output
    partner_record: PartnerRecord | None = None
    is_agency: bool = False
    agency_verified: bool = False
    relevant_service: bool = False
    business_clients_verified: bool = False
    
    # Classification
    classification: str = "PENDING"
    rejection_reasons: list[str] = field(default_factory=list)
    
    # Evidence
    evidence: list[Evidence] = field(default_factory=list)
    
    # Timing
    discovered_at: str = ""
    processing_time_ms: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "input_url": self.input_url,
            "input_company_name": self.input_company_name,
            "input_source": self.input_source,
            "partner_record": self.partner_record.to_dict() if self.partner_record else None,
            "is_agency": self.is_agency,
            "agency_verified": self.agency_verified,
            "relevant_service": self.relevant_service,
            "business_clients_verified": self.business_clients_verified,
            "classification": self.classification,
            "rejection_reasons": self.rejection_reasons,
            "evidence": [e.to_dict() for e in self.evidence],
            "discovered_at": self.discovered_at,
            "processing_time_ms": self.processing_time_ms,
        }


# ============================================================
# SCORING RESULT
# ============================================================

@dataclass
class ScoringResult:
    """Result of partner scoring."""
    
    client_access_score: int = 0
    client_access_evidence: str = ""
    client_access_signals: list[str] = field(default_factory=list)
    
    comai_partner_fit: int = 0
    comai_fit_evidence: str = ""
    comai_fit_signals: list[str] = field(default_factory=list)
    
    partner_intent: str = "UNKNOWN"
    partner_intent_evidence: str = ""
    
    partner_tier: str = "C"
    final_verdict: str = "NURTURE"
    
    partner_ready_gate_passed: bool = False
    high_priority_partner: bool = False
    
    rejection_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "client_access_score": self.client_access_score,
            "client_access_evidence": self.client_access_evidence,
            "client_access_signals": self.client_access_signals,
            "comai_partner_fit": self.comai_partner_fit,
            "comai_fit_evidence": self.comai_fit_evidence,
            "comai_fit_signals": self.comai_fit_signals,
            "partner_intent": self.partner_intent,
            "partner_intent_evidence": self.partner_intent_evidence,
            "partner_tier": self.partner_tier,
            "final_verdict": self.final_verdict,
            "partner_ready_gate_passed": self.partner_ready_gate_passed,
            "high_priority_partner": self.high_priority_partner,
            "rejection_reasons": self.rejection_reasons,
        }


# ============================================================
# CONTACTABILITY RESULT
# ============================================================

@dataclass
class ContactabilityResult:
    """Result of contactability verification."""
    
    email: str = ""
    email_status: str = "UNKNOWN"
    email_evidence: str = ""
    
    phone: str = ""
    phone_status: str = "UNKNOWN"
    phone_evidence: str = ""
    
    linkedin_url: str = ""
    linkedin_status: str = "UNKNOWN"
    linkedin_evidence: str = ""
    
    decision_maker_name: str = ""
    decision_maker_role: str = ""
    decision_maker_identified: bool = False
    
    contactability_level: str = "NONE"
    contactability_evidence: str = ""
    
    contact_page_url: str = ""
    partnership_page_url: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "email": self.email,
            "email_status": self.email_status,
            "email_evidence": self.email_evidence,
            "phone": self.phone,
            "phone_status": self.phone_status,
            "phone_evidence": self.phone_evidence,
            "linkedin_url": self.linkedin_url,
            "linkedin_status": self.linkedin_status,
            "linkedin_evidence": self.linkedin_evidence,
            "decision_maker_name": self.decision_maker_name,
            "decision_maker_role": self.decision_maker_role,
            "decision_maker_identified": self.decision_maker_identified,
            "contactability_level": self.contactability_level,
            "contactability_evidence": self.contactability_evidence,
            "contact_page_url": self.contact_page_url,
            "partnership_page_url": self.partnership_page_url,
        }


# ============================================================
# EXPORT DATA
# ============================================================

@dataclass
class ExportData:
    """Export data for partner discovery results."""
    
    generated_at: str = ""
    total_discovered: int = 0
    verified_agencies: int = 0
    explicit_partnership_intent: int = 0
    high_potential: int = 0
    hot_partners: int = 0
    contactable: int = 0
    tier_a: int = 0
    tier_b: int = 0
    tier_c: int = 0
    rejected: int = 0
    
    hot_partners_list: list[PartnerRecord] = field(default_factory=list)
    high_potential_list: list[PartnerRecord] = field(default_factory=list)
    nurture_list: list[PartnerRecord] = field(default_factory=list)
    rejected_list: list[PartnerRecord] = field(default_factory=list)
    
    evidence_audit: list[dict] = field(default_factory=list)
    contactability_audit: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "generated_at": self.generated_at,
            "total_discovered": self.total_discovered,
            "verified_agencies": self.verified_agencies,
            "explicit_partnership_intent": self.explicit_partnership_intent,
            "high_potential": self.high_potential,
            "hot_partners": self.hot_partners,
            "contactable": self.contactable,
            "tier_a": self.tier_a,
            "tier_b": self.tier_b,
            "tier_c": self.tier_c,
            "rejected": self.rejected,
            "hot_partners_list": [p.to_dict() for p in self.hot_partners_list],
            "high_potential_list": [p.to_dict() for p in self.high_potential_list],
            "nurture_list": [p.to_dict() for p in self.nurture_list],
            "rejected_list": [p.to_dict() for p in self.rejected_list],
            "evidence_audit": self.evidence_audit,
            "contactability_audit": self.contactability_audit,
        }
