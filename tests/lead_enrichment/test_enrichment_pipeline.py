from uuid import uuid4

from lead_enrichment import EnrichmentPipeline
from lead_enrichment.connectors.dns_mx import DnsMxConnector
from lead_enrichment.connectors.website import WebsiteConnector
from lead_enrichment.models.types import EnrichmentOpportunityInput


def make_input(**overrides: object) -> EnrichmentOpportunityInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "opportunity_id": uuid4(),
        "company_name": "Acme Logistics",
        "domain": "acmelogistics.example",
        "website": "https://acmelogistics.example",
        "opportunity_score": 86.0,
        "opportunity_status": "qualified",
        "opportunity_narrative": "Acme is scaling operations and seeking automation support.",
        "industry": "logistics",
        "description": "B2B logistics automation platform.",
        "location": "Austin, TX",
        "country": "USA",
        "company_attributes": {
            "company_email": "hello@acmelogistics.example",
            "business_phone": "+1 512 555 0199",
            "employee_count": 120,
            "founded_year": 2016,
        },
        "context_intelligence": {
            "company_stage": "scaling",
            "technology_stack": ["Salesforce", "AWS"],
            "hiring_pattern": "Engineering expansion",
        },
        "technology_signals": [
            {"technology": "OpenAI", "category": "ai", "confidence": 81.0, "adoption_signal": "pilot"}
        ],
        "pains": [{"category": "automation", "value": "manual ops workflows", "confidence": 84.0}],
        "goals": [{"category": "efficiency", "value": "reduce cycle time", "confidence": 78.0}],
        "known_people": [{"name": "Jane Founder", "title": "CEO", "linkedin_url": "https://www.linkedin.com/in/janefounder"}],
        "revenue_recommendation": {
            "recommended_service": "AI Automation",
            "business_pain": "manual ops workflows",
            "buyer_persona": "COO",
            "estimated_budget_range": "medium",
            "priority": "high",
            "conversation_angle": "Lead with ops cycle-time reduction.",
            "confidence": 82.0,
        },
        "opportunity_evidence": [
            {"category": "hiring", "summary": "Hiring Software Engineers for automation", "confidence": 77.0}
        ],
    }
    payload.update(overrides)
    return EnrichmentOpportunityInput(**payload)  # type: ignore[arg-type]


def _website_fetcher(url: str) -> tuple[int, str]:
    html = """
    <html><body>
      <a href="https://www.linkedin.com/company/acme-logistics">LinkedIn</a>
      <a href="https://github.com/acmelogistics">GitHub</a>
      Contact us at sales@acmelogistics.example or +1 (512) 555-0100.
      Jane Founder - CEO
      We are hiring Software Engineers and Support Specialists.
      Founded in 2016. Team of 120 employees in Austin, TX.
      <script src="https://js.stripe.com/v3/"></script>
      <script src="https://www.googletagmanager.com/gtag/js"></script>
    </body></html>
    """
    return 200, html


def test_enrichment_pipeline_returns_sales_ready_lead_profile() -> None:
    pipeline = EnrichmentPipeline(
        website=WebsiteConnector(fetcher=_website_fetcher),
        dns=DnsMxConnector(resolver=lambda _domain: ["aspmx.l.google.com"]),
    )
    result = pipeline.process(make_input())

    assert result.company_name == "Acme Logistics"
    assert result.opportunity_score == 86.0
    assert result.recommended_service == "AI Automation"
    assert result.business_pain
    assert result.buyer_persona
    assert result.company_profile.domain == "acmelogistics.example"
    assert result.company_profile.website
    assert result.public_contact_information
    assert result.decision_makers
    assert result.technology_stack
    assert result.social_profiles
    assert result.enrichment_confidence.overall_enrichment_confidence > 0
    assert result.source_attribution
    assert result.evidence_chain
    assert result.why_now
    assert result.best_outreach_angle
    assert result.processing_latency_ms >= 0.0
    assert all(item.source for item in result.source_attribution)


def test_enrichment_pipeline_works_without_website_fetch() -> None:
    pipeline = EnrichmentPipeline(
        website=WebsiteConnector(enabled=False),
        dns=DnsMxConnector(enabled=False),
    )
    result = pipeline.process(make_input())

    assert result.company_profile.company_name == "Acme Logistics"
    assert result.enrichment_confidence.profile_completeness > 0
    assert result.public_contact_information
    assert any(contact.value == "hello@acmelogistics.example" for contact in result.public_contact_information)
