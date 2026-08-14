from uuid import uuid4

from decision_discovery import DecisionDiscoveryPipeline
from decision_discovery.models.types import DecisionDiscoveryInput


def make_input(**overrides: object) -> DecisionDiscoveryInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "opportunity_id": uuid4(),
        "company_name": "Acme Logistics",
        "domain": "acmelogistics.example",
        "website": "https://acmelogistics.example",
        "opportunity_score": 84.0,
        "opportunity_status": "high_intent",
        "business_pain": "manual support workflows",
        "recommended_service": "AI Automation",
        "buyer_persona": "CTO",
        "revenue_recommendation": {
            "recommended_service": "AI Automation",
            "buyer_persona": "CTO",
        },
        "lead_profile": {
            "company_profile": {"website": "https://acmelogistics.example"},
            "team_insights": {"engineering_team_estimate": 12, "operations_team_estimate": 8},
        },
        "verification_payload": {"decision": "ready"},
        "context_intelligence": {"hiring_pattern": "Engineering expansion"},
        "known_people": [],
        "enrichment_people": [
            {
                "name": "Jane Founder",
                "role": "CEO",
                "department": "Leadership",
                "work_email": "ceo@acmelogistics.example",
                "confidence": 88.0,
                "source": "company_website",
                "source_url": "https://acmelogistics.example/about",
                "is_public": True,
            },
            {
                "name": "Sam Engineer",
                "role": "CTO",
                "department": "Engineering",
                "confidence": 82.0,
                "source": "company_website",
                "source_url": "https://acmelogistics.example/team",
                "is_public": True,
            },
        ],
        "enrichment_contacts": [
            {
                "kind": "role_based_email",
                "value": "hello@acmelogistics.example",
                "confidence": 80.0,
                "source": "company_website",
                "source_url": "https://acmelogistics.example/contact",
                "is_public": True,
            },
            {
                "kind": "business_phone",
                "value": "+1 512 555 0100",
                "confidence": 75.0,
                "source": "company_website",
                "source_url": "https://acmelogistics.example/contact",
                "is_public": True,
            },
        ],
        "enrichment_profiles": [
            {
                "platform": "linkedin",
                "url": "https://www.linkedin.com/company/acme-logistics",
                "confidence": 90.0,
                "source": "company_website",
            }
        ],
    }
    payload.update(overrides)
    return DecisionDiscoveryInput(**payload)  # type: ignore[arg-type]


def test_discovery_pipeline_selects_cto_for_ai_automation() -> None:
    result = DecisionDiscoveryPipeline().process(make_input())

    assert result.company_name == "Acme Logistics"
    assert result.primary_decision_maker is not None
    assert result.primary_decision_maker.role == "CTO"
    assert result.secondary_decision_maker is not None
    assert result.public_emails
    assert result.best_outreach_sequence
    assert result.confidence.overall_discovery_score > 0
    assert all(item.source_url or "@" in item.value or item.value.startswith("http") or sum(c.isdigit() for c in item.value) >= 7 for item in result.contact_channels)


def test_discovery_pipeline_does_not_invent_contacts() -> None:
    result = DecisionDiscoveryPipeline().process(
        make_input(
            enrichment_contacts=[],
            enrichment_profiles=[],
            enrichment_people=[
                {
                    "name": "Alex Operator",
                    "role": "COO",
                    "confidence": 70.0,
                    "source": "beacon_intelligence",
                    "is_public": True,
                }
            ],
        )
    )

    assert result.primary_decision_maker is not None
    assert result.primary_decision_maker.work_email is None
    assert "invent" not in result.reason.lower()
    if not result.contact_channels:
        assert result.no_public_contact_message == "No verified public business contact available."
