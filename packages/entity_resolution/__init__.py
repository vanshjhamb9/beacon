"""Entity Resolution & Official Website Discovery (EROWD v1).

Signal → Entity Resolution → Official Website Discovery → Identity Verification → Company.
A company without an official website is NOT a company — it remains a signal.
Never guess, fabricate, autocomplete, or infer domains.
"""

from entity_resolution.canonical_identity.engine import CanonicalIdentityEngine
from entity_resolution.domain_validator.engine import OfficialDomainValidator
from entity_resolution.entity_resolver.engine import EntityResolverEngine
from entity_resolution.evidence_graph.engine import EvidenceGraphEngine
from entity_resolution.identity_confidence.engine import IDENTITY_THRESHOLD, ErowdIdentityConfidenceEngine
from entity_resolution.models.types import (
    UNKNOWN,
    CanonicalIdentity,
    DomainValidation,
    EntityCandidate,
    ErowdAdmission,
    ErowdRebuildReport,
    ErowdSnapshot,
    ErowdVerdict,
    EvidenceEdge,
    IdentityScore,
    OfficialWebsite,
    RejectionReason,
    WebsiteAttribution,
)
from entity_resolution.pipelines.engine import ErowdPipeline
from entity_resolution.rebuild.engine import ErowdRebuildEngine
from entity_resolution.website_attribution.engine import WebsiteAttributionEngine
from entity_resolution.website_discovery.engine import OfficialWebsiteDiscoveryEngine

__all__ = [
    "IDENTITY_THRESHOLD",
    "CanonicalIdentity",
    "CanonicalIdentityEngine",
    "DomainValidation",
    "EntityCandidate",
    "EntityResolverEngine",
    "ErowdAdmission",
    "ErowdIdentityConfidenceEngine",
    "ErowdPipeline",
    "ErowdRebuildEngine",
    "ErowdRebuildReport",
    "ErowdSnapshot",
    "ErowdVerdict",
    "EvidenceEdge",
    "EvidenceGraphEngine",
    "IdentityScore",
    "OfficialDomainValidator",
    "OfficialWebsite",
    "OfficialWebsiteDiscoveryEngine",
    "RejectionReason",
    "WebsiteAttribution",
    "WebsiteAttributionEngine",
    "UNKNOWN",
]

SCORING_VERSION = "erowd-v1"
LIVE_OUTREACH_ENABLED = False
COMPANY_REQUIRES_OFFICIAL_WEBSITE = True
