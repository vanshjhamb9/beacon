from lead_enrichment.extractors.contacts import ContactExtractor
from lead_enrichment.models.types import EnrichmentOpportunityInput, WebsiteFetchResult, WebsitePageContent
from lead_enrichment.scoring.engine import EnrichmentScorer
from lead_enrichment.validators.enrichment import EnrichmentValidator
from tests.lead_enrichment.test_enrichment_pipeline import make_input


def test_contact_extractor_finds_public_emails_and_phones() -> None:
    website = WebsiteFetchResult(
        domain="acme.example",
        fetched=True,
        pages=[
            WebsitePageContent(
                url="https://acme.example/contact",
                page_type="contact",
                html="Email sales@acme.example Phone +1 415 555 1212",
                text="Email sales@acme.example Phone +1 415 555 1212",
            )
        ],
    )
    contacts = ContactExtractor().extract(make_input(company_attributes={}), website)
    assert any(contact.value == "sales@acme.example" for contact in contacts)
    assert any(contact.kind.value == "business_phone" for contact in contacts)


def test_validator_rejects_invalid_emails() -> None:
    from lead_enrichment.models.types import ContactEntry, ContactKind, EnrichmentSourceType

    validator = EnrichmentValidator()
    contacts = validator.validate_contacts(
        [
            ContactEntry(
                kind=ContactKind.COMPANY_EMAIL,
                value="not-an-email",
                confidence=50.0,
                source=EnrichmentSourceType.COMPANY_WEBSITE,
            ),
            ContactEntry(
                kind=ContactKind.COMPANY_EMAIL,
                value="ok@acme.example",
                confidence=80.0,
                source=EnrichmentSourceType.COMPANY_WEBSITE,
            ),
        ]
    )
    assert len(contacts) == 1
    assert contacts[0].value == "ok@acme.example"


def test_scorer_increases_with_richer_inputs() -> None:
    from lead_enrichment.models.types import (
        ContactEntry,
        ContactKind,
        EnrichedCompanyProfile,
        EnrichmentSourceType,
        PersonEntry,
        TechnologyEntry,
    )

    scorer = EnrichmentScorer()
    weak = scorer.score(
        profile=EnrichedCompanyProfile(company_name="Acme"),
        contacts=[],
        technologies=[],
        decision_makers=[],
    )
    strong = scorer.score(
        profile=EnrichedCompanyProfile(
            company_name="Acme",
            website="https://acme.example",
            domain="acme.example",
            industry="saas",
            description="Ops platform",
            location="Austin",
            country="USA",
            founded_year=2018,
            employee_count_estimate=100,
            company_size_range="51-200",
        ),
        contacts=[
            ContactEntry(
                kind=ContactKind.COMPANY_EMAIL,
                value="hello@acme.example",
                confidence=90.0,
                source=EnrichmentSourceType.COMPANY_WEBSITE,
            ),
            ContactEntry(
                kind=ContactKind.BUSINESS_PHONE,
                value="+15125550100",
                confidence=80.0,
                source=EnrichmentSourceType.COMPANY_WEBSITE,
            ),
            ContactEntry(
                kind=ContactKind.ROLE_BASED_EMAIL,
                value="sales@acme.example",
                confidence=85.0,
                source=EnrichmentSourceType.COMPANY_WEBSITE,
            ),
        ],
        technologies=[
            TechnologyEntry(
                name="Stripe",
                category="payment_gateways",
                confidence=88.0,
                source=EnrichmentSourceType.PUBLIC_JS,
            )
        ],
        decision_makers=[
            PersonEntry(
                name="Jane Founder",
                role="CEO",
                confidence=90.0,
                source=EnrichmentSourceType.COMPANY_WEBSITE,
            )
        ],
    )
    assert strong.overall_enrichment_confidence > weak.overall_enrichment_confidence


def test_make_input_is_typed_enrichment_opportunity() -> None:
    item = make_input()
    assert isinstance(item, EnrichmentOpportunityInput)
