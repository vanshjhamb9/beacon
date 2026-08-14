"""COMAI Intelligence — Vertical AI Revenue Intelligence Platform.

Transforms Beacon from a lead scraper into the intelligence brain for COMAI.
Every engine optimizes for one objective: find ecommerce companies highly likely
to purchase COMAI within 30-180 days.
"""

from packages.comai_intelligence.product_profile import COMAIProductCatalog
from packages.comai_intelligence.icp_engine import ICPEngine
from packages.comai_intelligence.evidence_tracker import EvidenceTracker
from packages.comai_intelligence.pain_engine import PainIntelligenceEngine
from packages.comai_intelligence.intent_engine import BuyingIntentEngine
from packages.comai_intelligence.decision_maker_engine import DecisionMakerEngine
from packages.comai_intelligence.tech_detection import COMAITechDetector
from packages.comai_intelligence.revenue_scorer import RevenueOpportunityScorer
from packages.comai_intelligence.close_probability import CloseProbabilityCalculator
from packages.comai_intelligence.qualification_pipeline import QualificationPipeline
from packages.comai_intelligence.output_formatter import SalesReadyOutputFormatter

__all__ = [
    "COMAIProductCatalog",
    "ICPEngine",
    "EvidenceTracker",
    "PainIntelligenceEngine",
    "BuyingIntentEngine",
    "DecisionMakerEngine",
    "COMAITechDetector",
    "RevenueOpportunityScorer",
    "CloseProbabilityCalculator",
    "QualificationPipeline",
    "SalesReadyOutputFormatter",
]
