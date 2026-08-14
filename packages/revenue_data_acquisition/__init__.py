"""Revenue Data Acquisition Platform (rdap-v1) — improve incoming data quality only.

Compose-only with ICE / IGF / EROWD. North star: new companies entering Revenue Ready pipeline.
"""

from revenue_data_acquisition.models.types import (
    UNKNOWN,
    SCORING_VERSION,
    CompanyDossier,
    ConnectorGrade,
    ConnectorScore,
    RdapAudit,
    RdapSnapshot,
    RecoveryReason,
    RevenueYield,
    SourceClass,
)
from revenue_data_acquisition.pipelines.engine import RevenueDataAcquisitionPipeline
from revenue_data_acquisition.rebuild.engine import RdapRebuildEngine

__all__ = [
    "UNKNOWN",
    "SCORING_VERSION",
    "CompanyDossier",
    "ConnectorGrade",
    "ConnectorScore",
    "RdapAudit",
    "RdapSnapshot",
    "RecoveryReason",
    "RevenueDataAcquisitionPipeline",
    "RdapRebuildEngine",
    "RevenueYield",
    "SourceClass",
]
