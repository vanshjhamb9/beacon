"""ARIE: Main Orchestrator.

Ties all ARIE engines together into a unified pipeline.
This is the entry point for the AI Revenue Intelligence Engine.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .arie_icp_engine import ARIEICPEngine, ICPMatchResult, ICPProfileData
from .arie_growth_engine import ARIEGrowthEngine, GrowthAnalysis
from .arie_intent_engine import ARIEIntentEngine, IntentAnalysis
from .arie_revenue_engine import ARIERevenueEngine, RevenueScoreResult
from .arie_verification_engine import ARIEVERificationEngine, VerifiedContact
from .arie_quality_engine import ARIEQualityEngine, QualityReport
from .arie_sales_copilot import ARIESalesCopilot, SalesPackage

logger = logging.getLogger(__name__)


@dataclass
class ARIEResult:
    """Complete ARIE analysis result for a company."""
    domain: str
    company_name: str
    
    # ICP Matching
    icp_match: ICPMatchResult = None
    matched_icp: str = ""
    
    # Growth Analysis
    growth_analysis: GrowthAnalysis = None
    
    # Intent Analysis
    intent_analysis: IntentAnalysis = None
    
    # Revenue Scoring
    revenue_score: RevenueScoreResult = None
    
    # Contact Verification
    verified_contacts: VerifiedContact = None
    
    # Quality Assessment
    quality_report: QualityReport = None
    
    # Sales Copilot
    sales_package: SalesPackage = None
    
    # Overall
    final_classification: str = "UNSCORED"  # HOT, WARM, COLD, REJECTED, UNSCORED
    overall_score: float = 0.0
    confidence: float = 0.0
    
    # Metadata
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    analysis_duration_ms: float = 0.0
    engines_used: list = field(default_factory=list)
    errors: list = field(default_factory=list)


def _deep_to_dict(obj):
    """Recursively convert dataclass/dict/list to plain dicts."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _deep_to_dict(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, dict):
        return {k: _deep_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_deep_to_dict(item) for item in obj]
    return obj


