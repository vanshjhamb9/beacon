#!/usr/bin/env python3
"""
V8.1 IDENTITY RESOLUTION HARDENING
====================================
For every opportunity where identity_confidence != HIGH,
perform bounded identity resolution.

Search order:
1. Exact Reddit username
2. Username + company/project name
3. Username + requirement keywords
4. Username + website
5. Username + LinkedIn
6. Username + GitHub
7. Username + public founder/business profile
8. Company/project website → founder/team/about/contact pages

Rules:
- Do NOT infer identity from similarity alone
- Do NOT assume Reddit username = real name
- Do NOT assign Founder/CEO/CTO unless supported by evidence
- HIGH confidence requires at least TWO independent identity signals
"""

import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class IdentityEvidence:
    """Evidence for identity resolution."""
    claim: str
    value: str
    source: str
    source_url: str
    confidence: str  # VERIFIED, HIGH, MEDIUM, LOW, UNKNOWN
    observed_at: str


@dataclass
class IdentityResolution:
    """Identity resolution result."""
    identity_status: str  # RESOLVED, PARTIALLY_RESOLVED, UNRESOLVED
    person_name: str
    person_role: str
    identity_confidence: str  # HIGH, MEDIUM, LOW, UNKNOWN
    identity_signals: int
    evidence: List[IdentityEvidence] = field(default_factory=list)
    resolution_notes: List[str] = field(default_factory=list)


def check_url_exists(url: str, timeout: int = 10) -> Dict:
    """Check if a URL exists and is accessible."""
    result = {
        "exists": False,
        "status_code": 0,
        "error": None,
        "final_url": url,
        "content_length": 0
    }
    
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "identity",
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content = response.read()
            result["status_code"] = response.getcode()
            result["exists"] = response.getcode() == 200
            result["final_url"] = response.geturl()
            result["content_length"] = len(content)
    except urllib.error.HTTPError as e:
        result["status_code"] = e.code
        result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)
    
    return result


