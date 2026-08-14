"""Cross-Source Validation Service for verifying information across multiple sources."""

from __future__ import annotations

import logging
from typing import Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of cross-source validation."""
    
    source_count: int
    source_urls: list[str]
    source_types: list[str]
    cross_source_confidence: str  # HIGH, MEDIUM, LOW
    
    # Validation details
    person_validated: bool
    company_validated: bool
    requirement_validated: bool
    
    # Inconsistencies
    inconsistencies: list[str]
    
    # Recommendations
    recommendations: list[str]


class CrossSourceValidator:
    """Validates information across multiple independent sources."""
    
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
    
    async def validate(
        self,
        person_name: str,
        company_name: str,
        source_url: str,
        requirement: str,
        linkedin_url: str = "",
        company_website: str = ""
    ) -> ValidationResult:
        """Validate information across multiple sources."""
        
        sources = []
        source_types = []
        inconsistencies = []
        
        # Add original source
        if source_url:
            sources.append(source_url)
            source_types.append(self._detect_source_type(source_url))
        
        # Validate person across sources
        person_validated = await self._validate_person(
            person_name, company_name, sources, inconsistencies
        )
        
        # Validate company across sources
        company_validated = await self._validate_company(
            company_name, company_website, sources, inconsistencies
        )
        
        # Validate requirement
        requirement_validated = bool(requirement and len(requirement) > 20)
        
        # Check LinkedIn if available
        if linkedin_url:
            sources.append(linkedin_url)
            source_types.append("linkedin")
        
        # Check company website if available
        if company_website:
            sources.append(company_website)
            source_types.append("company_website")
        
        # Calculate cross-source confidence
        cross_source_confidence = self._calculate_confidence(
            len(sources), person_validated, company_validated, inconsistencies
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            person_validated, company_validated, sources, inconsistencies
        )
        
        return ValidationResult(
            source_count=len(sources),
            source_urls=sources,
            source_types=list(set(source_types)),
            cross_source_confidence=cross_source_confidence,
            person_validated=person_validated,
            company_validated=company_validated,
            requirement_validated=requirement_validated,
            inconsistencies=inconsistencies,
            recommendations=recommendations
        )
    
    async def _validate_person(
        self,
        person_name: str,
        company_name: str,
        sources: list[str],
        inconsistencies: list[str]
    ) -> bool:
        """Validate person across multiple sources."""
        if not self.websearch_available or person_name == "Unknown":
            return False
        
        from opencode.tools import websearch
        
        try:
            # Search for person on LinkedIn
            query = f'"{person_name}" LinkedIn {company_name}'
            results = await websearch(query=query, numResults=3)
            
            if results and results.get("results"):
                for result in results["results"]:
                    url = result.get("url", "")
                    if "linkedin.com/in/" in url:
                        return True
            
            # Search for person on Twitter
            query = f'"{person_name}" Twitter {company_name}'
            results = await websearch(query=query, numResults=3)
            
            if results and results.get("results"):
                for result in results["results"]:
                    url = result.get("url", "")
                    if "twitter.com" in url or "x.com" in url:
                        return True
        except Exception as e:
            logger.warning("Person validation failed: %s", e)
        
        return False
    
    async def _validate_company(
        self,
        company_name: str,
        company_website: str,
        sources: list[str],
        inconsistencies: list[str]
    ) -> bool:
        """Validate company across multiple sources."""
        if not self.websearch_available or company_name == "Unknown":
            return False
        
        from opencode.tools import websearch
        
        try:
            # Search for company
            query = f'"{company_name}" official website'
            results = await websearch(query=query, numResults=3)
            
            if results and results.get("results"):
                for result in results["results"]:
                    url = result.get("url", "")
                    # Check if company name appears in results
                    title = result.get("title", "")
                    if company_name.lower() in title.lower():
                        return True
        except Exception as e:
            logger.warning("Company validation failed: %s", e)
        
        return False
    
    def _detect_source_type(self, url: str) -> str:
        """Detect source type from URL."""
        url_lower = url.lower()
        
        if "reddit.com" in url_lower:
            return "reddit"
        elif "twitter.com" in url_lower or "x.com" in url_lower:
            return "twitter"
        elif "linkedin.com" in url_lower:
            return "linkedin"
        elif "producthunt.com" in url_lower:
            return "producthunt"
        elif "upwork.com" in url_lower:
            return "upwork"
        elif "indiehackers.com" in url_lower:
            return "indiehackers"
        elif "news.ycombinator.com" in url_lower:
            return "hackernews"
        else:
            return "other"
    
    def _calculate_confidence(
        self,
        source_count: int,
        person_validated: bool,
        company_validated: bool,
        inconsistencies: list[str]
    ) -> str:
        """Calculate cross-source confidence."""
        score = 0
        
        # Source count
        if source_count >= 3:
            score += 40
        elif source_count >= 2:
            score += 25
        elif source_count >= 1:
            score += 10
        
        # Person validated
        if person_validated:
            score += 30
        
        # Company validated
        if company_validated:
            score += 20
        
        # Inconsistencies
        if not inconsistencies:
            score += 10
        
        if score >= 70:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendations(
        self,
        person_validated: bool,
        company_validated: bool,
        sources: list[str],
        inconsistencies: list[str]
    ) -> list[str]:
        """Generate recommendations for improving validation."""
        recommendations = []
        
        if not person_validated:
            recommendations.append("Search for LinkedIn profile to validate person")
        
        if not company_validated:
            recommendations.append("Search for company website to validate company")
        
        if len(sources) < 2:
            recommendations.append("Find additional source to cross-validate")
        
        if inconsistencies:
            recommendations.append("Review and resolve information inconsistencies")
        
        return recommendations
