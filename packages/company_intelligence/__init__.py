"""Company Intelligence Reconstruction (CIR v1) — evidence-only company understanding.

Verified Company → Website Understanding → Business → ICP → Technology → Buying Signals
→ Service Match → Narrative → Contacts → Revenue Readiness → Founder Card.
No GPT. No fabrication. UNKNOWN when unavailable. Every field attributed.
"""

from company_intelligence.buying_signals.engine import BuyingSignalEngine
from company_intelligence.company_understanding.engine import CompanyUnderstandingEngine
from company_intelligence.contact_recovery.engine import ContactRecoveryEngine
from company_intelligence.founder_card.engine import FounderIntelligenceCardEngine
from company_intelligence.founder_queue.engine import CirFounderQueueEngine
from company_intelligence.icp_detection.engine import IcpDetectionEngine
from company_intelligence.models.types import (
    UNKNOWN,
    AttributedValue,
    BuyingSignal,
    CirClassification,
    CirSnapshot,
    CirVerdict,
    CompanyBusinessProfile,
    ContactPerson,
    FounderIntelligenceCard,
    IcpProfile,
    OpportunityNarrative,
    ProductCatalog,
    RevenueReadinessScore,
    ServiceMatch,
    TechnologyHit,
    WebsiteCorpus,
)
from company_intelligence.opportunity_narrative.engine import OpportunityNarrativeEngine
from company_intelligence.pipelines.engine import CirPipeline
from company_intelligence.product_intelligence.engine import ProductIntelligenceEngine
from company_intelligence.rebuild.engine import CirRebuildEngine
from company_intelligence.revenue_readiness.engine import RevenueReadinessEngine
from company_intelligence.service_match.engine import ServiceMatchEngineV3
from company_intelligence.technology_intelligence.engine import TechnologyIntelligenceEngine
from company_intelligence.website_understanding.engine import WebsiteUnderstandingEngine

SCORING_VERSION = "cir-v1"
LIVE_OUTREACH_ENABLED = False
REQUIRES_EROWD_ADMITTED = True
FOUNDER_QUEUE_CLASSIFICATIONS = frozenset(
    {CirClassification.REVENUE_READY, CirClassification.PRIORITY_ACCOUNT}
)

__all__ = [
    "UNKNOWN",
    "AttributedValue",
    "BuyingSignal",
    "BuyingSignalEngine",
    "CirClassification",
    "CirFounderQueueEngine",
    "CirPipeline",
    "CirRebuildEngine",
    "CirSnapshot",
    "CirVerdict",
    "CompanyBusinessProfile",
    "CompanyUnderstandingEngine",
    "ContactPerson",
    "ContactRecoveryEngine",
    "FOUNDER_QUEUE_CLASSIFICATIONS",
    "FounderIntelligenceCard",
    "FounderIntelligenceCardEngine",
    "IcpDetectionEngine",
    "IcpProfile",
    "LIVE_OUTREACH_ENABLED",
    "OpportunityNarrative",
    "OpportunityNarrativeEngine",
    "ProductCatalog",
    "ProductIntelligenceEngine",
    "REQUIRES_EROWD_ADMITTED",
    "RevenueReadinessEngine",
    "RevenueReadinessScore",
    "SCORING_VERSION",
    "ServiceMatch",
    "ServiceMatchEngineV3",
    "TechnologyHit",
    "TechnologyIntelligenceEngine",
    "WebsiteCorpus",
    "WebsiteUnderstandingEngine",
]
