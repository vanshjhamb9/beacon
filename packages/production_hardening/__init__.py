"""Production Hardening (PH-1) — evidence-first revenue readiness."""

from production_hardening.admission.engine import OpportunityAdmissionGate
from production_hardening.dedupe.engine import DuplicateResolutionEngine
from production_hardening.identity.engine import CompanyIdentityValidator
from production_hardening.models.types import (
    AdmissionDecision,
    ContactReadiness,
    ContactReadinessStatus,
    IdentityReport,
    LeadQualityScore,
    TrustMetrics,
)
from production_hardening.readiness.engine import ContactReadinessEngine
from production_hardening.scoring.engine import LeadQualityScorer
from production_hardening.trust.engine import TrustMetricsEngine

__all__ = [
    "AdmissionDecision",
    "CompanyIdentityValidator",
    "ContactReadiness",
    "ContactReadinessEngine",
    "ContactReadinessStatus",
    "DuplicateResolutionEngine",
    "IdentityReport",
    "LeadQualityScore",
    "LeadQualityScorer",
    "OpportunityAdmissionGate",
    "TrustMetrics",
    "TrustMetricsEngine",
]

SCORING_VERSION = "ph1-v1"
IDENTITY_CONFIDENCE_THRESHOLD = 55.0
LEAD_QUALITY_HIDE_THRESHOLD = 70.0
