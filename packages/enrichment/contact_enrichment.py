"""Contact Enrichment Service for finding verified contact information."""

from __future__ import annotations

import re
import logging
from typing import Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ContactInfo:
    """Contact information for a person."""
    
    name: str
    email: str
    email_status: str  # VERIFIED, PUBLIC_UNVERIFIED, INVALID, UNKNOWN
    phone: str
    linkedin_url: str
    company_website: str
    social_profiles: dict[str, str]
    
    # Verification
    verification_sources: list[str]
    verification_confidence: str  # HIGH, MEDIUM, LOW


class ContactEnricher:
    """Enriches opportunities with verified contact information."""
    
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
    
    async def enrich_contact(
        self, person_name: str, company_name: str, source_url: str
    ) -> ContactInfo:
        """Enrich contact information for a person."""
        
        contact = ContactInfo(
            name=person_name,
            email="",
            email_status="UNKNOWN",
            phone="",
            linkedin_url="",
            company_website="",
            social_profiles={},
            verification_sources=[source_url] if source_url else [],
            verification_confidence="LOW"
        )
        
        if not self.websearch_available:
            return contact
        
        # Try to find LinkedIn profile
        linkedin_url = await self._find_linkedin(person_name, company_name)
        if linkedin_url:
            contact.linkedin_url = linkedin_url
            contact.verification_sources.append(linkedin_url)
        
        # Try to find company website
        company_website = await self._find_company_website(company_name)
        if company_website:
            contact.company_website = company_website
            contact.verification_sources.append(company_website)
            
            # Try to find email from company website
            email, email_status = await self._find_email_from_website(company_website)
            if email:
                contact.email = email
                contact.email_status = email_status
            
            # Try to find phone from company website
            phone = await self._find_phone_from_website(company_website)
            if phone:
                contact.phone = phone
        
        # Try to find social profiles
        social_profiles = await self._find_social_profiles(person_name, company_name)
        contact.social_profiles = social_profiles
        
        # Calculate verification confidence
        contact.verification_confidence = self._calculate_verification_confidence(contact)
        
        return contact
    
    async def _find_linkedin(self, person_name: str, company_name: str) -> str:
        """Find LinkedIn profile for a person."""
        from opencode.tools import websearch
        
        try:
            query = f'"{person_name}" LinkedIn {company_name}'
            results = await websearch(query=query, numResults=5)
            
            if results and results.get("results"):
                for result in results["results"]:
                    url = result.get("url", "")
                    if "linkedin.com/in/" in url:
                        return url
        except Exception as e:
            logger.warning("LinkedIn search failed: %s", e)
        
        return ""
    
    async def _find_company_website(self, company_name: str) -> str:
        """Find company website."""
        from opencode.tools import websearch
        
        if not company_name or company_name == "Unknown":
            return ""
        
        try:
            query = f'"{company_name}" official website'
            results = await websearch(query=query, numResults=5)
            
            if results and results.get("results"):
                for result in results["results"]:
                    url = result.get("url", "")
                    # Filter out social media and other non-company sites
                    if any(domain in url.lower() for domain in [
                        "linkedin.com", "twitter.com", "facebook.com",
                        "instagram.com", "crunchbase.com"
                    ]):
                        continue
                    
                    # Check if company name is in URL
                    company_clean = company_name.lower().replace(" ", "")
                    if company_clean in url.lower().replace(" ", "").replace("-", "").replace("_", ""):
                        return url
        except Exception as e:
            logger.warning("Company website search failed: %s", e)
        
        return ""
    
    async def _find_email_from_website(self, website_url: str) -> tuple[str, str]:
        """Find email from company website."""
        from opencode.tools import webfetch
        
        try:
            content = await webfetch(url=website_url, format="text")
            
            if content:
                # Extract email using regex
                email_pattern = r'[\w.-]+@[\w.-]+\.\w+'
                emails = re.findall(email_pattern, content)
                
                # Filter out common non-business emails
                filtered_emails = [
                    email for email in emails
                    if not any(domain in email.lower() for domain in [
                        "example.com", "test.com", "localhost",
                        "sentry.io", "wixpress.com"
                    ])
                ]
                
                if filtered_emails:
                    # Prefer info@, contact@, or hello@ emails
                    preferred = [
                        email for email in filtered_emails
                        if email.lower().startswith(("info@", "contact@", "hello@"))
                    ]
                    
                    if preferred:
                        return preferred[0], "PUBLIC_UNVERIFIED"
                    else:
                        return filtered_emails[0], "PUBLIC_UNVERIFIED"
        except Exception as e:
            logger.warning("Email extraction failed: %s", e)
        
        return "", "UNKNOWN"
    
    async def _find_phone_from_website(self, website_url: str) -> str:
        """Find phone number from company website."""
        from opencode.tools import webfetch
        
        try:
            content = await webfetch(url=website_url, format="text")
            
            if content:
                # Extract phone numbers
                phone_patterns = [
                    r'\+91[\s-]?\d{10}',
                    r'\+1[\s-]?\d{10}',
                    r'\d{10}',
                    r'\d{5}[\s-]\d{5}',
                ]
                
                for pattern in phone_patterns:
                    phones = re.findall(pattern, content)
                    if phones:
                        return phones[0]
        except Exception as e:
            logger.warning("Phone extraction failed: %s", e)
        
        return ""
    
    async def _find_social_profiles(
        self, person_name: str, company_name: str
    ) -> dict[str, str]:
        """Find social media profiles."""
        from opencode.tools import websearch
        
        profiles = {}
        
        try:
            # Search for Twitter/X
            query = f'"{person_name}" Twitter {company_name}'
            results = await websearch(query=query, numResults=3)
            
            if results and results.get("results"):
                for result in results["results"]:
                    url = result.get("url", "")
                    if "twitter.com" in url or "x.com" in url:
                        profiles["twitter"] = url
                        break
            
            # Search for GitHub
            query = f'"{person_name}" GitHub {company_name}'
            results = await websearch(query=query, numResults=3)
            
            if results and results.get("results"):
                for result in results["results"]:
                    url = result.get("url", "")
                    if "github.com" in url:
                        profiles["github"] = url
                        break
        except Exception as e:
            logger.warning("Social profile search failed: %s", e)
        
        return profiles
    
    def _calculate_verification_confidence(self, contact: ContactInfo) -> str:
        """Calculate verification confidence based on available information."""
        score = 0
        
        # LinkedIn profile
        if contact.linkedin_url:
            score += 30
        
        # Email
        if contact.email and contact.email_status == "VERIFIED":
            score += 30
        elif contact.email and contact.email_status == "PUBLIC_UNVERIFIED":
            score += 15
        
        # Phone
        if contact.phone:
            score += 15
        
        # Company website
        if contact.company_website:
            score += 15
        
        # Social profiles
        if contact.social_profiles:
            score += 10
        
        if score >= 70:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "LOW"
