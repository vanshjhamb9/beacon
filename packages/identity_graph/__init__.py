"""Identity Graph Foundation (igf-v1) — companies exist only after Identity Graph admits them.

Compose-only with EROWD website discovery. Never fabricate domains, emails, or people.
North star: increase Revenue Ready companies with attributed identity.
"""

from identity_graph.models.types import (
    UNKNOWN,
    SCORING_VERSION,
    CanonicalCompany,
    CanonicalStatus,
    IdentityCandidate,
    IdentityEvidence,
    IdentityScore,
    IgfAdmission,
    IgfFunnelMetrics,
    IgfSnapshot,
    IgfVerdict,
    MergeResult,
    RejectionReason,
    SourceRole,
)
from identity_graph.pipelines.engine import IdentityResolutionPipeline
from identity_graph.rebuild.engine import IgfRebuildEngine
from identity_graph.source_roles.engine import SourceRoleEngine

__all__ = [
    "UNKNOWN",
    "SCORING_VERSION",
    "CanonicalCompany",
    "CanonicalStatus",
    "IdentityCandidate",
    "IdentityEvidence",
    "IdentityResolutionPipeline",
    "IdentityScore",
    "IgfAdmission",
    "IgfFunnelMetrics",
    "IgfRebuildEngine",
    "IgfSnapshot",
    "IgfVerdict",
    "MergeResult",
    "RejectionReason",
    "SourceRole",
    "SourceRoleEngine",
]
