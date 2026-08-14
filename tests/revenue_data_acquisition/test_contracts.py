"""RDAP v1 contract tests — source roles, recovery, dossier, yield, API shapes."""

from __future__ import annotations

from revenue_data_acquisition import (
    SCORING_VERSION,
    RevenueDataAcquisitionPipeline,
    RdapRebuildEngine,
    SourceClass,
)
from revenue_data_acquisition.connector_quality.engine import ConnectorQualityEngine
from revenue_data_acquisition.contact_recovery.engine import ContactRecoveryEngine
from revenue_data_acquisition.dossier.engine import CompanyDossierEngine
from revenue_data_acquisition.dm_recovery.engine import DecisionMakerRecoveryEngine
from revenue_data_acquisition.models.types import AttributedValue, ConnectorGrade, RecoveryReason
from revenue_data_acquisition.recovery.engine import RdapRecoveryEngine
from revenue_data_acquisition.revenue_yield.engine import RevenueYieldEngine
from revenue_data_acquisition.source_roles.engine import SourceClassificationEngine
from revenue_data_acquisition.website_discovery.engine import OfficialWebsiteDiscoveryPipeline


def test_scoring_version():
    assert SCORING_VERSION == "rdap-v1"


def test_product_hunt_is_identity_only():
    roles = SourceClassificationEngine().roles("product_hunt")
    assert roles == [SourceClass.IDENTITY]
    assert SourceClassificationEngine().can_create_identity("product_hunt")


def test_github_is_identity_and_tech():
    roles = SourceClassificationEngine().roles("github_trending")
    assert SourceClass.IDENTITY in roles
    assert SourceClass.TECH in roles


def test_rss_news_cannot_create_identity():
    assert SourceClassificationEngine().roles("rss") == [SourceClass.NEWS]
    assert not SourceClassificationEngine().can_create_identity("rss")


def test_hn_community_cannot_create_identity():
    assert not SourceClassificationEngine().can_create_identity("hacker_news")
    assert not SourceClassificationEngine().can_create_identity("reddit")


def test_pipeline_no_website_no_fabricate():
    snap = RevenueDataAcquisitionPipeline().evaluate(
        {"signal_id": "s1", "source": "reddit", "title": "talk"},
        recover_contacts=False,
        recover_dms=False,
    )
    assert snap.website is None
    assert snap.emails == []
    assert snap.decision_makers == []
    assert not snap.can_create_identity
    assert RecoveryReason.WEBSITE_MISSING in snap.recovery


def test_pipeline_identity_with_official_site():
    snap = RevenueDataAcquisitionPipeline().evaluate(
        {
            "signal_id": "s2",
            "source": "product_hunt",
            "title": "Acme Launch",
            "official_website": "https://acme.example",
            "metadata": {"official_domain": "acme.example", "company_hints": ["Acme"]},
        },
        recover_contacts=False,
        recover_dms=False,
    )
    assert snap.can_create_identity
    assert snap.domain == "acme.example" or snap.website
    assert snap.dossier is not None
    assert snap.scoring_version == "rdap-v1"


def test_website_discovery_never_guesses():
    website, domain, trail = OfficialWebsiteDiscoveryPipeline().discover(
        {"source": "hacker_news", "title": "random", "url": "https://news.ycombinator.com/item?id=1"},
        fetch_github=False,
    )
    assert website is None
    assert domain is None
    assert isinstance(trail, list)


def test_contact_recovery_empty_without_website():
    assert ContactRecoveryEngine().recover("") == []


def test_dm_recovery_empty_without_website():
    assert DecisionMakerRecoveryEngine().recover("") == []


def test_recovery_reasons():
    reasons = RdapRecoveryEngine().reasons(website=None, emails=[], dms=[], confidence=10)
    assert RecoveryReason.WEBSITE_MISSING in reasons
    assert RecoveryReason.LOW_CONFIDENCE in reasons