class ARIEOrchestrator:
    """ARIE Main Orchestrator - ties all engines together.
    
    Usage:
        orchestrator = ARIEOrchestrator()
        result = orchestrator.analyze_company(company_data, icp_profiles)
    """
    
    def __init__(self):
        self.icp_engine = ARIEICPEngine()
        self.growth_engine = ARIEGrowthEngine()
        self.intent_engine = ARIEIntentEngine()
        self.revenue_engine = ARIERevenueEngine()
        self.verification_engine = ARIEVERificationEngine()
        self.quality_engine = ARIEQualityEngine()
        self.sales_copilot = ARIESalesCopilot()
    
    def analyze_company(
        self,
        company_data: dict[str, Any],
        icp_profiles: list[ICPProfileData] = None,
        contact_data: dict[str, Any] = None,
    ) -> ARIEResult:
        """Perform complete ARIE analysis for a company.
        
        Args:
            company_data: Company information
            icp_profiles: List of ICP profiles to match against
            contact_data: Contact information
            
        Returns:
            ARIEResult with complete analysis
        """
        start_time = datetime.utcnow()
        domain = company_data.get("domain", "")
        company_name = company_data.get("company_name", company_data.get("name", ""))
        
        result = ARIEResult(
            domain=domain,
            company_name=company_name,
        )
        
        try:
            # Step 1: ICP Matching (the brain)
            if icp_profiles:
                best_match = None
                best_score = -1
                
                for icp in icp_profiles:
                    match = self.icp_engine.match_company_against_icp(company_data, icp)
                    if match.icp_score > best_score:
                        best_score = match.icp_score
                        best_match = match
                        result.matched_icp = icp.name
                
                result.icp_match = best_match
                
                # Check if rejected
                if best_match and best_match.classified_as == "REJECTED":
                    result.final_classification = "REJECTED"
                    result.overall_score = 0.0
                    result.errors.append(f"Rejected: {best_match.negative_reason}")
                    return result
            
            # Step 2: Growth Analysis
            result.growth_analysis = self.growth_engine.analyze_growth(company_data)
            result.engines_used.append("growth")
            
            # Step 3: Intent Analysis
            result.intent_analysis = self.intent_engine.analyze_intent(company_data)
            result.engines_used.append("intent")
            
            # Step 4: Contact Verification
            if contact_data:
                result.verified_contacts = self.verification_engine.verify_contact(
                    contact_data, company_data
                )
                result.engines_used.append("verification")
            
            # Step 5: Quality Assessment
            result.quality_report = self.quality_engine.run_quality_checks(
                company_data, contact_data
            )
            result.engines_used.append("quality")
            
            # Step 6: Revenue Scoring
            result.revenue_score = self.revenue_engine.calculate_revenue_score(
                company_data=company_data,
                icp_match=_deep_to_dict(result.icp_match) if result.icp_match else None,
                growth_analysis=_deep_to_dict(result.growth_analysis) if result.growth_analysis else None,
                intent_analysis=_deep_to_dict(result.intent_analysis) if result.intent_analysis else None,
                decision_makers=company_data.get("decision_makers", []),
                contact_data=contact_data,
            )
            result.engines_used.append("revenue")
            
            # Step 7: Sales Copilot (only for qualified leads)
            if result.revenue_score.classification in ["HOT", "WARM"]:
                result.sales_package = self.sales_copilot.generate_sales_package(
                    company_data=company_data,
                    revenue_score=_deep_to_dict(result.revenue_score),
                    pain_analysis={"pain_points": []},  # Would come from pain engine
                    technology_analysis={},  # Would come from tech engine
                    growth_analysis=_deep_to_dict(result.growth_analysis) if result.growth_analysis else {},
                    intent_analysis=_deep_to_dict(result.intent_analysis) if result.intent_analysis else {},
                    decision_makers=company_data.get("decision_makers", []),
                    verified_contacts=_deep_to_dict(result.verified_contacts) if result.verified_contacts else {},
                )
                result.engines_used.append("copilot")
            
            # Step 8: Final Classification
            result.final_classification = self._determine_final_classification(result)
            result.overall_score = result.revenue_score.overall_score if result.revenue_score else 0.0
            result.confidence = result.revenue_score.overall_confidence if result.revenue_score else 0.0
            
        except Exception as e:
            logger.error(f"Error analyzing {domain}: {e}")
            result.errors.append(str(e))
        
        # Calculate duration
        end_time = datetime.utcnow()
        result.analysis_duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return result
    
    def _determine_final_classification(self, result: ARIEResult) -> str:
        """Determine final classification based on all analyses."""
        # Check quality first
        if result.quality_report and not result.quality_report.is_qualified:
            return "REJECTED"
        
        # Check ICP match
        if result.icp_match and result.icp_match.classified_as == "REJECTED":
            return "REJECTED"
        
        # Use revenue score classification
        if result.revenue_score:
            return result.revenue_score.classification
        
        return "UNSCORED"
    
    def batch_analyze(
        self,
        companies: list[dict[str, Any]],
        icp_profiles: list[ICPProfileData] = None,
        max_workers: int = 5,
    ) -> list[ARIEResult]:
        """Analyze multiple companies.
        
        Args:
            companies: List of company data dicts
            icp_profiles: ICP profiles to match against
            max_workers: Maximum concurrent workers
            
        Returns:
            List of ARIEResult
        """
        results = []
        
        for company in companies:
            result = self.analyze_company(company, icp_profiles)
            results.append(result)
        
        return results
    
    def get_summary(self, results: list[ARIEResult]) -> dict:
        """Get summary of batch analysis."""
        total = len(results)
        hot = sum(1 for r in results if r.final_classification == "HOT")
        warm = sum(1 for r in results if r.final_classification == "WARM")
        cold = sum(1 for r in results if r.final_classification == "COLD")
        rejected = sum(1 for r in results if r.final_classification == "REJECTED")
        unscored = sum(1 for r in results if r.final_classification == "UNSCORED")
        
        avg_score = sum(r.overall_score for r in results) / total if total > 0 else 0
        avg_confidence = sum(r.confidence for r in results) / total if total > 0 else 0
        
        return {
            "total": total,
            "hot": hot,
            "warm": warm,
            "cold": cold,
            "rejected": rejected,
            "unscored": unscored,
            "avg_score": avg_score,
            "avg_confidence": avg_confidence,
            "qualified": hot + warm,
            "qualification_rate": ((hot + warm) / total * 100) if total > 0 else 0,
        }
