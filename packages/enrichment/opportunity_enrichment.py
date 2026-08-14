"""Opportunity Enrichment Pipeline for Intent-First Discovery."""

from __future__ import annotations

import re
import logging
from datetime import date, datetime
from typing import Any, Optional
from dataclasses import dataclass, field

from packages.discovery_engine.models import DiscoveredCompany

logger = logging.getLogger(__name__)


@dataclass
class EnrichedOpportunity:
    """Enriched opportunity with full details."""
    
    # Core fields
    company_name: str
    person_name: str
    person_role: str
    company_website: str
    
    # Source information
    source_platform: str
    source_url: str
    source_date: str
    
    # Requirement
    exact_requirement: str
    intent_level: str
    intent_score: float
    
    # ICP and scoring
    icp_fit: float
    buyability: float
    evidence_quality: float
    opportunity_score: float
    
    # Business unit
    primary_business_unit: str
    secondary_business_unit: str
    
    # Service match
    recommended_service: str
    
    # Decision maker
    decision_maker: str
    decision_maker_confidence: str
    
    # Contact information
    linkedin_url: str
    email: str
    email_status: str
    phone: str
    
    # Company details
    company_stage: str
    company_size: str
    industry: str
    technology: str
    
    # Fit assessment
    outsourcing_fit: str
    
    # Sales intelligence
    why_now: str
    why_inowix: str
    
    # Evidence
    evidence: list[dict] = field(default_factory=list)
    
    # Cross-source validation
    cross_source_validation: dict = field(default_factory=dict)
    
    # Missing information
    missing_information: list[str] = field(default_factory=list)
    
    # Next steps
    recommended_next_research: list[str] = field(default_factory=list)
    
    # Status
    qualification_status: str = "PENDING"
    outreach_status: str = "PENDING_APPROVAL"