def test_dossier_sales_ready_requires_email_dm_signals():
    dossier = CompanyDossierEngine().build(
        company_id="c1",
        identity={"trade_name": "Acme", "legal_name": "Acme Inc"},
        website="https://acme.example",
        domain="acme.example",
        emails=[AttributedValue(value="info@acme.example", source="company_website", confidence=90, verified=True)],
        decision_makers=[{"name": "Ada", "role": "CEO", "url": "https://acme.example/team", "confidence": 80}],
        payload={"title": "Acme Launch", "source": "product_hunt", "metadata": {}},
        collector="product_hunt",
    )
    assert dossier.sales_ready
    assert dossier.trust_score >= 80
    assert dossier.contacts


def test_dossier_not_sales_ready_without_dm():
    dossier = CompanyDossierEngine().build(
        company_id="c2",
        identity={"trade_name": "Beta"},
        website="https://beta.example",
        domain="beta.example",
        emails=[AttributedValue(value="hello@beta.example", source="company_website", confidence=90, verified=True)],
        decision_makers=[],
        payload={"title": "Beta", "source": "product_hunt"},
        collector="product_hunt",
    )
    assert not dossier.sales_ready


def test_connector_quality_grades():
    scores = ConnectorQualityEngine().score(
        [
            {"connector": "product_hunt", "candidate": True, "company": True, "website": True, "business_email": True, "confidence": 80},
            {"connector": "rss", "candidate": False, "confidence": 20},
        ]
    )
    by = {s.connector: s for s in scores}
    assert by["product_hunt"].grade in {
        ConnectorGrade.EXCELLENT,
        ConnectorGrade.GOOD,
        ConnectorGrade.AVERAGE,
        ConnectorGrade.POOR,
    }
    assert by["rss"].grade == ConnectorGrade.DISABLED or by["rss"].verified_companies == 0


def test_revenue_yield_compute():
    yields = RevenueYieldEngine().compute(
        [
            {"connector": "github_trending", "company": True, "website": True, "business_email": True, "revenue_ready": True},
            {"connector": "github_trending", "company": True, "website": True},
        ]
    )
    assert yields[0].connector == "github_trending"
    assert yields[0].signals == 2
    assert yields[0].revenue_ready == 1


def test_funnel_and_audit():
    pipe = RevenueDataAcquisitionPipeline()
    snaps = [
        pipe.evaluate(
            {
                "signal_id": f"a{i}",
                "source": "product_hunt",
                "title": f"Co{i}",
                "official_website": f"https://co{i}.dev",
                "metadata": {"official_domain": f"co{i}.dev"},
            },
            recover_contacts=False,
            recover_dms=False,
        )
        for i in range(5)
    ]
    audit = RdapRebuildEngine().audit(
        before={"verified_companies": 0, "business_emails": 0, "decision_makers": 0, "sales_ready": 0, "revenue_ready": 0},
        after={"verified_companies": 5, "business_emails": 5, "decision_makers": 5, "sales_ready": 5, "revenue_ready": 5},
        snaps=snaps,
        collector_rows=[{"connector": "product_hunt", "company": True, "website": True} for _ in range(5)],
        top_rr=[{"name": "Co0"}],
    )
    assert audit.vansh_ready_answer == "YES"
    assert len(audit.funnel) == 8
    assert audit.funnel[0].name == "Signals"


def test_audit_no_when_below_threshold():
    audit = RdapRebuildEngine().audit(
        before={},
        after={"verified_companies": 2, "business_emails": 1, "decision_makers": 0, "sales_ready": 0, "revenue_ready": 0},
        snaps=[],
        collector_rows=[],
    )
    assert audit.vansh_ready_answer == "NO"


def test_evaluate_many():
    snaps = RevenueDataAcquisitionPipeline().evaluate_many(
        [{"signal_id": f"m{i}", "source": "rss", "title": f"n{i}"} for i in range(10)]
    )
    assert len(snaps) == 10
    assert all(not s.can_create_identity for s in snaps)
