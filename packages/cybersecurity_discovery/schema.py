"""Canonical opportunity schema for the cybersecurity lane."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class OpportunityType(StrEnum):
    DIRECT_SECURITY_CLIENT = "DIRECT_SECURITY_CLIENT"
    SECURITY_COMPLIANCE_CLIENT = "SECURITY_COMPLIANCE_CLIENT"
    SECURITY_REMEDIATION_CLIENT = "SECURITY_REMEDIATION_CLIENT"
    SECURITY_TESTING_CLIENT = "SECURITY_TESTING_CLIENT"
    SECURITY_CONTRACTOR_CLIENT = "SECURITY_CONTRACTOR_CLIENT"
    SECURITY_PARTNER = "SECURITY_PARTNER"
    REJECT = "REJECT"


class IntentLevel(StrEnum):
    HOT = "HOT"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class Currentness(StrEnum):
    HOT = "HOT"
    CURRENT = "CURRENT"
    AGING = "AGING"
    STALE = "STALE"
    REJECT = "REJECT"


class EmailStatus(StrEnum):
    VERIFIED = "VERIFIED"
    PUBLIC_UNVERIFIED = "PUBLIC_UNVERIFIED"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"


class FinalVerdict(StrEnum):
    SALES_READY = "SALES_READY"
    NEEDS_RESEARCH = "NEEDS_RESEARCH"
    REJECT = "REJECT"


class OutsourcingIntent(StrEnum):
    EXPLICIT = "EXPLICIT"
    HIGH = "HIGH"
    IMPLICIT = "IMPLICIT"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"


INOWIX_CYBER_SERVICES = (
    "Web Application VAPT",
    "API Security Testing",
    "Mobile Application Security Testing",
    "Infrastructure Security Assessment",
    "Vulnerability Assessment",
    "Penetration Testing",
    "Security Audit",
    "Security Hardening",
    "Vulnerability Remediation",
    "Secure Code Review",
    "Cloud Security Assessment",
    "Compliance Security Testing",
    "Pre-launch Security Assessment",
    "Continuous Security Testing",
)

DECISION_MAKER_ROLES = (
    "CTO",
    "Founder",
    "Co-Founder",
    "CISO",
    "Head of Security",
    "VP Engineering",
    "Head of Engineering",
    "Technical Director",
    "IT Director",
    "Engineering Manager",
)


def utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def evidence_item(
    claim: str,
    value: Any,
    source: str,
    source_url: str,
    confidence: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    return {
        "claim": claim,
        "value": value,
        "source": source,
        "source_url": source_url,
        "confidence": confidence,
        "observed_at": observed_at or utc_now_iso(),
    }


@dataclass
class RawDiscovery:
    """A single public post/listing before qualification."""

    source_name: str
    source_url: str
    title: str
    body: str
    published_at: str | None = None
    author: str | None = None
    author_profile_url: str | None = None
    company_hint: str | None = None
    company_url_hint: str | None = None
    country_hint: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return f"{self.title}\n{self.body}".strip()


@dataclass
class CyberOpportunity:
    """Fully qualified cybersecurity opportunity (directive section 12)."""

    opportunity_id: str
    company: str | None = None
    company_url: str | None = None
    country: str | None = None
    industry: str | None = None
    buyer_name: str | None = None
    buyer_role: str | None = None
    buyer_profile_url: str | None = None
    identity_confidence: str = "UNKNOWN"
    buying_event: str | None = None
    problem: str | None = None
    why_now: str | None = None
    intent_level: str = IntentLevel.UNKNOWN.value
    requirement_evidence: list[dict[str, Any]] = field(default_factory=list)
    source_name: str = ""
    source_url: str = ""
    source_status: str = "UNVERIFIED"
    published_at: str | None = None
    observed_at: str = field(default_factory=utc_now_iso)
    security_problem: str | None = None
    security_problem_evidence: list[dict[str, Any]] = field(default_factory=list)
    outsourcing_intent: str = OutsourcingIntent.UNKNOWN.value
    outsourcing_evidence: list[dict[str, Any]] = field(default_factory=list)
    service_match: str | None = None
    service_match_reason: str | None = None
    service_match_confidence: str = "LOW"
    email: str | None = None
    email_status: str = EmailStatus.UNKNOWN.value
    email_evidence: list[dict[str, Any]] = field(default_factory=list)
    linkedin_url: str | None = None
    linkedin_status: str = "UNKNOWN"
    contactability: str = "NONE"
    contactability_evidence: list[dict[str, Any]] = field(default_factory=list)
    currentness: str = Currentness.REJECT.value
    currentness_evidence: list[dict[str, Any]] = field(default_factory=list)
    competitor: bool = False
    safety_clear: bool = True
    opportunity_type: str = OpportunityType.REJECT.value
    outreach_priority: str | None = None
    cto_15_minute_test: str = "NO"
    cto_decision_reason: str = ""
    failed_gates: list[str] = field(default_factory=list)
    company_verified: bool = False
    requirement_verified: bool = False
    buying_event_verified: bool = False
    final_verdict: str = FinalVerdict.REJECT.value
    rejection_reason: str | None = None
    title: str = ""
    body_snippet: str = ""
    funnel_stage: str = "DISCOVERED"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
