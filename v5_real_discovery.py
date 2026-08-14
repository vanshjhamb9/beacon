#!/usr/bin/env python3
"""
V5 REAL OPPORTUNITY DISCOVERY
==============================
Actual discovery of opportunities using websearch.
Focus on publicly verifiable sources.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import sys

EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)


def search_web(query: str, num_results: int = 10) -> List[Dict]:
    """Search web using websearch."""
    try:
        # Use websearch tool via subprocess
        result = subprocess.run(
            ["python", "-c", f"""
import sys
sys.path.insert(0, '.')
from tools.websearch import websearch
results = websearch("{query}", num_results={num_results})
for r in results:
    print(json.dumps(r))
"""],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            return [json.loads(line) for line in lines if line]
        else:
            print(f"Search error: {result.stderr}")
            return []
    except Exception as e:
        print(f"Search exception: {e}")
        return []


def search_reddit_development() -> List[Dict]:
    """Search Reddit for development opportunities."""
    print("\n" + "=" * 70)
    print("REDDIT DISCOVERY — Development Opportunities")
    print("=" * 70)

    search_queries = [
        "site:reddit.com looking for developer",
        "site:reddit.com need developer",
        "site:reddit.com need technical team",
        "site:reddit.com looking for development agency",
        "site:reddit.com need MVP developer",
        "site:reddit.com need SaaS developer",
        "site:reddit.com need mobile app developer",
        "site:reddit.com need Android developer",
        "site:reddit.com need iOS developer",
        "site:reddit.com looking for technical partner",
        "site:reddit.com need AI developer",
        "site:reddit.com need chatbot",
        "site:reddit.com need WhatsApp bot",
        "site:reddit.com need Shopify developer",
        "site:reddit.com need someone to build",
        "site:reddit.com looking for software development company",
        "site:reddit.com need help building",
        "site:reddit.com need external development team",
    ]

    all_results = []

    for query in search_queries:
        print(f"\nSearching: '{query}'")
        results = search_web(query, num_results=5)

        for result in results:
            url = result.get("url", "")
            if "/comments/" in url:  # Exact Reddit post
                all_results.append({
                    "source": "REDDIT",
                    "url": url,
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "query": query
                })

    return all_results


def search_linkedin_development() -> List[Dict]:
    """Search LinkedIn for development opportunities."""
    print("\n" + "=" * 70)
    print("LINKEDIN DISCOVERY — Development Opportunities")
    print("=" * 70)

    search_queries = [
        "site:linkedin.com/posts looking for technical co-founder",
        "site:linkedin.com/posts need development team",
        "site:linkedin.com/posts outsourcing development",
        "site:linkedin.com/posts need software agency",
        "site:linkedin.com/posts looking for implementation partner",
        "site:linkedin.com/posts need MVP development",
        "site:linkedin.com/posts looking for technical partner",
    ]

    all_results = []

    for query in search_queries:
        print(f"\nSearching: '{query}'")
        results = search_web(query, num_results=5)

        for result in results:
            url = result.get("url", "")
            if "linkedin.com/posts/" in url:  # Exact LinkedIn post
                all_results.append({
                    "source": "LINKEDIN",
                    "url": url,
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "query": query
                })

    return all_results


def search_twitter_development() -> List[Dict]:
    """Search X/Twitter for development opportunities."""
    print("\n" + "=" * 70)
    print("X/TWITTER DISCOVERY — Development Opportunities")
    print("=" * 70)

    search_queries = [
        "site:twitter.com looking for developer",
        "site:twitter.com need developer",
        "site:twitter.com need technical team",
        "site:twitter.com looking for development agency",
        "site:twitter.com need MVP developer",
        "site:twitter.com need SaaS developer",
        "site:twitter.com need mobile app developer",
        "site:twitter.com need someone to build",
    ]

    all_results = []

    for query in search_queries:
        print(f"\nSearching: '{query}'")
        results = search_web(query, num_results=5)

        for result in results:
            url = result.get("url", "")
            if "twitter.com/" in url or "x.com/" in url:
                all_results.append({
                    "source": "X_TWITTER",
                    "url": url,
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "query": query
                })

    return all_results


def search_freelancer_exact_jobs() -> List[Dict]:
    """Search Freelancer.com for exact job postings."""
    print("\n" + "=" * 70)
    print("FREELANCER.COM DISCOVERY — Exact Job Postings")
    print("=" * 70)

    search_queries = [
        "site:freelancer.com/projects AI chatbot development",
        "site:freelancer.com/projects WhatsApp bot development",
        "site:freelancer.com/projects Shopify automation",
        "site:freelancer.com/projects mobile app development",
        "site:freelancer.com/projects SaaS MVP development",
        "site:freelancer.com/projects custom software development",
    ]

    all_results = []

    for query in search_queries:
        print(f"\nSearching: '{query}'")
        results = search_web(query, num_results=5)

        for result in results:
            url = result.get("url", "")
            if "/projects/" in url and "freelancer.com" in url:  # Exact job URL
                all_results.append({
                    "source": "FREELANCER",
                    "url": url,
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "query": query
                })

    return all_results


def search_upwork_exact_jobs() -> List[Dict]:
    """Search Upwork for exact job postings (only if verifiable)."""
    print("\n" + "=" * 70)
    print("UPWORK DISCOVERY — Exact Job Postings")
    print("=" * 70)

    search_queries = [
        "site:upwork.com/freelance-jobs AI chatbot development",
        "site:upwork.com/freelance-jobs WhatsApp bot development",
        "site:upwork.com/freelance-jobs Shopify automation",
        "site:upwork.com/freelance-jobs mobile app development",
        "site:upwork.com/freelance-jobs SaaS MVP development",
        "site:upwork.com/freelance-jobs custom software development",
    ]

    all_results = []

    for query in search_queries:
        print(f"\nSearching: '{query}'")
        results = search_web(query, num_results=5)

        for result in results:
            url = result.get("url", "")
            if "/freelance-jobs/apply/" in url and "_~" in url:  # Exact job URL
                all_results.append({
                    "source": "UPWORK",
                    "url": url,
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "query": query
                })

    return all_results


def extract_opportunity_from_reddit(result: Dict) -> Optional[Dict]:
    """Extract opportunity from Reddit search result."""
    url = result.get("url", "")
    title = result.get("title", "")
    snippet = result.get("snippet", "")

    # Check if it's an exact Reddit post
    if "/comments/" not in url:
        return None

    # Extract post ID
    match = re.search(r"/comments/([a-zA-Z0-9]+)/", url)
    if not match:
        return None

    post_id = match.group(1)

    # Check for development-related keywords
    dev_keywords = [
        "looking for developer", "need developer", "need technical team",
        "looking for development agency", "need MVP developer", "need SaaS developer",
        "need mobile app developer", "need Android developer", "need iOS developer",
        "looking for technical partner", "need AI developer", "need chatbot",
        "need WhatsApp bot", "need Shopify developer", "need someone to build",
        "looking for software development company", "need help building",
        "need external development team"
    ]

    has_dev_keyword = any(kw.lower() in snippet.lower() for kw in dev_keywords)

    if not has_dev_keyword:
        return None

    # Extract person name (username)
    person_match = re.search(r"reddit\.com/user/([a-zA-Z0-9_-]+)", url)
    person_name = person_match.group(1) if person_match else "Unknown"

    # Create opportunity
    return {
        "opportunity_id": f"V5-REDDIT-{post_id[:8]}",
        "source_type": "REDDIT",
        "source_url": url,
        "source_title": title,
        "source_access_status": "ACCESSIBLE",
        "source_verification_method": "EXACT_POST_URL",
        "source_date": "UNKNOWN",
        "person_name": person_name,
        "person_role": "Reddit User",
        "person_profile_url": f"https://www.reddit.com/user/{person_name}",
        "person_identity_confidence": "LOW",
        "company_name": "UNKNOWN",
        "company_domain": "",
        "company_linkedin": "",
        "company_description": "",
        "company_stage": "",
        "company_size": "",
        "industry": "",
        "country": "",
        "prospect_type": "UNKNOWN",
        "requirement": snippet,
        "requirement_confidence": "UNVERIFIED",
        "outsourcing_intent": "UNKNOWN",
        "outsourcing_fit": 0,
        "intent_level": "UNKNOWN",
        "intent_score": 0,
        "icp_fit": 0,
        "buyability": 0,
        "evidence_quality": 50,
        "service_match": 0,
        "service_match_score": 0,
        "comai_score": 0,
        "saas_score": 0,
        "custom_software_score": 0,
        "primary_business_unit": "UNKNOWN",
        "secondary_business_units": [],
        "budget_status": "UNKNOWN",
        "evidence": [],
        "cross_source_validation": [],
        "missing_information": ["Person name", "Company", "Exact requirement", "Date"],
        "next_research": ["Verify person identity", "Verify requirement", "Check for company"],
        "currentness": "UNKNOWN",
        "qualification_status": "NEEDS_RESEARCH",
        "v5_audit_score": 0,
        "audit_verdict": "UNKNOWN",
        "audit_reasons": []
    }


def extract_opportunity_from_linkedin(result: Dict) -> Optional[Dict]:
    """Extract opportunity from LinkedIn search result."""
    url = result.get("url", "")
    title = result.get("title", "")
    snippet = result.get("snippet", "")

    # Check if it's an exact LinkedIn post
    if "linkedin.com/posts/" not in url:
        return None

    # Extract person name from URL or title
    person_match = re.search(r"linkedin\.com/posts/([a-zA-Z0-9_-]+)", url)
    person_name = person_match.group(1) if person_match else "Unknown"

    # Check for development-related keywords
    dev_keywords = [
        "looking for technical co-founder", "need development team",
        "outsourcing development", "need software agency",
        "looking for implementation partner", "need MVP development",
        "looking for technical partner"
    ]

    has_dev_keyword = any(kw.lower() in snippet.lower() for kw in dev_keywords)

    if not has_dev_keyword:
        return None

    # Create opportunity
    return {
        "opportunity_id": f"V5-LINKEDIN-{person_name[:10]}",
        "source_type": "LINKEDIN",
        "source_url": url,
        "source_title": title,
        "source_access_status": "ACCESSIBLE",
        "source_verification_method": "EXACT_POST_URL",
        "source_date": "UNKNOWN",
        "person_name": person_name,
        "person_role": "LinkedIn User",
        "person_profile_url": f"https://www.linkedin.com/in/{person_name}",
        "person_identity_confidence": "MEDIUM",
        "company_name": "UNKNOWN",
        "company_domain": "",
        "company_linkedin": "",
        "company_description": "",
        "company_stage": "",
        "company_size": "",
        "industry": "",
        "country": "",
        "prospect_type": "UNKNOWN",
        "requirement": snippet,
        "requirement_confidence": "UNVERIFIED",
        "outsourcing_intent": "UNKNOWN",
        "outsourcing_fit": 0,
        "intent_level": "UNKNOWN",
        "intent_score": 0,
        "icp_fit": 0,
        "buyability": 0,
        "evidence_quality": 50,
        "service_match": 0,
        "service_match_score": 0,
        "comai_score": 0,
        "saas_score": 0,
        "custom_software_score": 0,
        "primary_business_unit": "UNKNOWN",
        "secondary_business_units": [],
        "budget_status": "UNKNOWN",
        "evidence": [],
        "cross_source_validation": [],
        "missing_information": ["Person name", "Company", "Exact requirement", "Date"],
        "next_research": ["Verify person identity", "Verify requirement", "Check for company"],
        "currentness": "UNKNOWN",
        "qualification_status": "NEEDS_RESEARCH",
        "v5_audit_score": 0,
        "audit_verdict": "UNKNOWN",
        "audit_reasons": []
    }


def extract_opportunity_from_freelancer(result: Dict) -> Optional[Dict]:
    """Extract opportunity from Freelancer.com search result."""
    url = result.get("url", "")
    title = result.get("title", "")
    snippet = result.get("snippet", "")

    # Check if it's an exact job URL
    if "/projects/" not in url or "freelancer.com" not in url:
        return None

    # Extract job ID
    job_match = re.search(r"/projects/(\d+)", url)
    if not job_match:
        return None

    job_id = job_match.group(1)

    # Create opportunity
    return {
        "opportunity_id": f"V5-FREELANCER-{job_id}",
        "source_type": "FREELANCER",
        "source_url": url,
        "source_title": title,
        "source_access_status": "ACCESSIBLE",
        "source_verification_method": "EXACT_JOB_URL",
        "source_date": "UNKNOWN",
        "person_name": "Anonymous Client",
        "person_role": "Client",
        "person_profile_url": "",
        "person_identity_confidence": "ANONYMOUS",
        "company_name": "UNKNOWN",
        "company_domain": "",
        "company_linkedin": "",
        "company_description": "",
        "company_stage": "",
        "company_size": "",
        "industry": "",
        "country": "",
        "prospect_type": "UNKNOWN",
        "requirement": snippet,
        "requirement_confidence": "UNVERIFIED",
        "outsourcing_intent": "EXPLICIT_OUTSOURCING",
        "outsourcing_fit": 80,
        "intent_level": "ACTIVE_REQUIREMENT",
        "intent_score": 70,
        "icp_fit": 50,
        "buyability": 50,
        "evidence_quality": 50,
        "service_match": 50,
        "service_match_score": 50,
        "comai_score": 0,
        "saas_score": 0,
        "custom_software_score": 0,
        "primary_business_unit": "UNKNOWN",
        "secondary_business_units": [],
        "budget_status": "UNKNOWN",
        "evidence": [],
        "cross_source_validation": [],
        "missing_information": ["Person name", "Company", "Exact requirement", "Date", "Budget"],
        "next_research": ["Verify job content", "Verify client identity", "Check for company"],
        "currentness": "UNKNOWN",
        "qualification_status": "NEEDS_RESEARCH",
        "v5_audit_score": 0,
        "audit_verdict": "UNKNOWN",
        "audit_reasons": []
    }


def extract_opportunity_from_upwork(result: Dict) -> Optional[Dict]:
    """Extract opportunity from Upwork search result."""
    url = result.get("url", "")
    title = result.get("title", "")
    snippet = result.get("snippet", "")

    # Check if it's an exact job URL
    if "/freelance-jobs/apply/" not in url or "_~" not in url:
        return None

    # Extract job ID
    job_match = re.search(r"_~([a-f0-9]+)", url)
    if not job_match:
        return None

    job_id = job_match.group(1)

    # Upwork blocks access, so we can't verify
    return {
        "opportunity_id": f"V5-UPWORK-{job_id[:8]}",
        "source_type": "UPWORK",
        "source_url": url,
        "source_title": title,
        "source_access_status": "BLOCKED_BUT_URL_VALID",
        "source_verification_method": "EXACT_JOB_URL",
        "source_date": "UNKNOWN",
        "person_name": "Anonymous Upwork Client",
        "person_role": "Client",
        "person_profile_url": "",
        "person_identity_confidence": "ANONYMOUS",
        "company_name": "UNKNOWN",
        "company_domain": "",
        "company_linkedin": "",
        "company_description": "",
        "company_stage": "",
        "company_size": "",
        "industry": "",
        "country": "",
        "prospect_type": "UNKNOWN",
        "requirement": snippet,
        "requirement_confidence": "UNVERIFIED",
        "outsourcing_intent": "EXPLICIT_OUTSOURCING",
        "outsourcing_fit": 80,
        "intent_level": "ACTIVE_REQUIREMENT",
        "intent_score": 70,
        "icp_fit": 50,
        "buyability": 50,
        "evidence_quality": 50,
        "service_match": 50,
        "service_match_score": 50,
        "comai_score": 0,
        "saas_score": 0,
        "custom_software_score": 0,
        "primary_business_unit": "UNKNOWN",
        "secondary_business_units": [],
        "budget_status": "UNKNOWN",
        "evidence": [],
        "cross_source_validation": [],
        "missing_information": ["Person name", "Company", "Exact requirement", "Date", "Budget"],
        "next_research": ["Verify job content via human", "Verify client identity", "Check for company"],
        "currentness": "UNKNOWN",
        "qualification_status": "NEEDS_RESEARCH",
        "v5_audit_score": 0,
        "audit_verdict": "UNKNOWN",
        "audit_reasons": []
    }


def main():
    """Main discovery execution."""
    print("=" * 70)
    print("V5 REAL OPPORTUNITY DISCOVERY")
    print("=" * 70)

    all_opportunities = []

    # Step 1: Reddit Discovery
    reddit_results = search_reddit_development()
    print(f"\nReddit results: {len(reddit_results)}")

    for result in reddit_results:
        opp = extract_opportunity_from_reddit(result)
        if opp:
            all_opportunities.append(opp)

    # Step 2: LinkedIn Discovery
    linkedin_results = search_linkedin_development()
    print(f"\nLinkedIn results: {len(linkedin_results)}")

    for result in linkedin_results:
        opp = extract_opportunity_from_linkedin(result)
        if opp:
            all_opportunities.append(opp)

    # Step 3: X/Twitter Discovery
    twitter_results = search_twitter_development()
    print(f"\nX/Twitter results: {len(twitter_results)}")

    for result in twitter_results:
        # Extract from Twitter (similar to Reddit/LinkedIn)
        pass

    # Step 4: Freelancer.com Discovery
    freelancer_results = search_freelancer_exact_jobs()
    print(f"\nFreelancer.com results: {len(freelancer_results)}")

    for result in freelancer_results:
        opp = extract_opportunity_from_freelancer(result)
        if opp:
            all_opportunities.append(opp)

    # Step 5: Upwork Discovery (if verifiable)
    upwork_results = search_upwork_exact_jobs()
    print(f"\nUpwork results: {len(upwork_results)}")

    for result in upwork_results:
        opp = extract_opportunity_from_upwork(result)
        if opp:
            all_opportunities.append(opp)

    # Step 6: Save opportunities
    print(f"\nTotal opportunities found: {len(all_opportunities)}")

    # Save to JSON
    json_path = EXPORTS_DIR / "v5_raw_opportunities.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "discovery_date": datetime.now().isoformat(),
            "total_opportunities": len(all_opportunities),
            "opportunities": all_opportunities
        }, f, indent=2, ensure_ascii=False)

    print(f"Raw opportunities saved: {json_path}")

    return all_opportunities


if __name__ == "__main__":
    main()
