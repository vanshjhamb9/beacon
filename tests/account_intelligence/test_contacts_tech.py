from datetime import UTC, datetime

import pytest

from account_intelligence.buying_committee.engine import BuyingCommitteeEngine, ContactValidationEngine, ROLE_ALIASES
from account_intelligence.models.types import AccountIntelligenceInput, CommitteeRole, ObservedContact
from account_intelligence.technology_enrichment.engine import TECH_MAP, TechnologyEnrichmentEngine


def test_never_invent_contacts_empty() -> None:
    item = AccountIntelligenceInput(company_name="Empty Co", observed_contacts=[])
    assert BuyingCommitteeEngine().discover(item) == []
    assert ContactValidationEngine().validate([], domain="empty.co") == []


def test_reject_invalid_email_not_rewrite() -> None:
    results = ContactValidationEngine().validate(
        [
            ObservedContact(full_name="Pat", role="CEO", business_email="not-an-email", source="web", evidence=[]),
        ],
        domain="x.com",
    )
    assert results[0].business_email is None
    assert "invalid_email_format" in results[0].conflicts


def test_domain_match_accepts() -> None:
    results = ContactValidationEngine().validate(
        [
            ObservedContact(
                full_name="Pat",
                role="CEO",
                business_email="pat@acme.com",
                linkedin_url="https://linkedin.com/in/pat",
                source="web",
                evidence=[],
                observed_at=datetime.now(UTC),
            )
        ],
        domain="acme.com",
    )
    assert results[0].domain_match is True
    assert results[0].accepted is True


@pytest.mark.parametrize("alias,role", ROLE_ALIASES)
def test_role_alias_maps(alias: str, role: str) -> None:
    members = BuyingCommitteeEngine().discover(
        AccountIntelligenceInput(
            company_name="R",
            observed_contacts=[ObservedContact(full_name="A Person", role=alias, source="s", evidence=[])],
        )
    )
    assert members[0].role == role


@pytest.mark.parametrize("role", list(CommitteeRole))
def test_committee_roles_enum(role: CommitteeRole) -> None:
    assert isinstance(role.value, str)


@pytest.mark.parametrize("category,patterns", list(TECH_MAP.items()))
def test_tech_categories_detectable(category: str, patterns: tuple[str, ...]) -> None:
    tech = TechnologyEnrichmentEngine().enrich(
        AccountIntelligenceInput(company_name="T", html_hints=[patterns[0]], tech_hints=[])
    )
    assert getattr(tech, category)
