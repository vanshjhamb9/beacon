import pytest

from account_intelligence import AccountIntelligencePipeline
from account_intelligence.models.types import AccountIntelligenceInput, ObservedContact
from account_intelligence.business_profile.engine import IndustryBenchmarkEngine


@pytest.mark.parametrize("industry", ["SaaS", "Healthcare", "Fintech", "Ecommerce", "Other"])
def test_industry_benchmarks(industry: str) -> None:
    b = IndustryBenchmarkEngine().for_industry(industry if industry != "Other" else None)
    assert b.industry
    assert 0 <= b.avg_digital_maturity <= 100


@pytest.mark.parametrize(
    "employees,funding,round_name,stage",
    [
        (5, None, None, "startup"),
        (25, "seed", "seed", "early"),
        (80, "Series A", "series_a", "growth"),
        (600, "Series C", "series_c", "scale"),
    ],
)
def test_growth_stages(employees: int, funding: str | None, round_name: str | None, stage: str) -> None:
    d = AccountIntelligencePipeline().process(
        AccountIntelligenceInput(
            company_name="G",
            employee_count=employees,
            funding=funding,
            latest_funding_round=round_name,
            html_hints=["https"],
        )
    )
    assert d.business.growth_stage == stage


@pytest.mark.parametrize(
    "role",
    [
        "Founder",
        "CEO",
        "CTO",
        "COO",
        "CIO",
        "VP Engineering",
        "Engineering Manager",
        "Head of AI",
        "Product Manager",
        "Head of Operations",
        "Marketing Head",
        "Sales Head",
        "Customer Success",
        "Support Head",
        "Finance Head",
        "HR Head",
        "Legal",
        "IT Manager",
    ],
)
def test_committee_priority_for_roles(role: str) -> None:
    d = AccountIntelligencePipeline().process(
        AccountIntelligenceInput(
            company_name="C",
            observed_contacts=[ObservedContact(full_name="N", role=role, source="s", evidence=[])],
        )
    )
    assert d.buying_committee[0].role
    assert d.buying_committee[0].priority > 0
    assert d.buying_committee[0].fabricated is False


def test_missing_fields_not_fabricated() -> None:
    d = AccountIntelligencePipeline().process(AccountIntelligenceInput(company_name="Sparse"))
    assert d.profile.employee_count.value is None
    assert d.profile.revenue_estimate.value is None
    assert d.buying_committee == []
    assert all(not c.accepted for c in d.verified_contacts) or d.verified_contacts == []
