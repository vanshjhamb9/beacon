"""Sales Intelligence & Decision Maker Platform (SIDP).

Transforms Revenue Ready companies into Outreach Ready Accounts.
Answers: WHO should I contact, WHY, and HOW can I reach them?
"""

from packages.sales_intelligence_platform.models import (
    Account,
    AccountHealth,
    AccountScore,
    BuyingCommittee,
    ContactChannel,
    DecisionMaker,
    EvidenceRecord,
)
from packages.sales_intelligence_platform.engines.account_builder import build_account
from packages.sales_intelligence_platform.engines.web_scraper import WebScraper
from packages.sales_intelligence_platform.engines.technology_detector import TechnologyDetector
from packages.sales_intelligence_platform.engines.pain_point_detector import PainPointDetector
from packages.sales_intelligence_platform.engines.comai_opportunity_score import COMAIOpportunityScorer
from packages.sales_intelligence_platform.engines.sales_intel_summary import SalesIntelligenceGenerator
from packages.sales_intelligence_platform.engines.call_preparation import CallPreparationGenerator

__all__ = [
    "Account",
    "BuyingCommittee",
    "ContactChannel",
    "DecisionMaker",
    "EvidenceRecord",
    "AccountHealth",
    "AccountScore",
    "build_account",
    "WebScraper",
    "TechnologyDetector",
    "PainPointDetector",
    "COMAIOpportunityScorer",
    "SalesIntelligenceGenerator",
    "CallPreparationGenerator",
]
