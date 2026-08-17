"""Canonical Opportunity Model for Beacon Intent-First Sales Intelligence.

Extends the existing opportunity_intelligence models with:
- Multi-ICP scoring (COMAI, SaaS Development, Custom Software)
- Intent detection and classification
- Service matching
- Decision maker tracking
- Qualification and outreach status
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any


# ============================================================
# ENUMS
# ============================================================

class IntentLevel(StrEnum):
    """How explicit is the buying requirement."""
    ACTIVE_REQUIREMENT = "ACTIVE_REQUIREMENT"    # Explicitly looking for solution
    EVALUATION = "EVALUATION"                    # Comparing vendors/options
    EARLY_INTENT = "EARLY_INTENT"                # Problem aware, not solution seeking
    COMPANY_OPPORTUNITY = "COMPANY_OPPORTUNITY"  # Fits ICP, no explicit intent
    NO_INTENT = "NO_INTENT"                      # No signal found


class BusinessUnit(StrEnum):
    """Inowix business units."""
    COMAI = "COMAI"
    SAAS_DEVELOPMENT = "SAAS_DEVELOPMENT"
    CUSTOM_SOFTWARE = "CUSTOM_SOFTWARE"
    CYBERSECURITY = "CYBERSECURITY"


class QualificationStatus(StrEnum):
    """Opportunity qualification state."""
    DISCOVERED = "DISCOVERED"
    ENRICHED = "ENRICHED"
    QUALIFIED = "QUALIFIED"
    SALES_READY = "SALES_READY"
    REJECTED = "REJECTED"


class OutreachStatus(StrEnum):
    """Outreach tracking state."""
    NOT_STARTED = "NOT_STARTED"
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    SENT = "SENT"
    REPLIED = "REPLIED"
    FOLLOW_UP = "FOLLOW_UP"
    MEETING_BOOKED = "MEETING_BOOKED"
    OPTED_OUT = "OPTED_OUT"
    CLOSED = "CLOSED"


class EvidenceConfidence(StrEnum):
    """Evidence confidence levels."""
    VERIFIED = "VERIFIED"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


# ============================================================
# EVIDENCE
# ============================================================

@dataclass
class EvidenceRecord:
    """A single piece of evidence for an opportunity."""
    claim: str
    value: str
    source: str
    source_url: str
    confidence: EvidenceConfidence
    observed_at: date


@dataclass
class ContactInfo:
    """Decision maker contact information."""
    name: str = ""
    role: str = ""
    email: str = ""
    email_valid: bool = False
    phone: str = ""
    linkedin_url: str = ""
    confidence: EvidenceConfidence = EvidenceConfidence.UNKNOWN


# ============================================================
# INTENT
# ============================================================

@dataclass
class IntentSignal:
    """A detected intent signal."""
    signal_text: str
    signal_source: str
    signal_url: str
    intent_level: IntentLevel
    intent_score: float  # 0-100
    detected_at: date
    evidence: list[EvidenceRecord] = field(default_factory=list)


# ============================================================
# SERVICE MATCH
# ============================================================

@dataclass
class ServiceMatch:
    """Matched Inowix service for an opportunity."""
    business_unit: BusinessUnit
    service_name: str
    service_description: str
    match_confidence: float  # 0-1
    match_reasons: list[str] = field(default_factory=list)


# ============================================================
# ICP SCORES
# ============================================================

@dataclass
class ICPScore:
    """Score for a single ICP dimension."""
    score: float = 0.0  # 0-100
    confidence: float = 0.0  # 0-1
    evidence: list[EvidenceRecord] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    signals_found: list[str] = field(default_factory=list)


# ============================================================
# OPPORTUNITY (CANONICAL)
# ============================================================

@dataclass
class Opportunity:
    """Canonical opportunity record for Beacon.

    Every discovered buying opportunity produces one of these.
    This is the single source of truth for an opportunity.
    """
    # Identity
    opportunity_id: str
    discovery_source: str
    discovery_source_url: str
    discovery_date: date
    discovery_reason: str

    # Company
    company_name: str
    domain: str
    company_stage: str  # early, growing, mid_size, enterprise
    industry: str
    city: str = ""
    country: str = "India"

    # Person / Decision Maker
    founder_name: str = ""
    founder_role: str = ""
    founder_email: str = ""
    founder_email_valid: bool = False
    founder_phone: str = ""
    founder_linkedin: str = ""
    founder_confidence: EvidenceConfidence = EvidenceConfidence.UNKNOWN

    # Intent
    intent_level: IntentLevel = IntentLevel.NO_INTENT
    intent_score: float = 0.0  # 0-100
    intent_signals: list[IntentSignal] = field(default_factory=list)
    explicit_requirement: str = ""  # What they explicitly need

    # ICP Fit (separate scores)
    comai_score: ICPScore = field(default_factory=ICPScore)
    saas_score: ICPScore = field(default_factory=ICPScore)
    custom_score: ICPScore = field(default_factory=ICPScore)

    # Opportunity Score (separate from ICP)
    # ICP Fit * 0.3 + Intent * 0.4 + Buyability * 0.3
    icp_fit_score: float = 0.0  # Best of comai/saas/custom
    buyability_score: float = 0.0
    opportunity_score: float = 0.0

    # Routing
    primary_business_unit: BusinessUnit = BusinessUnit.COMAI
    secondary_business_units: list[BusinessUnit] = field(default_factory=list)
    service_matches: list[ServiceMatch] = field(default_factory=list)

    # Sales Intelligence
    why_this_matters: str = ""
    what_they_achieving: str = ""
    likely_pain: str = ""
    evidence_for_pain: str = ""
    why_inowix_relevant: str = ""
    recommended_service: str = ""
    recommended_pitch: str = ""
    why_now: str = ""
    likely_objection: str = ""
    suggested_cta: str = ""

    # Buying Signals
    buying_signals: list[str] = field(default_factory=list)
    buying_signal_sources: list[str] = field(default_factory=list)

    # Growth Signals
    growth_signals: list[str] = field(default_factory=list)

    # Technology
    technology_signals: list[str] = field(default_factory=list)

    # Evidence (all evidence for this opportunity)
    evidence: list[EvidenceRecord] = field(default_factory=list)

    # Missing Information
    missing_information: list[str] = field(default_factory=list)
    recommended_research: list[str] = field(default_factory=list)

    # Status
    qualification_status: QualificationStatus = QualificationStatus.DISCOVERED
    outreach_status: OutreachStatus = OutreachStatus.NOT_STARTED

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
