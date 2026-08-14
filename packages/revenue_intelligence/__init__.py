"""Revenue Intelligence Engine for COMAI.

Deterministic intelligence layer that sits after Ecommerce Discovery.
Scores companies for purchase probability, pain, growth, and ICP fit.
"""

from packages.revenue_intelligence.models import CompanyIntelligence
from packages.revenue_intelligence.services.pipeline import RevenueIntelligencePipeline

__all__ = ["CompanyIntelligence", "RevenueIntelligencePipeline"]
