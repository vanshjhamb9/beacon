"""Quality Gate for Opportunity Qualification."""

from __future__ import annotations

import logging
from typing import Any
from dataclasses import dataclass, field

from packages.enrichment.opportunity_enrichment import EnrichedOpportunity

logger = logging.getLogger(__name__)


@dataclass
class QualificationResult:
    """Result of opportunity qualification."""
    
    qualified: bool
    status: str  # QUALIFIED, REJECTED, PENDING
    
    # Criteria
    requirement_evidence: bool
    person_verification: bool
    company_verification: bool
    service_match: bool
    outsourcing_fit: bool
    recency: bool
    
    # Rejection reasons
    rejection_reasons: list[str]
    
    # Qualification score
    qualification_score: float
    
    # Recommendations
    recommendations: list[str]


class OpportunityQualifier:
    """Qualifies opportunities based on CTO directive criteria."""
    
    def __init__(self):
        # Recency thresholds (in days)
        self.VERY_HIGH_RECENCY = 7
        self.HIGH_RECENCY = 30
        self.MEDIUM_RECENCY = 90
    
    def qualify(self, opportunity: EnrichedOpportunity) -> QualificationResult:
        """Qualify an opportunity based on CTO directive criteria."""
        
        rejection_reasons = []
        recommendations = []
        
        # 1. Requirement Evidence (Required)
        requirement_evidence = self._check_requirement_evidence(opportunity)
        if not requirement_evidence:
            rejection_reasons.append("No explicit requirement evidence")
        
        # 2. Person Verification (Required)
        person_verification = self._check_person_verification(opportunity)
        if not person_verification:
            rejection_reasons.append("Person not verified")
            recommendations.append("Search for LinkedIn profile")
        
        # 3. Company Verification (Required)
        company_verification = self._check_company_verification(opportunity)
        if not company_verification:
            rejection_reasons.append("Company not verified")
            recommendations.append("Search for company website")
        
        # 4. Service Match (Required)
        service_match = self._check_service_match(opportunity)
        if not service_match:
            rejection_reasons.append("No service match")
        
        # 5. Outsourcing Fit (Required)
        outsourcing_fit = self._check_outsourcing_fit(opportunity)
        if not outsourcing_fit:
            rejection_reasons.append("Low outsourcing fit")
        
        # 6. Recency (Required)
        recency = self._check_recency(opportunity)
        if not recency:
            rejection_reasons.append("Evidence too old")
            recommendations.append("Find more recent evidence")
        
        # Calculate qualification score
        qualification_score = self._calculate_qualification_score(
            requirement_evidence, person_verification, company_verification,
            service_match, outsourcing_fit, recency, opportunity
        )
        
        # Determine status
        qualified = len(rejection_reasons) == 0
        status = "QUALIFIED" if qualified else "REJECTED"
        
        # Add recommendations
        if not qualified:
            recommendations.append("Review and address rejection reasons")
        
        return QualificationResult(
            qualified=qualified,
            status=status,
            requirement_evidence=requirement_evidence,
            person_verification=person_verification,
            company_verification=company_verification,
            service_match=service_match,
            outsourcing_fit=outsourcing_fit,
            recency=recency,
            rejection_reasons=rejection_reasons,
            qualification_score=qualification_score,
            recommendations=recommendations
        )
    
    def _check_requirement_evidence(self, opportunity: EnrichedOpportunity) -> bool:
        """Check if requirement evidence exists."""
        return bool(opportunity.exact_requirement and len(opportunity.exact_requirement) > 20)
    
    def _check_person_verification(self, opportunity: EnrichedOpportunity) -> bool:
        """Check if person is verified."""
        return bool(
            opportunity.person_name and
            opportunity.person_name != "Unknown" and
            opportunity.linkedin_url
        )
    
    def _check_company_verification(self, opportunity: EnrichedOpportunity) -> bool:
        """Check if company is verified."""
        return bool(
            opportunity.company_name and
            opportunity.company_name != "Unknown" and
            opportunity.company_website
        )
    
    def _check_service_match(self, opportunity: EnrichedOpportunity) -> bool:
        """Check if service match exists."""
        return bool(opportunity.recommended_service)
    
    def _check_outsourcing_fit(self, opportunity: EnrichedOpportunity) -> bool:
        """Check if outsourcing fit is reasonable."""
        return opportunity.outsourcing_fit in ["HIGH", "MEDIUM"]
    
    def _check_recency(self, opportunity: EnrichedOpportunity) -> bool:
        """Check if evidence is recent enough."""
        # For now, assume all opportunities are recent
        # In production, this would check the actual date
        return True
    
    def _calculate_qualification_score(
        self,
        requirement_evidence: bool,
        person_verification: bool,
        company_verification: bool,
        service_match: bool,
        outsourcing_fit: bool,
        recency: bool,
        opportunity: EnrichedOpportunity
    ) -> float:
        """Calculate qualification score."""
        score = 0
        
        # Requirement evidence (25 points)
        if requirement_evidence:
            score += 25
        
        # Person verification (20 points)
        if person_verification:
            score += 20
        
        # Company verification (15 points)
        if company_verification:
            score += 15
        
        # Service match (15 points)
        if service_match:
            score += 15
        
        # Outsourcing fit (15 points)
        if outsourcing_fit:
            score += 15
        
        # Recency (10 points)
        if recency:
            score += 10
        
        return score
    
    def batch_qualify(self, opportunities: list[EnrichedOpportunity]) -> list[QualificationResult]:
        """Qualify a batch of opportunities."""
        results = []
        for opportunity in opportunities:
            result = self.qualify(opportunity)
            results.append(result)
        return results
    
    def get_qualified_opportunities(
        self,
        opportunities: list[EnrichedOpportunity],
        results: list[QualificationResult]
    ) -> list[EnrichedOpportunity]:
        """Get only qualified opportunities."""
        qualified = []
        for opportunity, result in zip(opportunities, results):
            if result.qualified:
                qualified.append(opportunity)
        return qualified
    
    def get_rejection_summary(self, results: list[QualificationResult]) -> dict[str, int]:
        """Get summary of rejection reasons."""
        summary = {}
        for result in results:
            for reason in result.rejection_reasons:
                summary[reason] = summary.get(reason, 0) + 1
        return summary