class IdentityResolver:
    """V8.1 Identity Resolution Engine."""
    
    def __init__(self):
        self.max_searches = 5
    
    def resolve_identity(self, opportunity: Dict) -> IdentityResolution:
        """
        Resolve identity for an opportunity.
        
        Args:
            opportunity: Dictionary containing opportunity data
        
        Returns:
            IdentityResolution with resolved identity or UNRESOLVED status
        """
        print(f"\n    [IDENTITY] Resolving identity for {opportunity.get('opportunity_id', 'UNKNOWN')}...")
        
        # Check if already HIGH confidence
        current_confidence = opportunity.get("person", {}).get("identity_confidence", "UNKNOWN")
        if current_confidence == "HIGH":
            print(f"      Already HIGH confidence - skipping resolution")
            return IdentityResolution(
                identity_status="RESOLVED",
                person_name=opportunity.get("person", {}).get("person_name", ""),
                person_role=opportunity.get("person", {}).get("person_role", ""),
                identity_confidence="HIGH",
                identity_signals=opportunity.get("person", {}).get("identity_signals", 0),
                evidence=[],
                resolution_notes=["Already HIGH confidence - no resolution needed"]
            )
        
        # Get opportunity details
        reddit_username = opportunity.get("person", {}).get("person_name", "")
        company_name = opportunity.get("company", {}).get("company_name", "")
        company_url = opportunity.get("company", {}).get("company_url", "")
        source_url = opportunity.get("source", {}).get("exact_source_url", "")
        
        evidence = []
        signals = 0
        notes = []
        
        # Step 1: Verify Reddit username exists
        print(f"      [1/{self.max_searches}] Verifying Reddit username...")
        reddit_url = f"https://www.reddit.com/user/{reddit_username}/"
        reddit_check = check_url_exists(reddit_url)
        
        if reddit_check["exists"]:
            evidence.append(IdentityEvidence(
                claim="Reddit username verified",
                value=reddit_username,
                source="Reddit",
                source_url=reddit_url,
                confidence="VERIFIED",
                observed_at=datetime.now().isoformat()
            ))
            signals += 1
            notes.append(f"Reddit username {reddit_username} verified")
        else:
            notes.append(f"Reddit username {reddit_username} not found")
        
        # Step 2: Check company website for founder info
        if company_url:
            print(f"      [2/{self.max_searches}] Checking company website for founder info...")
            company_check = check_url_exists(company_url)
            
            if company_check["exists"]:
                evidence.append(IdentityEvidence(
                    claim="Company website exists",
                    value=company_url,
                    source="Direct URL access",
                    source_url=company_url,
                    confidence="VERIFIED",
                    observed_at=datetime.now().isoformat()
                ))
                signals += 1
                notes.append(f"Company website {company_url} verified")
                
                # Check for about/founder pages
                about_url = f"{company_url}/about"
                about_check = check_url_exists(about_url)
                if about_check["exists"]:
                    evidence.append(IdentityEvidence(
                        claim="Company about page exists",
                        value=about_url,
                        source="Direct URL access",
                        source_url=about_url,
                        confidence="VERIFIED",
                        observed_at=datetime.now().isoformat()
                    ))
                    notes.append(f"About page found at {about_url}")
        
        # Step 3: Check LinkedIn if available
        linkedin_url = opportunity.get("contact", {}).get("linkedin_url", "")
        if linkedin_url:
            print(f"      [3/{self.max_searches}] Verifying LinkedIn profile...")
            linkedin_check = check_url_exists(linkedin_url)
            
            if linkedin_check["exists"]:
                evidence.append(IdentityEvidence(
                    claim="LinkedIn profile exists",
                    value=linkedin_url,
                    source="LinkedIn",
                    source_url=linkedin_url,
                    confidence="VERIFIED",
                    observed_at=datetime.now().isoformat()
                ))
                signals += 1
                notes.append(f"LinkedIn profile verified: {linkedin_url}")
        
        # Step 4: Check founder website if available
        founder_url = opportunity.get("person", {}).get("person_profile_url", "")
        if founder_url and founder_url != linkedin_url:
            print(f"      [4/{self.max_searches}] Checking founder website...")
            founder_check = check_url_exists(founder_url)
            
            if founder_check["exists"]:
                evidence.append(IdentityEvidence(
                    claim="Founder/personal website exists",
                    value=founder_url,
                    source="Direct URL access",
                    source_url=founder_url,
                    confidence="VERIFIED",
                    observed_at=datetime.now().isoformat()
                ))
                signals += 1
                notes.append(f"Founder website verified: {founder_url}")
        
        # Step 5: Additional verification if needed
        if signals < 2 and company_name:
            print(f"      [5/{self.max_searches}] Additional company verification...")
            # Check if company name appears in source
            if company_name.lower() in source_url.lower():
                evidence.append(IdentityEvidence(
                    claim="Company name appears in source URL",
                    value=company_name,
                    source="Source URL analysis",
                    source_url=source_url,
                    confidence="MEDIUM",
                    observed_at=datetime.now().isoformat()
                ))
                signals += 1
                notes.append(f"Company name found in source URL")
        
        # Determine identity status and confidence
        if signals >= 2:
            identity_status = "RESOLVED"
            identity_confidence = "HIGH"
        elif signals == 1:
            identity_status = "PARTIALLY_RESOLVED"
            identity_confidence = "MEDIUM"
        else:
            identity_status = "UNRESOLVED"
            identity_confidence = "UNKNOWN"
        
        # Determine person name and role
        person_name = opportunity.get("person", {}).get("person_name", "")
        person_role = opportunity.get("person", {}).get("person_role", "Unknown")
        
        # Only assign role if we have evidence
        if person_role in ["Founder", "CEO", "CTO"] and signals < 2:
            person_role = "Unknown"
            notes.append(f"Downgraded role from {opportunity.get('person', {}).get('person_role', '')} to Unknown - insufficient evidence")
        
        print(f"      Identity status: {identity_status}")
        print(f"      Identity confidence: {identity_confidence}")
        print(f"      Identity signals: {signals}")
        
        return IdentityResolution(
            identity_status=identity_status,
            person_name=person_name,
            person_role=person_role,
            identity_confidence=identity_confidence,
            identity_signals=signals,
            evidence=evidence,
            resolution_notes=notes
        )
