"""Beacon Alpha — Revenue Dataset Perfection. Data quality only."""

from beacon_alpha.acceptance.engine import AlphaAcceptanceEngine
from beacon_alpha.admission.engine import ColdEmailAdmissionEngine
from beacon_alpha.contact_enrichment.engine import ContactEnrichmentEngine
from beacon_alpha.dedupe.engine import AlphaDedupeEngine
from beacon_alpha.founder_queue.engine import FounderQueueEngine, TOP_N
from beacon_alpha.identity_gate.engine import IdentityGateEngine
from beacon_alpha.intent_v2.engine import IntentV2Engine
from beacon_alpha.manual_qa.engine import ManualQaEngine
from beacon_alpha.models.types import (
    AdmissionResult,
    AlphaAcceptance,
    AlphaSnapshot,
    AlphaVerdict,
    AttributedValue,
    CompanyScore,
    ContactEnrichmentResult,
    DedupeResult,
    FounderQueueCard,
    IdentityGateResult,
    IntentV2Result,
    ManualQaCard,
    ManualQaDecision,
    QaRating,
    ServiceBucket,
    SourceTransparency,
    UNKNOWN,
)
from beacon_alpha.pipelines.engine import BeaconAlphaPipeline
from beacon_alpha.scoring.engine import CompanyScoringEngine, FOUNDER_THRESHOLD
from beacon_alpha.transparency.engine import SourceTransparencyEngine

__all__ = [
    "TOP_N",
    "FOUNDER_THRESHOLD",
    "AdmissionResult",
    "AlphaAcceptance",
    "AlphaAcceptanceEngine",
    "AlphaDedupeEngine",
    "AlphaSnapshot",
    "AlphaVerdict",
    "AttributedValue",
    "BeaconAlphaPipeline",
    "ColdEmailAdmissionEngine",
    "CompanyScore",
    "CompanyScoringEngine",
    "ContactEnrichmentEngine",
    "ContactEnrichmentResult",
    "DedupeResult",
    "FounderQueueCard",
    "FounderQueueEngine",
    "IdentityGateEngine",
    "IdentityGateResult",
    "IntentV2Engine",
    "IntentV2Result",
    "ManualQaCard",
    "ManualQaDecision",
    "ManualQaEngine",
    "QaRating",
    "ServiceBucket",
    "SourceTransparency",
    "SourceTransparencyEngine",
    "UNKNOWN",
]

SCORING_VERSION = "alpha-v1"
LIVE_OUTREACH_ENABLED = False  # locked until AlphaAcceptanceEngine says ready
