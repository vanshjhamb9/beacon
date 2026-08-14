"""Evidence Engine — Every field carries proof.

Core principle: No assumptions. No hallucinations. Everything explainable.

Every field in the system must have:
- value: The actual data
- source: Where it came from
- confidence: 0-1 score
- proof_url: URL proving the claim
- timestamp: When it was detected
- verification_method: How it was verified
- freshness: How recent the data is
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class VerificationMethod(str, Enum):
    """How data was verified."""

    HTTP_200 = "http_200"
    HTML_FINGERPRINT = "html_fingerprint"
    API_RESPONSE = "api_response"
    REGEX_MATCH = "regex_match"
    CROSS_SOURCE = "cross_source"
    MANUAL = "manual"
    DNS_LOOKUP = "dns_lookup"
    SSL_CHECK = "ssl_check"
    SITEMAP_PARSE = "sitemap_parse"
    TECHNOLOGY_SCAN = "technology_scan"
    LINKEDIN_PROFILE = "linkedin_profile"
    GOOGLE_SEARCH = "google_search"
    INSTAGRAM_PROFILE = "instagram_profile"
    FACEBOOK_PAGE = "facebook_page"
    PRESS_MENTION = "press_mention"
    JOB_POSTING = "job_posting"
    FUNDING_ANNOUNCEMENT = "funding_announcement"
    REVIEW_PLATFORM = "review_platform"
    BUSINESS_DIRECTORY = "business_directory"
    CRUNCHBASE = "crunchbase"


class FreshnessTier(str, Enum):
    """Data freshness classification."""

    FRESH = "fresh"          # < 7 days
    RECENT = "recent"        # 7-30 days
    STALE = "stale"          # 30-90 days
    OUTDATED = "outdated"    # > 90 days


@dataclass
class Evidence:
    """Single evidence record for a field value."""

    field_name: str
    field_value: str
    confidence: float  # 0.0 - 1.0
    source: str
    proof_url: str
    timestamp: datetime
    verification_method: VerificationMethod
    freshness_days: int = 0
    raw_data: dict[str, Any] = field(default_factory=dict)

    @property
    def freshness_tier(self) -> FreshnessTier:
        """Classify freshness."""
        if self.freshness_days < 7:
            return FreshnessTier.FRESH
        if self.freshness_days < 30:
            return FreshnessTier.RECENT
        if self.freshness_days < 90:
            return FreshnessTier.STALE
        return FreshnessTier.OUTDATED

    @property
    def is_usable(self) -> bool:
        """Evidence is usable if confidence >= 0.5 and not outdated."""
        return self.confidence >= 0.5 and self.freshness_tier != FreshnessTier.OUTDATED

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "field_value": self.field_value,
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "proof_url": self.proof_url,
            "timestamp": self.timestamp.isoformat(),
            "verification_method": self.verification_method.value,
            "freshness_days": self.freshness_days,
        }


@dataclass
class FieldScore:
    """Aggregated score for a single field across multiple evidence records."""

    field_name: str
    best_value: str
    best_confidence: float
    evidence_count: int
    evidence_records: list[Evidence] = field(default_factory=list)
    last_verified: datetime | None = None
    sources: list[str] = field(default_factory=list)

    @property
    def is_verified(self) -> bool:
        return self.best_confidence >= 0.8

    @property
    def source_diversity(self) -> int:
        return len(set(self.sources))

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "best_value": self.best_value,
            "best_confidence": round(self.best_confidence, 3),
            "evidence_count": self.evidence_count,
            "last_verified": self.last_verified.isoformat() if self.last_verified else None,
            "sources": self.sources,
        }


@dataclass
class CompanyEvidenceProfile:
    """Complete evidence profile for a company."""

    domain: str
    company_name: str
    fields: dict[str, FieldScore] = field(default_factory=dict)
    all_evidence: list[Evidence] = field(default_factory=list)
    discovery_sources: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_evidence(self, evidence: Evidence) -> None:
        """Add an evidence record and update the field score."""
        self.all_evidence.append(evidence)
        self.last_updated = datetime.now(timezone.utc)

        if evidence.field_name not in self.fields:
            self.fields[evidence.field_name] = FieldScore(
                field_name=evidence.field_name,
                best_value=evidence.field_value,
                best_confidence=evidence.confidence,
                evidence_count=1,
                evidence_records=[evidence],
                last_verified=evidence.timestamp,
                sources=[evidence.source],
            )
        else:
            fs = self.fields[evidence.field_name]
            fs.evidence_count += 1
            fs.evidence_records.append(evidence)
            fs.sources.append(evidence.source)
            if evidence.confidence > fs.best_confidence:
                fs.best_value = evidence.field_value
                fs.best_confidence = evidence.confidence
            if evidence.timestamp and (
                fs.last_verified is None or evidence.timestamp > fs.last_verified
            ):
                fs.last_verified = evidence.timestamp

    def get_field(self, field_name: str) -> FieldScore | None:
        return self.fields.get(field_name)

    def get_field_value(self, field_name: str, default: str = "") -> str:
        fs = self.fields.get(field_name)
        return fs.best_value if fs else default

    def get_field_confidence(self, field_name: str) -> float:
        fs = self.fields.get(field_name)
        return fs.best_confidence if fs else 0.0

    def overall_confidence(self) -> float:
        """Calculate overall confidence across all fields."""
        if not self.fields:
            return 0.0
        confidences = [fs.best_confidence for fs in self.fields.values()]
        return sum(confidences) / len(confidences)

    def verified_field_count(self) -> int:
        """Count fields with confidence >= 0.8."""
        return sum(1 for fs in self.fields.values() if fs.is_verified)

    def total_evidence_count(self) -> int:
        return len(self.all_evidence)

    def source_diversity(self) -> int:
        """Count unique sources across all evidence."""
        return len(set(e.source for e in self.all_evidence))

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "company_name": self.company_name,
            "overall_confidence": round(self.overall_confidence(), 3),
            "verified_fields": self.verified_field_count(),
            "total_evidence": self.total_evidence_count(),
            "source_diversity": self.source_diversity(),
            "discovery_sources": self.discovery_sources,
            "fields": {name: fs.to_dict() for name, fs in self.fields.items()},
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }


class EvidenceTracker:
    """Tracks and aggregates evidence across all discovery sources.

    Every field must contain: value, source, confidence, proof_url,
    timestamp, verification_method, freshness.
    """

    def __init__(self) -> None:
        self._profiles: dict[str, CompanyEvidenceProfile] = {}

    def get_or_create_profile(self, domain: str, company_name: str) -> CompanyEvidenceProfile:
        """Get existing profile or create new one."""
        if domain not in self._profiles:
            self._profiles[domain] = CompanyEvidenceProfile(
                domain=domain, company_name=company_name
            )
        return self._profiles[domain]

    def record(
        self,
        domain: str,
        company_name: str,
        field_name: str,
        field_value: str,
        confidence: float,
        source: str,
        proof_url: str,
        verification_method: VerificationMethod,
        raw_data: dict[str, Any] | None = None,
    ) -> Evidence:
        """Record a piece of evidence for a company field."""
        now = datetime.now(timezone.utc)
        evidence = Evidence(
            field_name=field_name,
            field_value=field_value,
            confidence=min(max(confidence, 0.0), 1.0),
            source=source,
            proof_url=proof_url,
            timestamp=now,
            verification_method=verification_method,
            freshness_days=0,
            raw_data=raw_data or {},
        )
        profile = self.get_or_create_profile(domain, company_name)
        profile.add_evidence(evidence)
        if source not in profile.discovery_sources:
            profile.discovery_sources.append(source)
        return evidence

    def get_profile(self, domain: str) -> CompanyEvidenceProfile | None:
        return self._profiles.get(domain)

    def get_all_profiles(self) -> dict[str, CompanyEvidenceProfile]:
        return self._profiles

    def get_sales_ready_profiles(self, min_confidence: float = 0.7) -> list[CompanyEvidenceProfile]:
        """Return profiles that meet minimum confidence threshold."""
        return [
            p for p in self._profiles.values()
            if p.overall_confidence() >= min_confidence
        ]

    def merge_profiles(self, domain: str, other_domain: str) -> CompanyEvidenceProfile | None:
        """Merge evidence from two profiles (e.g., same company, different domains)."""
        primary = self._profiles.get(domain)
        secondary = self._profiles.get(other_domain)
        if not primary or not secondary:
            return primary or secondary

        for evidence in secondary.all_evidence:
            primary.add_evidence(evidence)
        for src in secondary.discovery_sources:
            if src not in primary.discovery_sources:
                primary.discovery_sources.append(src)

        del self._profiles[other_domain]
        return primary

    def decay_stale_evidence(self, decay_days: int = 30) -> int:
        """Mark evidence older than decay_days as stale. Returns count affected."""
        now = datetime.now(timezone.utc)
        count = 0
        for profile in self._profiles.values():
            for evidence in profile.all_evidence:
                age = (now - evidence.timestamp).days
                if age > decay_days:
                    evidence.freshness_days = age
                    count += 1
        return count

    def summary(self) -> dict[str, Any]:
        """Return summary of all tracked evidence."""
        total_profiles = len(self._profiles)
        total_evidence = sum(p.total_evidence_count() for p in self._profiles.values())
        avg_confidence = (
            sum(p.overall_confidence() for p in self._profiles.values()) / total_profiles
            if total_profiles > 0
            else 0.0
        )
        sales_ready = len(self.get_sales_ready_profiles())
        return {
            "total_profiles": total_profiles,
            "total_evidence": total_evidence,
            "avg_confidence": round(avg_confidence, 3),
            "sales_ready_count": sales_ready,
        }
