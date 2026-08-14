"""Company Resolution Engine (CRE v1) — Signal → Evidence → Identity → Verification → Company."""

from company_resolution.admission.engine import CreAdmissionEngine
from company_resolution.identity_confidence.engine import IDENTITY_THRESHOLD, IdentityConfidenceEngine
from company_resolution.models.types import (
    UNKNOWN,
    CreAdmission,
    CreRebuildReport,
    CreSnapshot,
    CreVerdict,
    IdentityConfidence,
    OrganizationCandidate,
    RawSignalEnvelope,
    RejectionReason,
    SourceAttribution,
    WebsiteValidation,
)
from company_resolution.organization_resolver.engine import OrganizationResolverEngine
from company_resolution.pipelines.engine import CompanyResolutionPipeline
from company_resolution.rebuild.engine import CreRebuildEngine
from company_resolution.source_attribution.engine import SourceAttributionEngine
from company_resolution.website_validator.engine import WebsiteValidatorEngine

__all__ = [
    "IDENTITY_THRESHOLD",
    "CompanyResolutionPipeline",
    "CreAdmission",
    "CreAdmissionEngine",
    "CreRebuildEngine",
    "CreRebuildReport",
    "CreSnapshot",
    "CreVerdict",
    "IdentityConfidence",
    "IdentityConfidenceEngine",
    "OrganizationCandidate",
    "OrganizationResolverEngine",
    "RawSignalEnvelope",
    "RejectionReason",
    "SourceAttribution",
    "SourceAttributionEngine",
    "WebsiteValidation",
    "WebsiteValidatorEngine",
    "UNKNOWN",
]

SCORING_VERSION = "cre-v1"
LIVE_OUTREACH_ENABLED = False
COMPANY_CREATE_REQUIRES_CRE = True
