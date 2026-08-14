from decision_discovery.extractors.channels import ContactChannelExtractor
from decision_discovery.extractors.people import DecisionMakerExtractor
from decision_discovery.extractors.roles import is_plausible_person_name, normalize_role
from decision_discovery.matching.buyer import BuyerMatcher
from decision_discovery.models.types import DecisionRole


def test_normalize_role_covers_required_titles() -> None:
    assert normalize_role("Chief Technology Officer")[0] == DecisionRole.CTO
    assert normalize_role("Head of Customer Support")[0] == DecisionRole.HEAD_OF_CUSTOMER_SUPPORT
    assert normalize_role("AI Lead")[0] == DecisionRole.AI_LEAD


def test_rejects_placeholder_names() -> None:
    assert is_plausible_person_name("Jane Founder")
    assert not is_plausible_person_name("Unknown")
    assert not is_plausible_person_name("Acme Logistics COO")


def test_people_extractor_skips_fabricated_company_persona() -> None:
    makers = DecisionMakerExtractor().extract(
        [
            {
                "name": "Acme Logistics COO",
                "role": "COO",
                "confidence": 55.0,
                "source": "beacon_revenue",
            },
            {
                "name": "Pat Support",
                "role": "Head of Support",
                "confidence": 77.0,
                "source": "company_website",
                "source_url": "https://example.com/team",
            },
        ]
    )
    assert len(makers) == 1
    assert makers[0].name == "Pat Support"


def test_channel_extractor_rejects_personal_email_domains() -> None:
    channels = ContactChannelExtractor().extract_channels(
        contacts=[
            {
                "kind": "company_email",
                "value": "founder@gmail.com",
                "confidence": 90.0,
                "source": "company_website",
                "is_public": True,
            },
            {
                "kind": "role_based_email",
                "value": "support@acme.example",
                "confidence": 90.0,
                "source": "company_website",
                "source_url": "https://acme.example/contact",
                "is_public": True,
            },
        ],
        profiles=[],
        lead_profile={},
        domain="acme.example",
    )
    values = {item.value for item in channels}
    assert "founder@gmail.com" not in values
    assert "support@acme.example" in values


def test_buyer_matcher_maps_services() -> None:
    matcher = BuyerMatcher()
    assert DecisionRole.HEAD_OF_CUSTOMER_SUPPORT in matcher.preferred_roles("COMAI Support Automation", None)
    assert DecisionRole.CTO in matcher.preferred_roles("AI Automation Platform", None)
    assert DecisionRole.FOUNDER in matcher.preferred_roles("Mobile App Development", None)
    assert DecisionRole.COO in matcher.preferred_roles("ERP Modernization", None)
    assert DecisionRole.MARKETING_HEAD in matcher.preferred_roles("Website Redesign", None)
