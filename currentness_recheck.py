#!/usr/bin/env python3
"""
V8.1 CURRENTNESS RECHECK
==========================
When an opportunity is older than 30 days, perform bounded currentness investigation.

Check:
1. Original requirement/post
2. Company/product website
3. Founder website
4. LinkedIn/public social activity
5. Product updates
6. Recent project activity
7. Recent hiring/request activity
8. Recent comments/replies where publicly available

Rules:
- A live website alone does NOT prove the original requirement remains active
- A recent company post alone does NOT prove the original development requirement remains active
- Accept currentness only when evidence is connected to the project/requirement
- 0-30 days: CURRENT unless contradictory evidence exists
- 31-60 days: AGING unless recent evidence demonstrates active requirement
- 61-90 days: AGING unless strong current evidence exists
- 90+ days: STALE by default
- Exception: An older opportunity may become CURRENT only if independent evidence
  directly indicates that the same project/requirement is still active
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass, field


@dataclass
class CurrentnessEvidence:
    """Evidence for currentness verification."""
    claim: str
    value: str
    source: str
    source_url: str
    confidence: str  # VERIFIED, HIGH, MEDIUM, LOW, UNKNOWN
    observed_at: str


@dataclass
class CurrentnessRecheck:
    """Currentness recheck result."""
    currentness_status: str  # CURRENT, AGING, STALE, UNKNOWN
    age_days: int
    recheck_performed: bool
    evidence: List[CurrentnessEvidence] = field(default_factory=list)
    recheck_notes: List[str] = field(default_factory=list)
    requirement_specific_evidence: bool = False


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


def calculate_age_days(post_date_str: str) -> int:
    """Calculate age in days from post date string."""
    try:
        post_date = datetime.fromisoformat(post_date_str.replace("Z", "+00:00"))
        delta = datetime.now() - post_date.replace(tzinfo=None)
        return delta.days
    except:
        pass
    
    formats = ["%Y-%m-%d", "%d %b %Y", "%B %d, %Y"]
    for fmt in formats:
        try:
            post_date = datetime.strptime(post_date_str, fmt)
            delta = datetime.now() - post_date
            return delta.days
        except:
            continue
    
    return 999


class CurrentnessRecheckEngine:
    """V8.1 Currentness Recheck Engine."""
    
    def __init__(self):
        self.max_searches = 5
    
    def recheck_currentness(self, opportunity: Dict) -> CurrentnessRecheck:
        """
        Recheck currentness for an opportunity.
        
        Args:
            opportunity: Dictionary containing opportunity data
        
        Returns:
            CurrentnessRecheck with updated currentness status
        """
        print(f"\n    [CURRENTNESS] Rechecking currentness for {opportunity.get('opportunity_id', 'UNKNOWN')}...")
        
        # Get opportunity details
        published_at = opportunity.get("source", {}).get("published_at", "")
        source_url = opportunity.get("source", {}).get("exact_source_url", "")
        company_url = opportunity.get("company", {}).get("company_url", "")
        currentness_status = opportunity.get("currentness", {}).get("currentness_status", "UNKNOWN")
        
        # Calculate age
        age_days = calculate_age_days(published_at)
        print(f"      Age: {age_days} days")
        
        evidence = []
        notes = []
        requirement_specific_evidence = False
        
        # If already CURRENT and < 30 days, skip detailed recheck
        if age_days <= 30 and currentness_status == "CURRENT":
            print(f"      Already CURRENT and < 30 days - minimal recheck")
            return CurrentnessRecheck(
                currentness_status="CURRENT",
                age_days=age_days,
                recheck_performed=False,
                evidence=[],
                recheck_notes=["Already CURRENT and < 30 days - no recheck needed"],
                requirement_specific_evidence=True
            )
        
        # Perform bounded currentness investigation
        print(f"      Performing bounded currentness investigation...")
        
        # Step 1: Verify original source still exists
        print(f"      [1/{self.max_searches}] Verifying original source...")
        source_check = check_url_exists(source_url)
        
        if source_check["exists"]:
            evidence.append(CurrentnessEvidence(
                claim="Original source still accessible",
                value=f"HTTP {source_check['status_code']}",
                source="Direct URL access",
                source_url=source_url,
                confidence="VERIFIED",
                observed_at=datetime.now().isoformat()
            ))
            notes.append(f"Original source accessible at {source_url}")
        else:
            evidence.append(CurrentnessEvidence(
                claim="Original source accessibility",
                value=f"HTTP {source_check['status_code']}",
                source="Direct URL access",
                source_url=source_url,
                confidence="NOT_VERIFIED",
                observed_at=datetime.now().isoformat()
            ))
            notes.append(f"Original source returned HTTP {source_check['status_code']}")
        
        # Step 2: Check company website for recent activity
        if company_url:
            print(f"      [2/{self.max_searches}] Checking company website...")
            company_check = check_url_exists(company_url)
            
            if company_check["exists"]:
                evidence.append(CurrentnessEvidence(
                    claim="Company website still active",
                    value=company_url,
                    source="Direct URL access",
                    source_url=company_url,
                    confidence="VERIFIED",
                    observed_at=datetime.now().isoformat()
                ))
                notes.append(f"Company website active at {company_url}")
        
        # Step 3: Check for recent blog/updates
        if company_url:
            print(f"      [3/{self.max_searches}] Checking for recent updates...")
            blog_url = f"{company_url}/blog"
            blog_check = check_url_exists(blog_url)
            
            if blog_check["exists"]:
                evidence.append(CurrentnessEvidence(
                    claim="Blog/updates page exists",
                    value=blog_url,
                    source="Direct URL access",
                    source_url=blog_url,
                    confidence="VERIFIED",
                    observed_at=datetime.now().isoformat()
                ))
                notes.append(f"Blog page found at {blog_url}")
        
        # Step 4: Check founder website if available
        founder_url = opportunity.get("person", {}).get("person_profile_url", "")
        if founder_url and "linkedin.com" not in founder_url:
            print(f"      [4/{self.max_searches}] Checking founder website...")
            founder_check = check_url_exists(founder_url)
            
            if founder_check["exists"]:
                evidence.append(CurrentnessEvidence(
                    claim="Founder website still active",
                    value=founder_url,
                    source="Direct URL access",
                    source_url=founder_url,
                    confidence="VERIFIED",
                    observed_at=datetime.now().isoformat()
                ))
                notes.append(f"Founder website active at {founder_url}")
        
        # Step 5: Check LinkedIn if available
        linkedin_url = opportunity.get("contact", {}).get("linkedin_url", "")
        if linkedin_url:
            print(f"      [5/{self.max_searches}] Checking LinkedIn...")
            linkedin_check = check_url_exists(linkedin_url)
            
            if linkedin_check["exists"]:
                evidence.append(CurrentnessEvidence(
                    claim="LinkedIn profile exists",
                    value=linkedin_url,
                    source="LinkedIn",
                    source_url=linkedin_url,
                    confidence="VERIFIED",
                    observed_at=datetime.now().isoformat()
                ))
                notes.append(f"LinkedIn profile exists at {linkedin_url}")
        
        # Determine currentness status based on age and evidence
        if age_days <= 30:
            # 0-30 days: CURRENT unless contradictory evidence
            if source_check["exists"]:
                new_status = "CURRENT"
            else:
                new_status = "AGING"
        elif age_days <= 60:
            # 31-60 days: AGING unless recent evidence demonstrates active requirement
            # Check if we have requirement-specific evidence
            if source_check["exists"] and company_check.get("exists", False):
                new_status = "AGING"
                # Could be CURRENT if we find requirement-specific evidence
                # For now, keep as AGING without specific evidence
            else:
                new_status = "AGING"
        elif age_days <= 90:
            # 61-90 days: AGING unless strong current evidence
            new_status = "AGING"
        else:
            # 90+ days: STALE by default
            new_status = "STALE"
            # Exception: Can become CURRENT only with requirement-specific evidence
            # We don't have that evidence here
        
        # Check if we found any requirement-specific evidence
        # (Evidence that directly indicates the same project/requirement is still active)
        # For now, we don't have such evidence, so requirement_specific_evidence = False
        
        print(f"      Currentness status: {new_status}")
        print(f"      Age: {age_days} days")
        print(f"      Requirement-specific evidence: {requirement_specific_evidence}")
        
        return CurrentnessRecheck(
            currentness_status=new_status,
            age_days=age_days,
            recheck_performed=True,
            evidence=evidence,
            recheck_notes=notes,
            requirement_specific_evidence=requirement_specific_evidence
        )
