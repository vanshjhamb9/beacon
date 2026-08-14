"""Opportunity Intelligence Platform foundation."""

try:
    from packages.opportunity_intelligence.constants import SCORING_VERSION
    from packages.opportunity_intelligence.models import Opportunity, OpportunityEvidence, OpportunityScoreRecord
    from packages.opportunity_intelligence.opportunity_builder import OpportunityBuilder
except ImportError:
    SCORING_VERSION = "1.0.0"
    Opportunity = None  # type: ignore
    OpportunityEvidence = None  # type: ignore
    OpportunityScoreRecord = None  # type: ignore
    OpportunityBuilder = None  # type: ignore

__all__ = [
    "Opportunity",
    "OpportunityBuilder",
    "OpportunityEvidence",
    "OpportunityScoreRecord",
    "SCORING_VERSION",
]
