"""Evidence Extractor — CTO Hotfix.

Extracts structured evidence from verified source URLs.
Ensures every opportunity has verifiable, non-fabricated evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class IdentityConfidence(Enum):
    VERIFIED = "VERIFIED"       # Named person with public profile
    HIGH = "HIGH"               # Named person, role confirmed
    MEDIUM = "MEDIUM"           # Named person, role inferred
    LOW = "LOW"                 # Anonymous or generic identity
    UNKNOWN = "UNKNOWN"         # Cannot determine


class EvidenceConfidence(Enum):
    VERIFIED = "VERIFIED"       # Exact quote from exact post
    HIGH = "HIGH"               # Strong evidence, specific post
    MEDIUM = "MEDIUM"           # Evidence present but indirect
    LOW = "LOW"                 # Weak or inferred evidence
    UNKNOWN = "UNKNOWN"         # Cannot determine


class ProspectType(Enum):
    BUYER = "BUYER"                         # Explicitly looking to buy
    POTENTIAL_BUYER = "POTENTIAL_BUYER"     # May need services
    SERVICE_PROVIDER = "SERVICE_PROVIDER"   # Agency, consultancy
    SOFTWARE_DEV = "SOFTWARE_DEV"           # Software development company
    AI_DEV = "AI_DEV"                       # AI development company
    FREELANCER = "FREELANCER"               # Independent freelancer
    JOB_SEEKER = "JOB_SEEKER"              # Looking for employment
    UNKNOWN = "UNKNOWN"


class OutsourcingIntent(Enum):
    EXPLICIT_OUTSOURCING = "EXPLICIT_OUTSOURCING"
    STRONG_EXTERNAL_SIGNAL = "STRONG_EXTERNAL_SIGNAL"
    POSSIBLE_EXTERNAL_NEED = "POSSIBLE_EXTERNAL_NEED"
    INTERNAL_HIRING_ONLY = "INTERNAL_HIRING_ONLY"
    UNKNOWN = "UNKNOWN"


@dataclass
class EvidenceRecord:
    """Structured evidence for one opportunity."""
    # Source
    source_url: str = ""
    source_platform: str = ""
    source_title: str = ""
    source_author: str = ""
    author_profile_url: str = ""
    published_at: str = ""
    discovered_at: str = ""

    # Evidence
    evidence_text: str = ""
    requirement: str = ""
    discovery_reason: str = ""

    # Person
    person_name: str = ""
    person_role: str = ""
    identity_confidence: str = "UNKNOWN"
    company_name: str = ""

    # Classification
    prospect_type: str = "UNKNOWN"
    outsourcing_intent: str = "UNKNOWN"
    evidence_confidence: str = "UNKNOWN"

    # Services
    bu_match: str = ""
    service_match: list[str] = field(default_factory=list)

    # Contact
    public_email: str = ""
    email_status: str = "UNKNOWN"
    linkedin_url: str = ""

    # Metadata
    technology_signals: list[str] = field(default_factory=list)
    budget: str = ""
    timeline: str = ""
    location: str = ""
    industry: str = ""

    # Audit trail
    validation_status: str = ""
    rejection_reason: str = ""
    notes: str = ""


# ── EVIDENCE QUALITY RULES ──────────────────────────────────────────

def classify_person(person_name: str, role: str) -> str:
    """Classify identity confidence based on name and role."""
    if not person_name or person_name in ("Reddit User", "Upwork Client", "LinkedIn User",
                                            "IndieHackers User", "Product Hunt Maker",
                                            "Freelancer Client", "Upwork Freelancer"):
        return IdentityConfidence.LOW.value

    generic_patterns = ["user", "client", "maker", "freelancer"]
    if any(p in person_name.lower() for p in generic_patterns):
        return IdentityConfidence.LOW.value

    # Has a real-looking name
    if role and role not in ("Unknown", "UNKNOWN", ""):
        return IdentityConfidence.HIGH.value

    return IdentityConfidence.MEDIUM.value


def classify_outsourcing_intent(requirement: str, role: str) -> str:
    """Classify whether this person wants to buy or build internally."""
    req_lower = requirement.lower()

    explicit = ["looking for", "need a developer", "need help", "agency",
                "team to build", "external", "outsourc", "freelance", "contract",
                "need someone", "looking for someone", "technical cofounder",
                "looking for agency", "need a team"]
    strong = ["technical cofounder", "need someone", "looking for someone",
              "need engineering", "need a team"]
    hiring = ["hiring", "job posting", "employee", "full-time"]

    explicit_matches = sum(1 for e in explicit if e in req_lower)
    strong_matches = sum(1 for s in strong if s in req_lower)
    hiring_matches = sum(1 for h in hiring if h in req_lower)

    if explicit_matches >= 2:
        return OutsourcingIntent.EXPLICIT_OUTSOURCING.value
    elif strong_matches >= 1:
        return OutsourcingIntent.STRONG_EXTERNAL_SIGNAL.value
    elif hiring_matches > 0:
        return OutsourcingIntent.INTERNAL_HIRING_ONLY.value
    else:
        return OutsourcingIntent.UNKNOWN.value


def classify_prospect_type(person_name: str, role: str, requirement: str, company: str) -> str:
    """Classify whether this is a buyer, service provider, etc."""
    req_lower = requirement.lower()
    role_lower = role.lower() if role else ""
    company_lower = company.lower() if company else ""

    # Service provider signals
    agency_signals = ["agency", "consulting", "development company", "software company",
                      "outsourcing", "freelance platform", "marketplace", "services"]
    if any(s in company_lower for s in agency_signals):
        return ProspectType.SERVICE_PROVIDER.value

    dev_company_signals = ["software dev", "development company", "tech company"]
    if any(s in company_lower for s in dev_company_signals):
        return ProspectType.SOFTWARE_DEV.value

    ai_signals = ["ai company", "ai startup", "machine learning"]
    if any(s in company_lower for s in ai_signals):
        return ProspectType.AI_DEV.value

    freelancer_signals = ["freelancer", "independent", "contractor"]
    if any(s in role_lower for s in freelancer_signals):
        return ProspectType.FREELANCER.value

    job_signals = ["hiring", "looking for a job", "seeking employment"]
    if any(s in req_lower for s in job_signals):
        return ProspectType.JOB_SEEKER.value

    # Buyer signals
    buyer_signals = ["looking for", "need", "build", "develop", "create",
                     "need a team", "looking for agency", "technical cofounder"]
    if any(s in req_lower for s in buyer_signals):
        if "founder" in role_lower or "ceo" in role_lower or "owner" in role_lower:
            return ProspectType.BUYER.value
        return ProspectType.POTENTIAL_BUYER.value

    return ProspectType.UNKNOWN.value


def validate_requirement_text(requirement: str) -> tuple[bool, str]:
    """Check if requirement is specific enough to map to an Inowix service."""
    if not requirement or len(requirement.strip()) < 10:
        return False, "Requirement too short or missing"

    req_lower = requirement.lower()

    # Good signals — specific needs
    good_patterns = [
        "looking for", "need a", "need to", "need help", "need someone",
        "seeking", "build a", "build my", "develop", "create a", "create my",
        "budget", "timeline", "must have", "requirement",
        "technical cofounder", "looking for agency", "looking for team",
        "need a team", "need engineering", "need developers",
        "need a developer", "need an app", "need a website",
        "need a platform", "need a system", "need automation",
        "need a chatbot", "need whatsapp", "need shopify",
        "need saas", "need mvp", "need crm", "need erp",
    ]

    matches = sum(1 for p in good_patterns if p in req_lower)

    # Bad signals — vague or internal
    bad_patterns = [
        "interested in", "we're hiring", "startup launched",
        "raised funding", "looking for talented", "hiring great",
        "join our team", "we are growing", "excited to announce",
    ]
    bad_matches = sum(1 for p in bad_patterns if p in req_lower)

    if matches >= 2:
        return True, f"Specific requirement with {matches} strong signals"
    elif matches >= 1 and bad_matches == 0:
        return True, f"Requirement present with {matches} signal"
    else:
        return False, f"Vague requirement (good={matches}, bad={bad_matches})"


def extract_evidence_from_websearch(
    url: str,
    title: str,
    snippet: str,
    author: str = "",
    date: str = "",
) -> EvidenceRecord:
    """Create an EvidenceRecord from websearch results.

    This is the entry point for converting websearch hits into
    structured evidence records.
    """
    from packages.discovery_engine.source_validator import validate_source_url

    # Validate source URL first
    validation = validate_source_url(url)

    record = EvidenceRecord(
        source_url=url,
        source_platform=validation.platform,
        source_title=title,
        source_author=author,
        published_at=date,
        discovered_at=datetime.now().isoformat(),
        evidence_text=snippet,
        validation_status=validation.status.value,
        rejection_reason=validation.rejection_reason,
    )

    return record


def finalize_evidence(record: EvidenceRecord) -> EvidenceRecord:
    """Apply all classification rules to finalize an evidence record.

    Call this after populating person_name, requirement, etc.
    """
    # Person classification
    record.identity_confidence = classify_person(record.person_name, record.person_role)

    # Outsourcing intent
    record.outsourcing_intent = classify_outsourcing_intent(record.requirement, record.person_role)

    # Prospect type
    record.prospect_type = classify_prospect_type(
        record.person_name, record.person_role, record.requirement, record.company_name
    )

    # Requirement validation
    req_valid, req_note = validate_requirement_text(record.requirement)
    if not req_valid:
        record.evidence_confidence = EvidenceConfidence.LOW.value
        record.notes = f"Requirement issue: {req_note}"
    else:
        # Evidence confidence based on source validation
        if record.validation_status == "VALID":
            record.evidence_confidence = EvidenceConfidence.HIGH.value
        elif record.validation_status == "NEEDS_REVIEW":
            record.evidence_confidence = EvidenceConfidence.MEDIUM.value
        else:
            record.evidence_confidence = EvidenceConfidence.LOW.value

    return record