class OpportunityEnricher:
    """Enriches discovered opportunities with detailed information."""
    
    def __init__(self):
        self.websearch_available = False
        self._check_websearch()
    
    def _check_websearch(self):
        """Check if websearch tool is available."""
        try:
            from opencode.tools import websearch
            self.websearch_available = True
        except ImportError:
            logger.warning("Websearch tool not available")
    
    async def enrich(self, opportunity: DiscoveredCompany) -> EnrichedOpportunity:
        """Enrich a discovered opportunity with full details."""
        
        # Extract basic information
        person_name = opportunity.founder_name or "Unknown"
        person_role = opportunity.founder_role or "Founder"
        company_name = opportunity.company_name or "Unknown"
        
        # Get source information
        source_platform = opportunity.metadata.get("source_platform", opportunity.source)
        source_url = opportunity.metadata.get("source_url", "")
        source_date = str(opportunity.discovery_date)
        
        # Get requirement
        exact_requirement = opportunity.metadata.get("exact_requirement", "")
        if not exact_requirement and opportunity.buying_signals:
            exact_requirement = opportunity.buying_signals[0]
        
        # Get intent level
        intent_level = opportunity.metadata.get("intent_level", "COMPANY_OPPORTUNITY")
        
        # Calculate intent score based on level
        intent_score = self._calculate_intent_score(intent_level, exact_requirement)
        
        # Determine business unit
        primary_business_unit = self._determine_business_unit(exact_requirement, opportunity)
        secondary_business_unit = ""
        
        # Determine service match
        recommended_service = self._determine_service(exact_requirement, primary_business_unit)
        
        # Enrich with websearch if available
        linkedin_url = ""
        email = ""
        email_status = "UNKNOWN"
        phone = ""
        company_website = ""
        company_stage = "unknown"
        company_size = "unknown"
        industry = ""
        technology = ""
        
        if self.websearch_available and person_name != "Unknown":
            enrichment_data = await self._enrich_with_websearch(
                person_name, company_name, source_platform
            )
            linkedin_url = enrichment_data.get("linkedin_url", "")
            email = enrichment_data.get("email", "")
            email_status = enrichment_data.get("email_status", "UNKNOWN")
            phone = enrichment_data.get("phone", "")
            company_website = enrichment_data.get("company_website", "")
            company_stage = enrichment_data.get("company_stage", "unknown")
            company_size = enrichment_data.get("company_size", "unknown")
            industry = enrichment_data.get("industry", "")
            technology = enrichment_data.get("technology", "")
        
        # Calculate ICP fit
        icp_fit = self._calculate_icp_fit(
            company_name, company_stage, company_size, industry, primary_business_unit
        )
        
        # Calculate buyability
        buyability = self._calculate_buyability(
            person_name, linkedin_url, email, email_status, phone, company_website
        )
        
        # Calculate evidence quality
        evidence_quality = self._calculate_evidence_quality(
            source_url, exact_requirement, intent_level, opportunity
        )
        
        # Calculate opportunity score
        opportunity_score = self._calculate_opportunity_score(
            icp_fit, intent_score, buyability, evidence_quality
        )
        
        # Determine outsourcing fit
        outsourcing_fit = self._determine_outsourcing_fit(
            exact_requirement, intent_level, primary_business_unit
        )
        
        # Generate sales intelligence
        why_now = self._generate_why_now(exact_requirement, intent_level, source_platform)
        why_inowix = self._generate_why_inowix(
            exact_requirement, primary_business_unit, recommended_service
        )
        
        # Create evidence list
        evidence = self._create_evidence_list(opportunity, source_url, exact_requirement)
        
        # Cross-source validation
        cross_source_validation = {
            "source_count": 1,
            "source_urls": [source_url] if source_url else [],
            "source_types": [source_platform],
            "cross_source_confidence": "LOW"
        }
        
        # Missing information
        missing_information = self._identify_missing_info(
            linkedin_url, email, phone, company_website, company_name
        )
        
        # Next steps
        recommended_next_research = self._recommend_next_research(
            missing_information, primary_business_unit
        )
        
        # Create enriched opportunity
        enriched = EnrichedOpportunity(
            company_name=company_name,
            person_name=person_name,
            person_role=person_role,
            company_website=company_website,
            source_platform=source_platform,
            source_url=source_url,
            source_date=source_date,
            exact_requirement=exact_requirement,
            intent_level=intent_level,
            intent_score=intent_score,
            icp_fit=icp_fit,
            buyability=buyability,
            evidence_quality=evidence_quality,
            opportunity_score=opportunity_score,
            primary_business_unit=primary_business_unit,
            secondary_business_unit=secondary_business_unit,
            recommended_service=recommended_service,
            decision_maker=person_name,
            decision_maker_confidence="MEDIUM" if linkedin_url else "LOW",
            linkedin_url=linkedin_url,
            email=email,
            email_status=email_status,
            phone=phone,
            company_stage=company_stage,
            company_size=company_size,
            industry=industry,
            technology=technology,
            outsourcing_fit=outsourcing_fit,
            why_now=why_now,
            why_inowix=why_inowix,
            evidence=evidence,
            cross_source_validation=cross_source_validation,
            missing_information=missing_information,
            recommended_next_research=recommended_next_research,
            qualification_status="QUALIFIED" if opportunity_score >= 60 else "PENDING",
            outreach_status="PENDING_APPROVAL"
        )
        
        return enriched
    
    def _calculate_intent_score(self, intent_level: str, requirement: str) -> float:
        """Calculate intent score based on level and requirement."""
        base_scores = {
            "ACTIVE_REQUIREMENT": 95,
            "EVALUATION": 75,
            "EARLY_INTENT": 55,
            "COMPANY_OPPORTUNITY": 30,
            "NO_INTENT": 10
        }
        
        score = base_scores.get(intent_level, 30)
        
        # Boost for strong requirement signals
        if requirement:
            strong_signals = ["looking for", "need", "hire", "build", "agency", "team"]
            if any(signal in requirement.lower() for signal in strong_signals):
                score = min(score + 5, 100)
        
        return score
    
    def _determine_business_unit(self, requirement: str, opportunity: DiscoveredCompany) -> str:
        """Determine primary business unit based on requirement."""
        requirement_lower = requirement.lower()
        
        # COMAI signals
        comai_signals = ["whatsapp", "chatbot", "ecommerce", "shopify", "woocommerce", "customer support"]
        if any(signal in requirement_lower for signal in comai_signals):
            return "COMAI"
        
        # CUSTOM_SOFTWARE signals
        custom_signals = ["automation", "erp", "crm", "ai", "machine learning", "mobile app", "web app"]
        if any(signal in requirement_lower for signal in custom_signals):
            return "CUSTOM_SOFTWARE"
        
        # Default to SAAS_DEVELOPMENT
        return "SAAS_DEVELOPMENT"
    
    def _determine_service(self, requirement: str, business_unit: str) -> str:
        """Determine recommended service based on requirement."""
        requirement_lower = requirement.lower()
        
        if business_unit == "COMAI":
            if "whatsapp" in requirement_lower:
                return "WhatsApp Automation"
            elif "chatbot" in requirement_lower:
                return "AI Chatbot Development"
            else:
                return "Customer Support Automation"
        
        elif business_unit == "CUSTOM_SOFTWARE":
            if "automation" in requirement_lower:
                return "AI Automation"
            elif "erp" in requirement_lower:
                return "ERP Development"
            elif "crm" in requirement_lower:
                return "CRM Development"
            elif "mobile" in requirement_lower:
                return "Mobile App Development"
            else:
                return "Custom Software Development"
        
        else:  # SAAS_DEVELOPMENT
            if "mvp" in requirement_lower:
                return "SaaS MVP Development"
            elif "full stack" in requirement_lower or "full-stack" in requirement_lower:
                return "Full-Stack Development"
            elif "backend" in requirement_lower:
                return "Backend Development"
            elif "frontend" in requirement_lower:
                return "Frontend Development"
            else:
                return "SaaS Development"
    
    async def _enrich_with_websearch(
        self, person_name: str, company_name: str, source_platform: str
    ) -> dict[str, Any]:
        """Enrich opportunity using websearch."""
        from opencode.tools import websearch
        
        enrichment_data = {
            "linkedin_url": "",
            "email": "",
            "email_status": "UNKNOWN",
            "phone": "",
            "company_website": "",
            "company_stage": "unknown",
            "company_size": "unknown",
            "industry": "",
            "technology": ""
        }
        
        try:
            # Search for LinkedIn profile
            linkedin_query = f'"{person_name}" LinkedIn {company_name}'
            results = await websearch(query=linkedin_query, numResults=5)
            
            if results and results.get("results"):
                for result in results["results"]:
                    url = result.get("url", "")
                    if "linkedin.com/in/" in url:
                        enrichment_data["linkedin_url"] = url
                        break
            
            # Search for company website
            if company_name and company_name != "Unknown":
                website_query = f'"{company_name}" official website'
                results = await websearch(query=website_query, numResults=5)
                
                if results and results.get("results"):
                    for result in results["results"]:
                        url = result.get("url", "")
                        if company_name.lower().replace(" ", "") in url.lower().replace(" ", ""):
                            enrichment_data["company_website"] = url
                            break
            
            # Search for contact information
            if company_name and company_name != "Unknown":
                contact_query = f'"{company_name}" email contact'
                results = await websearch(query=contact_query, numResults=5)
                
                if results and results.get("results"):
                    for result in results["results"]:
                        excerpts = result.get("excerpts", [])
                        for excerpt in excerpts:
                            # Extract email
                            email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', excerpt)
                            if email_match:
                                enrichment_data["email"] = email_match.group(0)
                                enrichment_data["email_status"] = "PUBLIC_UNVERIFIED"
                                break
        
        except Exception as e:
            logger.warning("Websearch enrichment failed: %s", e)
        
        return enrichment_data
    
    def _calculate_icp_fit(
        self, company_name: str, company_stage: str, company_size: str,
        industry: str, business_unit: str
    ) -> float:
        """Calculate ICP fit score."""
        score = 50  # Base score
        
        # Company stage
        if company_stage in ["early", "growing"]:
            score += 20
        elif company_stage == "mid_size":
            score += 10
        
        # Company size
        if company_size in ["1-10", "11-50"]:
            score += 15
        elif company_size == "51-200":
            score += 5
        
        # Industry
        tech_industries = ["saas", "technology", "software", "ai", "fintech"]
        if any(ind in industry.lower() for ind in tech_industries):
            score += 15
        
        return min(score, 100)
    
    def _calculate_buyability(
        self, person_name: str, linkedin_url: str, email: str,
        email_status: str, phone: str, company_website: str
    ) -> float:
        """Calculate buyability score."""
        score = 30  # Base score
        
        # Decision maker identified
        if person_name and person_name != "Unknown":
            score += 20
        
        # LinkedIn profile
        if linkedin_url:
            score += 20
        
        # Contact information
        if email and email_status == "VERIFIED":
            score += 20
        elif email and email_status == "PUBLIC_UNVERIFIED":
            score += 10
        
        # Company website
        if company_website:
            score += 10
        
        return min(score, 100)
    
    def _calculate_evidence_quality(
        self, source_url: str, requirement: str, intent_level: str,
        opportunity: DiscoveredCompany
    ) -> float:
        """Calculate evidence quality score."""
        score = 40  # Base score
        
        # Source URL
        if source_url:
            score += 20
        
        # Requirement
        if requirement and len(requirement) > 20:
            score += 20
        
        # Intent level
        if intent_level == "ACTIVE_REQUIREMENT":
            score += 20
        elif intent_level == "EVALUATION":
            score += 10
        
        # Multiple signals
        if len(opportunity.buying_signals) > 1:
            score += 10
        
        return min(score, 100)
    
    def _calculate_opportunity_score(
        self, icp_fit: float, intent_score: float, buyability: float, evidence_quality: float
    ) -> float:
        """Calculate overall opportunity score."""
        # Formula: ICP × 0.25 + Intent × 0.40 + Buyability × 0.20 + Evidence Quality × 0.15
        score = (
            icp_fit * 0.25 +
            intent_score * 0.40 +
            buyability * 0.20 +
            evidence_quality * 0.15
        )
        return round(score, 2)
    
    def _determine_outsourcing_fit(
        self, requirement: str, intent_level: str, business_unit: str
    ) -> str:
        """Determine outsourcing fit."""
        requirement_lower = requirement.lower()
        
        # High fit signals
        high_signals = [
            "looking for agency", "need agency", "looking for development team",
            "need development team", "outsource", "dedicated team", "external team"
        ]
        if any(signal in requirement_lower for signal in high_signals):
            return "HIGH"
        
        # Medium fit signals
        medium_signals = [
            "looking for developer", "need developer", "hire developer",
            "need help building", "looking for partner"
        ]
        if any(signal in requirement_lower for signal in medium_signals):
            return "MEDIUM"
        
        # Low fit - just hiring
        low_signals = ["hiring", "full-time", "permanent", "employee"]
        if any(signal in requirement_lower for signal in low_signals):
            return "LOW"
        
        return "MEDIUM"
    
    def _generate_why_now(self, requirement: str, intent_level: str, source_platform: str) -> str:
        """Generate why now explanation."""
        if intent_level == "ACTIVE_REQUIREMENT":
            return f"Explicit requirement detected on {source_platform}. Active need for technical services."
        elif intent_level == "EVALUATION":
            return f"Evaluating solutions on {source_platform}. Ready to engage with providers."
        else:
            return f"Opportunity identified through {source_platform} signal."
    
    def _generate_why_inowix(
        self, requirement: str, business_unit: str, service: str
    ) -> str:
        """Generate why Inowix explanation."""
        if business_unit == "COMAI":
            return f"Inowix specializes in {service} for ecommerce and customer engagement. Direct match with requirement."
        elif business_unit == "CUSTOM_SOFTWARE":
            return f"Inowix provides {service} with proven expertise. Can deliver immediate value."
        else:
            return f"Inowix offers {service} with dedicated teams. Can accelerate development timeline."
    
    def _create_evidence_list(
        self, opportunity: DiscoveredCompany, source_url: str, requirement: str
    ) -> list[dict]:
        """Create evidence list."""
        evidence = []
        
        if source_url:
            evidence.append({
                "claim": "Source post identified",
                "value": source_url,
                "source": opportunity.source,
                "confidence": "VERIFIED"
            })
        
        if requirement:
            evidence.append({
                "claim": "Requirement stated",
                "value": requirement,
                "source": opportunity.source,
                "confidence": "HIGH"
            })
        
        if opportunity.buying_signals:
            for signal in opportunity.buying_signals[:3]:
                evidence.append({
                    "claim": "Buying signal detected",
                    "value": signal,
                    "source": opportunity.source,
                    "confidence": "MEDIUM"
                })
        
        return evidence
    
    def _identify_missing_info(
        self, linkedin_url: str, email: str, phone: str,
        company_website: str, company_name: str
    ) -> list[str]:
        """Identify missing information."""
        missing = []
        
        if not linkedin_url:
            missing.append("LinkedIn profile")
        
        if not email or email == "":
            missing.append("Email address")
        
        if not phone or phone == "":
            missing.append("Phone number")
        
        if not company_website:
            missing.append("Company website")
        
        if company_name == "Unknown":
            missing.append("Company name")
        
        return missing
    
    def _recommend_next_research(
        self, missing_info: list[str], business_unit: str
    ) -> list[str]:
        """Recommend next research steps."""
        recommendations = []
        
        if "LinkedIn profile" in missing_info:
            recommendations.append("Search for LinkedIn profile")
        
        if "Email address" in missing_info:
            recommendations.append("Search for public email on company website")
        
        if "Company website" in missing_info:
            recommendations.append("Search for official company website")
        
        if business_unit == "COMAI":
            recommendations.append("Check for ecommerce/Shopify presence")
        
        return recommendations
