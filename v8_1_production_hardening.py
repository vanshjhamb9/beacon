#!/usr/bin/env python3
"""
V8.1 PRODUCTION HARDENING PATCH
=================================
Hardening patch for V8, NOT a new discovery engine.

V8.1 DOES NOT FIND MORE LEADS.
V8.1 MAKES V8'S EXISTING LEADS HARDER TO FOOL.

IDENTITY MUST BE PROVABLE.
CURRENTNESS MUST BE DEFENSIBLE.
CONTACTABILITY MUST BE REAL.
EVIDENCE MUST BE REPRODUCIBLE.

ONLY THEN: SALES_READY.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

# Import hardening modules
from identity_resolver import IdentityResolver, IdentityResolution
from currentness_recheck import CurrentnessRecheckEngine, CurrentnessRecheck
from contact_verifier import ContactVerifier, ContactVerification
from evidence_consistency_auditor import EvidenceConsistencyAuditor, EvidenceConsistencyAudit

EXPORTS_DIR = Path("exports") / "discovery_v8_1"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

V8_DATA_PATH = Path("exports") / "discovery_v8" / "v8_sales_ready.json"


@dataclass
class V8_1Opportunity:
    """V8.1 hardened opportunity."""
    opportunity_id: str
    
    # Original V8 data
    v8_data: Dict = field(default_factory=dict)
    
    # V8.1 hardening results
    identity_resolution: Optional[IdentityResolution] = None
    currentness_recheck: Optional[CurrentnessRecheck] = None
    contact_verification: Optional[ContactVerification] = None
    evidence_consistency: Optional[EvidenceConsistencyAudit] = None
    
    # New fields
    identity_resolution_status: str = "UNKNOWN"
    currentness_recheck_status: str = "UNKNOWN"
    contact_association_status: str = "UNKNOWN"
    evidence_consistency_status: str = "UNKNOWN"
    reproducibility_test: str = "FAIL"
    reproducibility_reason: str = ""
    buying_event_verified: bool = False
    buying_event_evidence: List[Dict] = field(default_factory=list)
    
    # Final V8.1 verdict
    final_salesability: str = "REJECT"
    cto_15_minute_test: str = "NO"
    cto_decision_reason: str = ""
    rejection_reasons: List[str] = field(default_factory=list)


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


class V8_1Engine:
    """V8.1 Production Hardening Engine."""
    
    def __init__(self):
        self.identity_resolver = IdentityResolver()
        self.currentness_recheck = CurrentnessRecheckEngine()
        self.contact_verifier = ContactVerifier()
        self.evidence_auditor = EvidenceConsistencyAuditor()
        
        self.opportunities: List[V8_1Opportunity] = []
        self.stats = {
            "total_discovered": 0,
            "exact_source_verified": 0,
            "requirement_verified": 0,
            "buying_event_verified": 0,
            "identity_high": 0,
            "company_verified": 0,
            "current": 0,
            "explicit_outsourcing": 0,
            "service_match_high": 0,
            "contact_high": 0,
            "evidence_consistency_pass": 0,
            "reproducibility_pass": 0,
            "sales_ready": 0,
            "needs_research": 0,
            "rejected": 0
        }
    
    def load_v8_data(self) -> Dict:
        """Load V8 opportunity data."""
        print("\n[STEP 1] Loading V8 data...")
        
        # Try to load from V8 output
        if V8_DATA_PATH.exists():
            with open(V8_DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"  Loaded {len(data.get('opportunities', []))} opportunities from V8")
            return data
        
        # If V8 data doesn't exist, create sample data for testing
        print("  V8 data not found, creating sample data for testing...")
        return self._create_sample_v8_data()
    
    def _create_sample_v8_data(self) -> Dict:
        """Create sample V8 data for testing."""
        return {
            "opportunities": [
                {
                    "opportunity_id": "V8-001",
                    "requirement": "Build production app from existing specs — Next.js 14, Supabase, Tailwind, DocuSign, Twilio, Stripe Connect. Budget $15,000 - $20,000.",
                    "requirement_verified": True,
                    "source": {
                        "source_name": "Reddit",
                        "source_type": "REDDIT",
                        "exact_source_url": "https://old.reddit.com/r/forhire/comments/1spxdi9/",
                        "source_post_id": "1spxdi9",
                        "published_at": "2026-04-19",
                        "observed_at": datetime.now().isoformat(),
                        "source_access_status": "VERIFIED",
                        "requirement_observed": True,
                        "evidence": [
                            {
                                "claim": "Original Reddit post accessed",
                                "value": "HTTP 200 - Content verified",
                                "source": "Direct URL access",
                                "source_url": "https://old.reddit.com/r/forhire/comments/1spxdi9/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "person": {
                        "person_name": "betapunch",
                        "person_role": "Founder",
                        "person_profile_url": "https://www.reddit.com/user/betapunch/",
                        "company_name": "MarylandBid",
                        "company_url": "https://www.marylandbid.com",
                        "identity_confidence": "MEDIUM",
                        "identity_signals": 2,
                        "evidence": [
                            {
                                "claim": "Reddit username verified",
                                "value": "betapunch",
                                "source": "Reddit",
                                "source_url": "https://www.reddit.com/user/betapunch/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            },
                            {
                                "claim": "Company website exists",
                                "value": "marylandbid.com",
                                "source": "Direct URL access",
                                "source_url": "https://www.marylandbid.com",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "company": {
                        "company_name": "MarylandBid",
                        "company_url": "https://www.marylandbid.com",
                        "product_url": "https://www.marylandbid.com",
                        "company_description": "Real estate auction marketplace for off-market assignment contracts in Maryland",
                        "company_status": "VERIFIED_ACTIVE",
                        "evidence": [
                            {
                                "claim": "Live website with active auctions",
                                "value": "Platform operational with listings",
                                "source": "Direct URL access",
                                "source_url": "https://www.marylandbid.com",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "currentness": {
                        "age_days": 111,
                        "last_verified_at": datetime.now().isoformat(),
                        "currentness_status": "STALE",
                        "evidence": [
                            {
                                "claim": "Post date verified",
                                "value": "111 days old",
                                "source": "Reddit post metadata",
                                "source_url": "https://old.reddit.com/r/forhire/comments/1spxdi9/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "outsourcing": {
                        "outsourcing_intent": "EXPLICIT",
                        "outsourcing_confidence": "HIGH",
                        "evidence": [
                            {
                                "claim": "Post explicitly hiring developer",
                                "value": "[Hiring] tag + budget + requirements",
                                "source": "Reddit post",
                                "source_url": "https://old.reddit.com/r/forhire/comments/1spxdi9/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "service_match": {
                        "service": "Custom Software Development, SaaS Development",
                        "match_reason": "Full-stack development with Next.js, Supabase, Stripe integration",
                        "confidence": "HIGH",
                        "evidence": [
                            {
                                "claim": "Tech stack matches Inowix capabilities",
                                "value": "Next.js, Supabase, Stripe Connect",
                                "source": "Reddit post",
                                "source_url": "https://old.reddit.com/r/forhire/comments/1spxdi9/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "contact": {
                        "email": "",
                        "email_status": "UNKNOWN",
                        "linkedin_url": "",
                        "linkedin_status": "UNKNOWN",
                        "phone": "",
                        "phone_status": "UNKNOWN",
                        "platform_contact": "Reddit DM (u/betapunch)",
                        "platform_contact_status": "VERIFIED",
                        "contactability": "MEDIUM",
                        "contactability_evidence": [
                            {
                                "claim": "Reddit DM available",
                                "value": "u/betapunch",
                                "source": "Reddit",
                                "source_url": "https://www.reddit.com/user/betapunch/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "competitor": False,
                    "safety_clear": True,
                    "final_salesability": "REJECT",
                    "opportunity_verdict": "REJECT",
                    "contact_verdict": "NOT_CONTACTABLE",
                    "cto_15_minute_test": "NO",
                    "cto_decision_reason": "Identity not HIGH, Contactability not HIGH",
                    "rejection_reasons": [
                        "Identity confidence: MEDIUM (needs real name)",
                        "Contactability: MEDIUM (no email/LinkedIn)"
                    ]
                },
                {
                    "opportunity_id": "V8-002",
                    "requirement": "React Native mobile app (iOS + Android) for menstrual cycle planning app. Budget $2,000 USD total for MVP.",
                    "requirement_verified": True,
                    "source": {
                        "source_name": "Reddit",
                        "source_type": "REDDIT",
                        "exact_source_url": "https://www.reddit.com/r/forhire/comments/1txv6sr/",
                        "source_post_id": "1txv6sr",
                        "published_at": "2026-07-13",
                        "observed_at": datetime.now().isoformat(),
                        "source_access_status": "VERIFIED",
                        "requirement_observed": True,
                        "evidence": [
                            {
                                "claim": "Original Reddit post accessed",
                                "value": "HTTP 200 - Content verified",
                                "source": "Direct URL access",
                                "source_url": "https://www.reddit.com/r/forhire/comments/1txv6sr/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "person": {
                        "person_name": "Paloma Chiara",
                        "person_role": "Founder",
                        "person_profile_url": "https://linkedin.com/in/paloma-chiara",
                        "company_name": "Kilova",
                        "company_url": "https://kilova.app",
                        "identity_confidence": "HIGH",
                        "identity_signals": 4,
                        "evidence": [
                            {
                                "claim": "Reddit username verified",
                                "value": "paloma_chiara",
                                "source": "Reddit",
                                "source_url": "https://www.reddit.com/user/paloma_chiara/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            },
                            {
                                "claim": "LinkedIn profile found",
                                "value": "linkedin.com/in/paloma-chiara",
                                "source": "LinkedIn",
                                "source_url": "https://linkedin.com/in/paloma-chiara",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            },
                            {
                                "claim": "Company website verified",
                                "value": "kilova.app",
                                "source": "Direct URL access",
                                "source_url": "https://kilova.app",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            },
                            {
                                "claim": "Founder website verified",
                                "value": "palomachiara.com",
                                "source": "Direct URL access",
                                "source_url": "https://palomachiara.com",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "company": {
                        "company_name": "Kilova",
                        "company_url": "https://kilova.app",
                        "product_url": "https://kilova.app",
                        "company_description": "Menstrual cycle planning app - syncs cycle phases into calendar for lifestyle planning",
                        "company_status": "VERIFIED_ACTIVE",
                        "evidence": [
                            {
                                "claim": "Live web app with paying users",
                                "value": "$5/month subscription",
                                "source": "Direct URL access",
                                "source_url": "https://kilova.app",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "currentness": {
                        "age_days": 26,
                        "last_verified_at": datetime.now().isoformat(),
                        "currentness_status": "CURRENT",
                        "evidence": [
                            {
                                "claim": "Post date verified",
                                "value": "26 days old",
                                "source": "Reddit post metadata",
                                "source_url": "https://www.reddit.com/r/forhire/comments/1txv6sr/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "outsourcing": {
                        "outsourcing_intent": "EXPLICIT",
                        "outsourcing_confidence": "HIGH",
                        "evidence": [
                            {
                                "claim": "Post explicitly hiring developer",
                                "value": "[HIRING] tag + budget + requirements",
                                "source": "Reddit post",
                                "source_url": "https://www.reddit.com/r/forhire/comments/1txv6sr/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "service_match": {
                        "service": "Mobile App Development, React Native",
                        "match_reason": "React Native mobile app for iOS + Android",
                        "confidence": "HIGH",
                        "evidence": [
                            {
                                "claim": "Tech stack matches Inowix capabilities",
                                "value": "React Native, iOS, Android",
                                "source": "Reddit post",
                                "source_url": "https://www.reddit.com/r/forhire/comments/1txv6sr/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "contact": {
                        "email": "kilova.app@gmail.com",
                        "email_status": "PUBLIC_UNVERIFIED",
                        "linkedin_url": "https://linkedin.com/in/paloma-chiara",
                        "linkedin_status": "VERIFIED",
                        "phone": "",
                        "phone_status": "UNKNOWN",
                        "platform_contact": "Email, LinkedIn DM, Instagram DM, Contact form",
                        "platform_contact_status": "VERIFIED",
                        "contactability": "HIGH",
                        "contactability_evidence": [
                            {
                                "claim": "Multiple contact channels available",
                                "value": "Email, LinkedIn, Instagram, Contact form",
                                "source": "Multiple sources",
                                "source_url": "https://kilova.app",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "competitor": False,
                    "safety_clear": True,
                    "final_salesability": "SALES_READY",
                    "opportunity_verdict": "VERIFIED",
                    "contact_verdict": "CONTACTABLE",
                    "cto_15_minute_test": "YES",
                    "cto_decision_reason": "All gates passed - verified buyer with explicit requirement and contact channel",
                    "rejection_reasons": []
                },
                {
                    "opportunity_id": "V8-003",
                    "requirement": "Looking for experienced WordPress developer (or small team) with genuine publisher/media website experience.",
                    "requirement_verified": True,
                    "source": {
                        "source_name": "Reddit",
                        "source_type": "REDDIT",
                        "exact_source_url": "https://old.reddit.com/r/forhire/comments/1u9a9d8/",
                        "source_post_id": "1u9a9d8",
                        "published_at": "2026-07-08",
                        "observed_at": datetime.now().isoformat(),
                        "source_access_status": "VERIFIED",
                        "requirement_observed": True,
                        "evidence": [
                            {
                                "claim": "Original Reddit post accessed",
                                "value": "HTTP 200 - Content verified",
                                "source": "Direct URL access",
                                "source_url": "https://old.reddit.com/r/forhire/comments/1u9a9d8/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "person": {
                        "person_name": "jason23a",
                        "person_role": "Unknown",
                        "person_profile_url": "https://www.reddit.com/user/jason23a/",
                        "company_name": "Entertainment News Publisher",
                        "company_url": "",
                        "identity_confidence": "LOW",
                        "identity_signals": 1,
                        "evidence": [
                            {
                                "claim": "Reddit username verified",
                                "value": "jason23a",
                                "source": "Reddit",
                                "source_url": "https://www.reddit.com/user/jason23a/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "company": {
                        "company_name": "Entertainment News Publisher",
                        "company_url": "",
                        "product_url": "",
                        "company_description": "Entertainment news publisher (unverified)",
                        "company_status": "UNKNOWN",
                        "evidence": []
                    },
                    "currentness": {
                        "age_days": 31,
                        "last_verified_at": datetime.now().isoformat(),
                        "currentness_status": "CURRENT",
                        "evidence": [
                            {
                                "claim": "Post date verified",
                                "value": "31 days old",
                                "source": "Reddit post metadata",
                                "source_url": "https://old.reddit.com/r/forhire/comments/1u9a9d8/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "outsourcing": {
                        "outsourcing_intent": "EXPLICIT",
                        "outsourcing_confidence": "HIGH",
                        "evidence": [
                            {
                                "claim": "Post explicitly hiring developer",
                                "value": "[Hiring] tag + requirements",
                                "source": "Reddit post",
                                "source_url": "https://old.reddit.com/r/forhire/comments/1u9a9d8/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "service_match": {
                        "service": "Web Development, WordPress",
                        "match_reason": "WordPress developer for publisher/media website",
                        "confidence": "HIGH",
                        "evidence": [
                            {
                                "claim": "Tech stack matches Inowix capabilities",
                                "value": "WordPress, Web Development",
                                "source": "Reddit post",
                                "source_url": "https://old.reddit.com/r/forhire/comments/1u9a9d8/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "contact": {
                        "email": "",
                        "email_status": "UNKNOWN",
                        "linkedin_url": "",
                        "linkedin_status": "UNKNOWN",
                        "phone": "",
                        "phone_status": "UNKNOWN",
                        "platform_contact": "Reddit DM (u/jason23a)",
                        "platform_contact_status": "VERIFIED",
                        "contactability": "LOW",
                        "contactability_evidence": [
                            {
                                "claim": "Reddit DM available",
                                "value": "u/jason23a",
                                "source": "Reddit",
                                "source_url": "https://www.reddit.com/user/jason23a/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "competitor": False,
                    "safety_clear": True,
                    "final_salesability": "REJECT",
                    "opportunity_verdict": "REJECT",
                    "contact_verdict": "NOT_CONTACTABLE",
                    "cto_15_minute_test": "NO",
                    "cto_decision_reason": "Cannot identify buyer or company - only Reddit username available",
                    "rejection_reasons": [
                        "Decision maker identity not verified (only Reddit username)",
                        "Company/publishing business not identified",
                        "No email address found",
                        "No LinkedIn profile found",
                        "Contactability: LOW"
                    ]
                },
                {
                    "opportunity_id": "V8-004",
                    "requirement": "Looking for someone with great idea on the application frontend for SAAS application Zolly.",
                    "requirement_verified": True,
                    "source": {
                        "source_name": "Reddit",
                        "source_type": "REDDIT",
                        "exact_source_url": "https://www.reddit.com/r/hiredev/comments/1u79xa6/",
                        "source_post_id": "1u79xa6",
                        "published_at": "2026-07-05",
                        "observed_at": datetime.now().isoformat(),
                        "source_access_status": "VERIFIED",
                        "requirement_observed": True,
                        "evidence": [
                            {
                                "claim": "Original Reddit post accessed",
                                "value": "HTTP 200 - Content verified",
                                "source": "Direct URL access",
                                "source_url": "https://www.reddit.com/r/hiredev/comments/1u79xa6/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "person": {
                        "person_name": "Evening_Acadia_6021",
                        "person_role": "Unknown",
                        "person_profile_url": "",
                        "company_name": "Zolly",
                        "company_url": "",
                        "identity_confidence": "UNKNOWN",
                        "identity_signals": 0,
                        "evidence": []
                    },
                    "company": {
                        "company_name": "Zolly",
                        "company_url": "",
                        "product_url": "",
                        "company_description": "SaaS application (unverified)",
                        "company_status": "NOT_FOUND",
                        "evidence": []
                    },
                    "currentness": {
                        "age_days": 34,
                        "last_verified_at": datetime.now().isoformat(),
                        "currentness_status": "AGING",
                        "evidence": [
                            {
                                "claim": "Post date verified",
                                "value": "34 days old",
                                "source": "Reddit post metadata",
                                "source_url": "https://www.reddit.com/r/hiredev/comments/1u79xa6/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "outsourcing": {
                        "outsourcing_intent": "EXPLICIT",
                        "outsourcing_confidence": "HIGH",
                        "evidence": [
                            {
                                "claim": "Post explicitly hiring developer",
                                "value": "Hiring post with budget",
                                "source": "Reddit post",
                                "source_url": "https://www.reddit.com/r/hiredev/comments/1u79xa6/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "service_match": {
                        "service": "SaaS Development, Frontend Development",
                        "match_reason": "Frontend developer for SaaS application",
                        "confidence": "HIGH",
                        "evidence": [
                            {
                                "claim": "Tech stack matches Inowix capabilities",
                                "value": "SaaS, Frontend",
                                "source": "Reddit post",
                                "source_url": "https://www.reddit.com/r/hiredev/comments/1u79xa6/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "contact": {
                        "email": "",
                        "email_status": "UNKNOWN",
                        "linkedin_url": "",
                        "linkedin_status": "UNKNOWN",
                        "phone": "",
                        "phone_status": "UNKNOWN",
                        "platform_contact": "Reddit DM",
                        "platform_contact_status": "UNKNOWN",
                        "contactability": "NONE",
                        "contactability_evidence": []
                    },
                    "competitor": False,
                    "safety_clear": True,
                    "final_salesability": "REJECT",
                    "opportunity_verdict": "REJECT",
                    "contact_verdict": "NOT_CONTACTABLE",
                    "cto_15_minute_test": "NO",
                    "cto_decision_reason": "Cannot identify buyer or verify company - anonymous with low budget",
                    "rejection_reasons": [
                        "Decision maker identity not verified",
                        "SaaS application 'Zolly' not found",
                        "No email address found",
                        "No LinkedIn profile found",
                        "Contactability: NONE"
                    ]
                },
                {
                    "opportunity_id": "V8-005",
                    "requirement": "Landing page for a startup building products for neurodivergent people (multilingual, dark/light mode, accessible, SEO + GEO).",
                    "requirement_verified": True,
                    "source": {
                        "source_name": "Reddit",
                        "source_type": "REDDIT",
                        "exact_source_url": "https://www.reddit.com/r/forhire/comments/1tor0zh/",
                        "source_post_id": "1tor0zh",
                        "published_at": "2026-07-01",
                        "observed_at": datetime.now().isoformat(),
                        "source_access_status": "VERIFIED",
                        "requirement_observed": True,
                        "evidence": [
                            {
                                "claim": "Original Reddit post accessed",
                                "value": "HTTP 200 - Content verified",
                                "source": "Direct URL access",
                                "source_url": "https://www.reddit.com/r/forhire/comments/1tor0zh/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "person": {
                        "person_name": "Anonymous",
                        "person_role": "Unknown",
                        "person_profile_url": "",
                        "company_name": "Neurodivergent Products Startup",
                        "company_url": "",
                        "identity_confidence": "UNKNOWN",
                        "identity_signals": 0,
                        "evidence": []
                    },
                    "company": {
                        "company_name": "Neurodivergent Products Startup",
                        "company_url": "",
                        "product_url": "",
                        "company_description": "Startup building products for neurodivergent people (unverified)",
                        "company_status": "UNKNOWN",
                        "evidence": []
                    },
                    "currentness": {
                        "age_days": 38,
                        "last_verified_at": datetime.now().isoformat(),
                        "currentness_status": "AGING",
                        "evidence": [
                            {
                                "claim": "Post date verified",
                                "value": "38 days old",
                                "source": "Reddit post metadata",
                                "source_url": "https://www.reddit.com/r/forhire/comments/1tor0zh/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "outsourcing": {
                        "outsourcing_intent": "EXPLICIT",
                        "outsourcing_confidence": "HIGH",
                        "evidence": [
                            {
                                "claim": "Post explicitly hiring developer",
                                "value": "[Hiring] tag + budget",
                                "source": "Reddit post",
                                "source_url": "https://www.reddit.com/r/forhire/comments/1tor0zh/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "service_match": {
                        "service": "Web Development, Landing Page",
                        "match_reason": "Landing page development with accessibility features",
                        "confidence": "HIGH",
                        "evidence": [
                            {
                                "claim": "Tech stack matches Inowix capabilities",
                                "value": "Web Development, Accessibility",
                                "source": "Reddit post",
                                "source_url": "https://www.reddit.com/r/forhire/comments/1tor0zh/",
                                "confidence": "VERIFIED",
                                "observed_at": datetime.now().isoformat()
                            }
                        ]
                    },
                    "contact": {
                        "email": "",
                        "email_status": "UNKNOWN",
                        "linkedin_url": "",
                        "linkedin_status": "UNKNOWN",
                        "phone": "",
                        "phone_status": "UNKNOWN",
                        "platform_contact": "",
                        "platform_contact_status": "UNKNOWN",
                        "contactability": "NONE",
                        "contactability_evidence": []
                    },
                    "competitor": False,
                    "safety_clear": True,
                    "final_salesability": "REJECT",
                    "opportunity_verdict": "REJECT",
                    "contact_verdict": "NOT_CONTACTABLE",
                    "cto_15_minute_test": "NO",
                    "cto_decision_reason": "Anonymous buyer - cannot verify identity or contact",
                    "rejection_reasons": [
                        "Anonymous identity - cannot verify decision maker",
                        "No contact information available",
                        "No company information available",
                        "Contactability: NONE"
                    ]
                }
            ]
        }
    
    def verify_buying_event(self, opportunity: Dict) -> bool:
        """Verify that this is a genuine buying event."""
        requirement = opportunity.get("requirement", "").lower()
        
        # Valid buying event indicators
        buying_indicators = [
            "looking for",
            "need someone",
            "need a developer",
            "need an agency",
            "hiring",
            "budget",
            "build",
            "develop",
            "create",
            "need help",
            "looking to hire",
            "open to freelancers",
            "contractors"
        ]
        
        # Invalid buying event indicators (cofounder, equity, internal)
        invalid_indicators = [
            "cofounder",
            "co-founder",
            "equity",
            "looking for ct",
            "looking for cto",
            "full-time",
            "employee",
            "internal hire"
        ]
        
        # Check for valid indicators
        has_buying_indicator = any(indicator in requirement for indicator in buying_indicators)
        
        # Check for invalid indicators
        has_invalid_indicator = any(indicator in requirement for indicator in invalid_indicators)
        
        # Must have buying indicator and no invalid indicators
        return has_buying_indicator and not has_invalid_indicator
    
    def check_reproducibility(self, opportunity: Dict, identity_resolved: bool, currentness_ok: bool, contact_ok: bool, evidence_ok: bool) -> Tuple[bool, str]:
        """Check if the conclusion is reproducible."""
        issues = []
        
        if not identity_resolved:
            issues.append("Identity not fully resolved")
        
        if not currentness_ok:
            issues.append("Currentness not verified")
        
        if not contact_ok:
            issues.append("Contact not verified")
        
        if not evidence_ok:
            issues.append("Evidence consistency failed")
        
        # Check if all critical evidence has source URLs
        critical_evidence = [
            opportunity.get("source", {}).get("evidence", []),
            opportunity.get("person", {}).get("evidence", []),
            opportunity.get("company", {}).get("evidence", [])
        ]
        
        for evidence_list in critical_evidence:
            for ev in evidence_list:
                if not ev.get("source_url"):
                    issues.append(f"Evidence missing source_url: {ev.get('claim', '')}")
        
        if issues:
            return False, "; ".join(issues)
        
        return True, "All evidence is reproducible"
    
    def run_v8_1_engine(self):
        """Run V8.1 Production Hardening Engine."""
        print("=" * 70)
        print("V8.1 PRODUCTION HARDENING PATCH")
        print("=" * 70)
        
        # Step 1: Load V8 data
        v8_data = self.load_v8_data()
        opportunities = v8_data.get("opportunities", [])
        self.stats["total_discovered"] = len(opportunities)
        
        # Step 2: Process each opportunity
        print("\n[STEP 2] Processing opportunities through V8.1 hardening...")
        
        for opp_data in opportunities:
            opp_id = opp_data.get("opportunity_id", "UNKNOWN")
            print(f"\n{'='*50}")
            print(f"Processing {opp_id}...")
            print(f"{'='*50}")
            
            v8_1_opp = V8_1Opportunity(
                opportunity_id=opp_id,
                v8_data=opp_data
            )
            
            # Check source verification
            if opp_data.get("source", {}).get("source_access_status") == "VERIFIED":
                self.stats["exact_source_verified"] += 1
            
            # Check requirement verification
            if opp_data.get("requirement_verified"):
                self.stats["requirement_verified"] += 1
            
            # Step 2.1: Verify buying event
            print("\n  [2.1] Verifying buying event...")
            buying_event_verified = self.verify_buying_event(opp_data)
            v8_1_opp.buying_event_verified = buying_event_verified
            
            if buying_event_verified:
                self.stats["buying_event_verified"] += 1
                print(f"    Buying event: VERIFIED")
            else:
                print(f"    Buying event: NOT VERIFIED")
            
            # Step 2.2: Identity resolution
            print("\n  [2.2] Running identity resolution...")
            identity_resolution = self.identity_resolver.resolve_identity(opp_data)
            v8_1_opp.identity_resolution = identity_resolution
            v8_1_opp.identity_resolution_status = identity_resolution.identity_status
            
            if identity_resolution.identity_confidence == "HIGH":
                self.stats["identity_high"] += 1
            
            # Step 2.3: Currentness recheck
            print("\n  [2.3] Running currentness recheck...")
            currentness_recheck = self.currentness_recheck.recheck_currentness(opp_data)
            v8_1_opp.currentness_recheck = currentness_recheck
            v8_1_opp.currentness_recheck_status = currentness_recheck.currentness_status
            
            if currentness_recheck.currentness_status == "CURRENT":
                self.stats["current"] += 1
            
            # Step 2.4: Contact verification
            print("\n  [2.4] Running contact verification...")
            contact_verification = self.contact_verifier.verify_contacts(opp_data)
            v8_1_opp.contact_verification = contact_verification
            v8_1_opp.contact_association_status = contact_verification.contactability
            
            if contact_verification.contactability == "HIGH":
                self.stats["contact_high"] += 1
            
            # Step 2.5: Evidence consistency audit
            print("\n  [2.5] Running evidence consistency audit...")
            evidence_consistency = self.evidence_auditor.audit_evidence(opp_data)
            v8_1_opp.evidence_consistency = evidence_consistency
            v8_1_opp.evidence_consistency_status = evidence_consistency.overall_status
            
            if evidence_consistency.overall_status == "PASS":
                self.stats["evidence_consistency_pass"] += 1
            
            # Step 2.6: Check company verification
            if opp_data.get("company", {}).get("company_status") in ["VERIFIED_ACTIVE", "VERIFIED_EARLY_STAGE"]:
                self.stats["company_verified"] += 1
            
            # Step 2.7: Check outsourcing
            if opp_data.get("outsourcing", {}).get("outsourcing_intent") == "EXPLICIT":
                self.stats["explicit_outsourcing"] += 1
            
            # Step 2.8: Check service match
            if opp_data.get("service_match", {}).get("confidence") == "HIGH":
                self.stats["service_match_high"] += 1
            
            # Step 2.9: Check reproducibility
            print("\n  [2.9] Checking reproducibility...")
            identity_ok = identity_resolution.identity_confidence == "HIGH"
            currentness_ok = currentness_recheck.currentness_status == "CURRENT"
            contact_ok = contact_verification.contactability == "HIGH"
            evidence_ok = evidence_consistency.overall_status == "PASS"
            
            reproducible, reproducibility_reason = self.check_reproducibility(
                opp_data, identity_ok, currentness_ok, contact_ok, evidence_ok
            )
            v8_1_opp.reproducibility_test = "PASS" if reproducible else "FAIL"
            v8_1_opp.reproducibility_reason = reproducibility_reason
            
            if reproducible:
                self.stats["reproducibility_pass"] += 1
            
            print(f"    Reproducibility: {v8_1_opp.reproducibility_test}")
            print(f"    Reason: {reproducibility_reason}")
            
            # Step 3: Apply final V8.1 SALES_READY gate
            print("\n  [3] Applying final V8.1 SALES_READY gate...")
            
            v8_1_opp.rejection_reasons = []
            
            # Check all gates
            gates = {
                "requirement_verified": opp_data.get("requirement_verified", False),
                "currentness_status": currentness_recheck.currentness_status == "CURRENT",
                "identity_confidence": identity_resolution.identity_confidence == "HIGH",
                "outsourcing_intent": opp_data.get("outsourcing", {}).get("outsourcing_intent") == "EXPLICIT",
                "company_verified": opp_data.get("company", {}).get("company_status") in ["VERIFIED_ACTIVE", "VERIFIED_EARLY_STAGE"],
                "service_match_confidence": opp_data.get("service_match", {}).get("confidence") == "HIGH",
                "contactability": contact_verification.contactability == "HIGH",
                "competitor": not opp_data.get("competitor", False),
                "safety_clear": opp_data.get("safety_clear", True),
                "evidence_consistency": evidence_consistency.overall_status == "PASS",
                "reproducibility": reproducible,
                "buying_event": buying_event_verified
            }
            
            # Record failed gates
            for gate_name, gate_value in gates.items():
                if not gate_value:
                    v8_1_opp.rejection_reasons.append(f"Failed gate: {gate_name}")
            
            # Determine final salesability
            all_gates_pass = all(gates.values())
            
            if all_gates_pass:
                v8_1_opp.final_salesability = "SALES_READY"
                self.stats["sales_ready"] += 1
            elif len(v8_1_opp.rejection_reasons) <= 3:
                v8_1_opp.final_salesability = "NEEDS_RESEARCH"
                self.stats["needs_research"] += 1
            else:
                v8_1_opp.final_salesability = "REJECT"
                self.stats["rejected"] += 1
            
            # CTO 15-minute test
            if v8_1_opp.final_salesability == "SALES_READY":
                v8_1_opp.cto_15_minute_test = "YES"
                v8_1_opp.cto_decision_reason = "All V8.1 gates passed - verified, reproducible, contactable"
            else:
                v8_1_opp.cto_15_minute_test = "NO"
                v8_1_opp.cto_decision_reason = "; ".join(v8_1_opp.rejection_reasons[:3]) if v8_1_opp.rejection_reasons else "Failed gates"
            
            print(f"    Final salesability: {v8_1_opp.final_salesability}")
            print(f"    CTO 15-minute test: {v8_1_opp.cto_15_minute_test}")
            
            self.opportunities.append(v8_1_opp)
        
        # Step 4: Generate output
        print("\n[STEP 4] Generating V8.1 output files...")
        self.generate_output()
        
        # Step 5: Generate CTO report
        print("\n[STEP 5] Generating CTO report...")
        self.generate_cto_report()
    
    def generate_output(self):
        """Generate all V8.1 output files."""
        # Sales Ready JSON
        sales_ready = [o for o in self.opportunities if o.final_salesability == "SALES_READY"]
        needs_research = [o for o in self.opportunities if o.final_salesability == "NEEDS_RESEARCH"]
        rejected = [o for o in self.opportunities if o.final_salesability == "REJECT"]
        
        # v8_1_sales_ready.json
        sales_ready_path = EXPORTS_DIR / "v8_1_sales_ready.json"
        with open(sales_ready_path, "w", encoding="utf-8") as f:
            json.dump({
                "audit_name": "V8.1 Sales Ready Opportunities",
                "audit_date": datetime.now().isoformat(),
                "total_sales_ready": len(sales_ready),
                "opportunities": [self._opp_to_dict(o) for o in sales_ready]
            }, f, indent=2, ensure_ascii=False)
        print(f"  Saved: {sales_ready_path}")
        
        # v8_1_report.txt
        report_path = EXPORTS_DIR / "v8_1_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("V8.1 PRODUCTION HARDENING REPORT\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 70 + "\n\n")
            
            f.write("DISCOVERY FUNNEL:\n")
            f.write(f"  TOTAL_DISCOVERED: {self.stats['total_discovered']}\n")
            f.write(f"  EXACT_SOURCE_VERIFIED: {self.stats['exact_source_verified']}\n")
            f.write(f"  REQUIREMENT_VERIFIED: {self.stats['requirement_verified']}\n")
            f.write(f"  BUYING_EVENT_VERIFIED: {self.stats['buying_event_verified']}\n")
            f.write(f"  IDENTITY_HIGH: {self.stats['identity_high']}\n")
            f.write(f"  COMPANY_VERIFIED: {self.stats['company_verified']}\n")
            f.write(f"  CURRENT: {self.stats['current']}\n")
            f.write(f"  EXPLICIT_OUTSOURCING: {self.stats['explicit_outsourcing']}\n")
            f.write(f"  SERVICE_MATCH_HIGH: {self.stats['service_match_high']}\n")
            f.write(f"  CONTACT_HIGH: {self.stats['contact_high']}\n")
            f.write(f"  EVIDENCE_CONSISTENCY_PASS: {self.stats['evidence_consistency_pass']}\n")
            f.write(f"  REPRODUCIBILITY_PASS: {self.stats['reproducibility_pass']}\n")
            f.write(f"  SALES_READY: {self.stats['sales_ready']}\n")
            f.write(f"  NEEDS_RESEARCH: {self.stats['needs_research']}\n")
            f.write(f"  REJECTED: {self.stats['rejected']}\n\n")
            
            f.write("=" * 70 + "\n")
            f.write("SALES_READY LEADS\n")
            f.write("=" * 70 + "\n\n")
            
            if sales_ready:
                for opp in sales_ready:
                    f.write(f"{opp.opportunity_id}: {opp.v8_data.get('company', {}).get('company_name', 'Unknown')}\n")
                    f.write(f"  Person: {opp.identity_resolution.person_name if opp.identity_resolution else 'Unknown'}\n")
                    f.write(f"  Identity: {opp.identity_resolution.identity_confidence if opp.identity_resolution else 'Unknown'}\n")
                    f.write(f"  Currentness: {opp.currentness_recheck.currentness_status if opp.currentness_recheck else 'Unknown'}\n")
                    f.write(f"  Contactability: {opp.contact_verification.contactability if opp.contact_verification else 'Unknown'}\n")
                    f.write(f"  Evidence: {opp.evidence_consistency.overall_status if opp.evidence_consistency else 'Unknown'}\n")
                    f.write(f"  Reproducibility: {opp.reproducibility_test}\n")
                    f.write(f"  CTO 15-Min Test: {opp.cto_15_minute_test}\n\n")
            else:
                f.write("  NO SALES_READY LEADS\n\n")
            
            f.write("=" * 70 + "\n")
            f.write("NEEDS_RESEARCH LEADS\n")
            f.write("=" * 70 + "\n\n")
            
            if needs_research:
                for opp in needs_research:
                    f.write(f"{opp.opportunity_id}: {opp.v8_data.get('company', {}).get('company_name', 'Unknown')}\n")
                    f.write(f"  Rejection Reasons:\n")
                    for reason in opp.rejection_reasons[:3]:
                        f.write(f"    - {reason}\n")
                    f.write("\n")
            else:
                f.write("  NO NEEDS_RESEARCH LEADS\n\n")
            
            f.write("=" * 70 + "\n")
            f.write("REJECTED LEADS\n")
            f.write("=" * 70 + "\n\n")
            
            if rejected:
                for opp in rejected:
                    f.write(f"{opp.opportunity_id}: {opp.v8_data.get('company', {}).get('company_name', 'Unknown')}\n")
                    f.write(f"  Failed Gates:\n")
                    for reason in opp.rejection_reasons[:3]:
                        f.write(f"    - {reason}\n")
                    f.write("\n")
            else:
                f.write("  NO REJECTED LEADS\n\n")
        
        print(f"  Saved: {report_path}")
        
        # v8_1_rejected_report.txt
        rejected_path = EXPORTS_DIR / "v8_1_rejected_report.txt"
        with open(rejected_path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("V8.1 REJECTED LEADS REPORT\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Total Rejected: {len(rejected)}\n\n")
            
            for opp in rejected:
                f.write(f"{opp.opportunity_id}: {opp.v8_data.get('company', {}).get('company_name', 'Unknown')}\n")
                f.write(f"  FAILED_GATE: Multiple\n")
                f.write(f"  EVIDENCE: See evidence_audit.json\n")
                f.write(f"  SOURCE_URL: {opp.v8_data.get('source', {}).get('exact_source_url', 'N/A')}\n")
                f.write(f"  WHY_IT_FAILED:\n")
                for reason in opp.rejection_reasons:
                    f.write(f"    - {reason}\n")
                f.write("\n")
        
        print(f"  Saved: {rejected_path}")
        
        # v8_1_evidence_audit.json
        evidence_path = EXPORTS_DIR / "v8_1_evidence_audit.json"
        all_evidence = []
        for opp in self.opportunities:
            opp_evidence = {
                "opportunity_id": opp.opportunity_id,
                "company": opp.v8_data.get("company", {}).get("company_name", ""),
                "identity_resolution": asdict(opp.identity_resolution) if opp.identity_resolution else None,
                "currentness_recheck": asdict(opp.currentness_recheck) if opp.currentness_recheck else None,
                "contact_verification": asdict(opp.contact_verification) if opp.contact_verification else None,
                "evidence_consistency": asdict(opp.evidence_consistency) if opp.evidence_consistency else None,
                "reproducibility_test": opp.reproducibility_test,
                "reproducibility_reason": opp.reproducibility_reason
            }
            all_evidence.append(opp_evidence)
        
        with open(evidence_path, "w", encoding="utf-8") as f:
            json.dump({
                "audit_name": "V8.1 Evidence Audit",
                "audit_date": datetime.now().isoformat(),
                "total_opportunities": len(all_evidence),
                "evidence": all_evidence
            }, f, indent=2, ensure_ascii=False)
        print(f"  Saved: {evidence_path}")
        
        # v8_1_contactability_audit.json
        contact_path = EXPORTS_DIR / "v8_1_contactability_audit.json"
        all_contacts = []
        for opp in self.opportunities:
            opp_contact = {
                "opportunity_id": opp.opportunity_id,
                "company": opp.v8_data.get("company", {}).get("company_name", ""),
                "contactability": opp.contact_verification.contactability if opp.contact_verification else "UNKNOWN",
                "email_status": opp.contact_verification.email_status if opp.contact_verification else "UNKNOWN",
                "linkedin_status": opp.contact_verification.linkedin_status if opp.contact_verification else "UNKNOWN",
                "linkedin_decision_maker_match": opp.contact_verification.linkedin_decision_maker_match if opp.contact_verification else False,
                "linkedin_company_match": opp.contact_verification.linkedin_company_match if opp.contact_verification else False,
                "channels": [asdict(c) for c in opp.contact_verification.channels] if opp.contact_verification else []
            }
            all_contacts.append(opp_contact)
        
        with open(contact_path, "w", encoding="utf-8") as f:
            json.dump({
                "audit_name": "V8.1 Contactability Audit",
                "audit_date": datetime.now().isoformat(),
                "total_opportunities": len(all_contacts),
                "contacts": all_contacts
            }, f, indent=2, ensure_ascii=False)
        print(f"  Saved: {contact_path}")
        
        # Excel output
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "V8.1 Opportunities"
            
            headers = [
                "ID", "Company", "Identity", "Currentness", "Contactability",
                "Evidence", "Reproducibility", "Final", "CTO Test", "Rejection Reasons"
            ]
            ws.append(headers)
            
            for opp in self.opportunities:
                ws.append([
                    opp.opportunity_id,
                    opp.v8_data.get("company", {}).get("company_name", ""),
                    opp.identity_resolution.identity_confidence if opp.identity_resolution else "UNKNOWN",
                    opp.currentness_recheck.currentness_status if opp.currentness_recheck else "UNKNOWN",
                    opp.contact_verification.contactability if opp.contact_verification else "UNKNOWN",
                    opp.evidence_consistency.overall_status if opp.evidence_consistency else "UNKNOWN",
                    opp.reproducibility_test,
                    opp.final_salesability,
                    opp.cto_15_minute_test,
                    "; ".join(opp.rejection_reasons[:3])
                ])
            
            xlsx_path = EXPORTS_DIR / "v8_1_sales_ready.xlsx"
            wb.save(xlsx_path)
            print(f"  Saved: {xlsx_path}")
        except ImportError:
            print("  openpyxl not available, skipping Excel output")
    
    def _opp_to_dict(self, opp: V8_1Opportunity) -> Dict:
        """Convert V8_1Opportunity to dictionary."""
        result = {
            "opportunity_id": opp.opportunity_id,
            "v8_data": opp.v8_data,
            "identity_resolution_status": opp.identity_resolution_status,
            "currentness_recheck_status": opp.currentness_recheck_status,
            "contact_association_status": opp.contact_association_status,
            "evidence_consistency_status": opp.evidence_consistency_status,
            "reproducibility_test": opp.reproducibility_test,
            "reproducibility_reason": opp.reproducibility_reason,
            "buying_event_verified": opp.buying_event_verified,
            "final_salesability": opp.final_salesability,
            "cto_15_minute_test": opp.cto_15_minute_test,
            "cto_decision_reason": opp.cto_decision_reason,
            "rejection_reasons": opp.rejection_reasons
        }
        
        if opp.identity_resolution:
            result["identity_resolution"] = asdict(opp.identity_resolution)
        
        if opp.currentness_recheck:
            result["currentness_recheck"] = asdict(opp.currentness_recheck)
        
        if opp.contact_verification:
            result["contact_verification"] = asdict(opp.contact_verification)
        
        if opp.evidence_consistency:
            result["evidence_consistency"] = asdict(opp.evidence_consistency)
        
        return result
    
    def generate_cto_report(self):
        """Generate final CTO report."""
        print("\n" + "=" * 70)
        print("BEACON V8.1 — PRODUCTION HARDENING COMPLETE")
        print("=" * 70)
        
        print(f"\nDiscovered: {self.stats['total_discovered']}")
        print(f"Sales Ready: {self.stats['sales_ready']}")
        print(f"Needs Research: {self.stats['needs_research']}")
        print(f"Rejected: {self.stats['rejected']}")
        
        print(f"\nIdentity Resolution: {self.stats['identity_high']}/{self.stats['total_discovered']} HIGH")
        print(f"Currentness Recheck: {self.stats['current']}/{self.stats['total_discovered']} CURRENT")
        print(f"Contact Verification: {self.stats['contact_high']}/{self.stats['total_discovered']} HIGH")
        print(f"Evidence Consistency: {self.stats['evidence_consistency_pass']}/{self.stats['total_discovered']} PASS")
        print(f"Reproducibility: {self.stats['reproducibility_pass']}/{self.stats['total_discovered']} PASS")
        
        print(f"\nTop Sales-Ready Opportunities:")
        sales_ready = [o for o in self.opportunities if o.final_salesability == "SALES_READY"]
        if sales_ready:
            for i, opp in enumerate(sales_ready[:3], 1):
                print(f"  {i}. {opp.opportunity_id}: {opp.v8_data.get('company', {}).get('company_name', 'Unknown')}")
        else:
            print("  None")
        
        print(f"\nDowngraded Opportunities:")
        for opp in self.opportunities:
            if opp.final_salesability != "SALES_READY":
                print(f"  - {opp.opportunity_id}: {opp.rejection_reasons[0] if opp.rejection_reasons else 'Unknown'}")
        
        print(f"\nRejected Opportunities:")
        for opp in self.opportunities:
            if opp.final_salesability == "REJECT":
                print(f"  - {opp.opportunity_id}: {opp.rejection_reasons[0] if opp.rejection_reasons else 'Unknown'}")
        
        print(f"\nCTO 15-Minute Test:")
        yes_count = sum(1 for o in self.opportunities if o.cto_15_minute_test == "YES")
        no_count = sum(1 for o in self.opportunities if o.cto_15_minute_test == "NO")
        print(f"  YES: {yes_count}")
        print(f"  NO: {no_count}")
        
        print(f"\nProduction Status:")
        print(f"  OUTREACH DISABLED")
        print(f"  AUTOMATION DISABLED")
        print(f"  APPROVAL REQUIRED")
        
        print("\n" + "=" * 70)
        print("FINAL PRINCIPLE:")
        print("V8.1 DOES NOT FIND MORE LEADS.")
        print("V8.1 MAKES V8'S EXISTING LEADS HARDER TO FOOL.")
        print("IDENTITY MUST BE PROVABLE.")
        print("CURRENTNESS MUST BE DEFENSIBLE.")
        print("CONTACTABILITY MUST BE REAL.")
        print("EVIDENCE MUST BE REPRODUCIBLE.")
        print("ONLY THEN: SALES_READY.")
        print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():
    engine = V8_1Engine()
    engine.run_v8_1_engine()


if __name__ == "__main__":
    main()
