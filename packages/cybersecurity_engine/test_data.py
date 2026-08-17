"""Test data for BEACON Cybersecurity Discovery Engine.

Sample buying signals to verify the full pipeline.
"""

from cybersecurity_engine.sources import RawSignal
from cybersecurity_engine.models import Contact, Company, CompanySize
from datetime import UTC, datetime


SAMPLE_SIGNALS = [
    # P0 — Active Buying Events
    RawSignal(
        source="reddit",
        source_tier=2,
        url="https://www.reddit.com/r/netsec/comments/example1",
        title="Looking for penetration testing company for our SaaS",
        content="We're a B2B SaaS company preparing for enterprise sales. Our CISO is looking for a penetration testing company to do a full security assessment before our Series B. Need web application and API security testing. Budget: $15k-25k. Timeline: 4 weeks.",
        author="cto_throwaway",
        published_at=datetime(2026, 8, 10, tzinfo=UTC),
        score=15,
        metadata={"subreddit": "netsec", "reddit_id": "example1"},
    ),
    RawSignal(
        source="hacker_news",
        source_tier=2,
        url="https://news.ycombinator.com/item?id=example2",
        title="Need VAPT before SOC 2 audit",
        content="Our fintech startup needs a VAPT (vulnerability assessment and penetration test) before our SOC 2 Type 2 audit next month. Looking for a security testing vendor who can deliver a report within 3 weeks. Any recommendations?",
        author="fintech_founder",
        published_at=datetime(2026, 8, 12, tzinfo=UTC),
        score=12,
        metadata={"hn_id": "example2", "points": 25},
    ),
    RawSignal(
        source="web_search",
        source_tier=2,
        url="https://example-forum.com/post/security-audit-rfp",
        title="Security Audit RFP for Healthcare SaaS",
        content="RFP: We are seeking proposals for a comprehensive security audit and penetration test for our healthcare SaaS platform. Must have experience with HIPAA compliance. Enterprise customer requires security assessment before contract signing.",
        author="procurement_team",
        published_at=datetime(2026, 8, 8, tzinfo=UTC),
        score=20,
        metadata={"query": "security testing rfp"},
    ),

    # P1 — Verified Security Pain
    RawSignal(
        source="reddit",
        source_tier=2,
        url="https://www.reddit.com/r/netsec/comments/example3",
        title="Found SQL injection in production - need remediation",
        content="Our security team just discovered a critical SQL injection vulnerability in our payment API. We need immediate remediation and retesting. Previous pentest missed this. Looking for an external security team to help fix and validate.",
        author="security_engineer",
        published_at=datetime(2026, 8, 14, tzinfo=UTC),
        score=18,
        metadata={"subreddit": "netsec", "reddit_id": "example3"},
    ),
    RawSignal(
        source="company_blog",
        source_tier=1,
        url="https://www.healthtech-company.com/security",
        title="Security Update - Compliance Deadline Approaching",
        content="We are updating our security posture to meet new compliance requirements. Our ISO 27001 certification deadline is approaching and we need external security assessment support. Enterprise customers require penetration testing documentation.",
        author="ciso",
        published_at=datetime(2026, 8, 5, tzinfo=UTC),
        score=22,
        metadata={"company_url": "healthtech-company.com"},
    ),

    # P2 — High-Potential Outbound
    RawSignal(
        source="web_search",
        source_tier=3,
        url="https://techcrunch.com/fintech-series-b",
        title="Fintech Startup Raises $20M Series B",
        content="PayFlow, a B2B fintech SaaS company, has raised $20M in Series B funding. The company plans to expand into enterprise markets and hire security engineers. They handle sensitive payment data and will need SOC 2 compliance.",
        author="tech_reporter",
        published_at=datetime(2026, 8, 1, tzinfo=UTC),
        score=8,
        metadata={"query": "fintech series b funding"},
    ),
    RawSignal(
        source="hacker_news",
        source_tier=3,
        url="https://news.ycombinator.com/item?id=example4",
        title="Launch: AI-powered developer tools platform",
        content="We just launched DevTools AI, a platform that helps developers write better code. We handle sensitive code data and are expanding into enterprise. Looking to hire security engineers and prepare for SOC 2 certification.",
        author="devtools_founder",
        published_at=datetime(2026, 8, 13, tzinfo=UTC),
        score=10,
        metadata={"hn_id": "example4", "points": 15},
    ),
]


def get_sample_signals() -> list[RawSignal]:
    """Return sample signals for testing."""
    return SAMPLE_SIGNALS


# Sample verified contacts for testing
SAMPLE_CONTACTS = {
    "saas_company_1": Contact(
        name="Alex Chen",
        role="CTO",
        email="alex@secureflow.io",
        email_status="verified",
        email_evidence="Found on company website /about page",
        linkedin_url="https://linkedin.com/in/alexchen-cto",
        linkedin_status="verified",
        phone="+1-555-0123",
        phone_status="verified",
        identity_confidence=95.0,
    ),
    "fintech_company_1": Contact(
        name="Sarah Williams",
        role="Head of Security",
        email="sarah.williams@payflow.com",
        email_status="verified",
        email_evidence="Found on company security page",
        linkedin_url="https://linkedin.com/in/sarahwilliams-sec",
        linkedin_status="verified",
        phone="",
        phone_status="unverified",
        identity_confidence=90.0,
    ),
    "healthcare_company_1": Contact(
        name="Dr. James Morrison",
        role="CEO",
        email="james@healthtech-solutions.com",
        email_status="verified",
        email_evidence="Found on company about page",
        linkedin_url="https://linkedin.com/in/jamesmorrison-ceo",
        linkedin_status="verified",
        phone="+1-555-0456",
        phone_status="verified",
        identity_confidence=92.0,
    ),
}


# Sample verified companies for testing
SAMPLE_COMPANIES = {
    "saas_company_1": Company(
        name="SecureFlow",
        url="secureflow.io",
        country="United States",
        industry="SaaS",
        company_size=CompanySize.MEDIUM,
        employee_count=85,
        description="B2B SaaS workflow automation platform",
        technologies=["React", "Node.js", "AWS", "PostgreSQL"],
    ),
    "fintech_company_1": Company(
        name="PayFlow",
        url="payflow.com",
        country="United States",
        industry="Fintech",
        company_size=CompanySize.MEDIUM,
        employee_count=120,
        description="B2B payment processing SaaS",
        technologies=["Python", "Django", "GCP", "Stripe"],
    ),
    "healthcare_company_1": Company(
        name="HealthTech Solutions",
        url="healthtech-solutions.com",
        country="United States",
        industry="Healthtech",
        company_size=CompanySize.SMALL,
        employee_count=45,
        description="Healthcare patient management platform",
        technologies=["React", "Python", "AWS", "HIPAA"],
    ),
}
