"""Sales Readiness Engine (SRE v1) — convert opportunities into sales-ready accounts."""

from sales_readiness.classification.engine import SalesReadinessClassifier
from sales_readiness.contacts.engine import ContactCompletenessEngine
from sales_readiness.identity.engine import IdentityCompletenessEngine
from sales_readiness.intent.engine import BuyingIntentEngine
from sales_readiness.models.types import (
    AttributedField,
    BuyingIntentLevel,
    DealSizeBand,
    OutreachReadinessStatus,
    SalesReadinessStatus,
    SalesReadinessSnapshot,
    WebsiteGrade,
)
from sales_readiness.outreach.engine import OutreachReadinessEngine
from sales_readiness.revenue.engine import RevenuePotentialEngine
from sales_readiness.service_match.engine import ServiceMatchingEngineV2
from sales_readiness.technology.engine import TechnologyReadinessEngine
from sales_readiness.trust.engine import SalesTrustEngine
from sales_readiness.website.engine import WebsiteIntelligenceEngine

__all__ = [
    "AttributedField",
    "BuyingIntentEngine",
    "BuyingIntentLevel",
    "ContactCompletenessEngine",
    "DealSizeBand",
    "IdentityCompletenessEngine",
    "OutreachReadinessEngine",
    "OutreachReadinessStatus",
    "RevenuePotentialEngine",
    "SalesReadinessClassifier",
    "SalesReadinessSnapshot",
    "SalesReadinessStatus",
    "SalesTrustEngine",
    "ServiceMatchingEngineV2",
    "TechnologyReadinessEngine",
    "WebsiteGrade",
    "WebsiteIntelligenceEngine",
]

SCORING_VERSION = "sre-v1"
FOUNDER_QUEUE_STATUSES = frozenset(
    {
        SalesReadinessStatus.CONTACT_READY,
        SalesReadinessStatus.SALES_READY,
        SalesReadinessStatus.ENTERPRISE_READY,
    }
)
REVENUE_HUNTER_STATUSES = frozenset(
    {
        SalesReadinessStatus.SALES_READY,
        SalesReadinessStatus.ENTERPRISE_READY,
    }
)
UNKNOWN = "UNKNOWN"
