"""RDAP deterministic param matrix — 800+ cases."""

from __future__ import annotations

import time

import pytest

from revenue_data_acquisition import RevenueDataAcquisitionPipeline, RdapRebuildEngine, SourceClass
from revenue_data_acquisition.connector_quality.engine import ConnectorQualityEngine
from revenue_data_acquisition.dossier.engine import CompanyDossierEngine
from revenue_data_acquisition.models.types import AttributedValue
from revenue_data_acquisition.recovery.engine import RdapRecoveryEngine
from revenue_data_acquisition.revenue_yield.engine import RevenueYieldEngine
from revenue_data_acquisition.source_roles.engine import SourceClassificationEngine

SOURCES = (
    "product_hunt",
    "github_trending",
    "hacker_news",
    "reddit",
    "devto",
    "rss",
    "indie_hackers",
    "sec_edgar",
)

CASES: list[tuple] = []
for i in range(640):
    source = SOURCES[i % len(SOURCES)]
    with_site = source in {"product_hunt", "github_trending"} and i % 2 == 0
    domain = f"co{i}.dev" if with_site else None
    CASES.append((i, source, domain, f"Co{i}"))

assert len(CASES) >= 640


@pytest.mark.parametrize("i,source,domain,name", CASES)
def test_rdap_param(i, source, domain, name):
    payload = {
        "signal_id": f"rdap-{i}",
        "title": name if source != "github_trending" else f"GitHub: org/{name.lower()}",
        "source": source,
        "url": f"https://example.com/{i}",
        "metadata": {"company_hints": [name]},
    }
    if domain:
        payload["official_website"] = f"https://{domain}"
        payload["metadata"]["repo_homepage"] = f"https://{domain}"
        payload["metadata"]["official_domain"] = domain
    snap = RevenueDataAcquisitionPipeline().evaluate(
        payload, fetch_github=False, recover_contacts=False, recover_dms=False
    )
    assert snap.signal_id == f"rdap-{i}"
    assert snap.scoring_version == "rdap-v1"
    can_id = SourceClassificationEngine().can_create_identity(source)
    assert snap.can_create_identity == can_id
    if domain and can_id:
        assert snap.domain == domain or snap.website
    if source in {"hacker_news", "reddit", "rss"} and not domain:
        assert snap.website is None
        assert not snap.can_create_identity


ROLE_CASES = [
    ("product_hunt", (SourceClass.IDENTITY,)),
    ("github", (SourceClass.IDENTITY, SourceClass.TECH)),
    ("github_trending", (SourceClass.IDENTITY, SourceClass.TECH)),
    ("rss", (SourceClass.NEWS,)),
    ("hacker_news", (SourceClass.COMMUNITY,)),
    ("hn", (SourceClass.COMMUNITY,)),
    ("reddit", (SourceClass.COMMUNITY,)),
    ("devto", (SourceClass.COMMUNITY, SourceClass.TECH)),
    ("twitter", (SourceClass.SOCIAL,)),
    ("funding", (SourceClass.FUNDING, SourceClass.INTENT)),
]


@pytest.mark.parametrize("source,expected", ROLE_CASES)
def test_source_roles_table(source, expected):
    assert tuple(SourceClassificationEngine().roles(source)) == expected


@pytest.mark.parametrize("i", range(80))
def test_recovery_param(i):
    website = f"https://x{i}.com" if i % 2 == 0 else None
    emails = [AttributedValue(value=f"info@x{i}.com")] if i % 3 == 0 and website else []
    dms = [{"name": f"P{i}"}] if i % 5 == 0 and website else []
    reasons = RdapRecoveryEngine().reasons(website=website, emails=emails, dms=dms, confidence=float(i % 100))
    if not website:
        assert any(r.value == "Website Missing" for r in reasons)
    if website and not emails:
        assert any(r.value == "Email Missing" for r in reasons)


@pytest.mark.parametrize("i", range(60))
def test_dossier_param(i):
    has_email = i % 2 == 0
    has_dm = i % 3 == 0
    dossier = CompanyDossierEngine().build(
        company_id=f"c{i}",
        identity={"trade_name": f"Brand{i}"},
        website=f"https://brand{i}.com",
        domain=f"brand{i}.com",
        emails=(
            [AttributedValue(value=f"info@brand{i}.com", source="company_website", confidence=90, verified=True)]
            if has_email
            else []
        ),
        decision_makers=[{"name": f"CEO{i}", "role": "CEO", "url": f"https://brand{i}.com/team"}] if has_dm else [],
        payload={"title": f"Brand{i} Launch", "source": "product_hunt", "metadata": {}},
        collector="product_hunt",
    )
    if has_email and has_dm:
        assert dossier.sales_ready
    else:
        assert not dossier.sales_ready
    assert 0 <= dossier.trust_score <= 99


@pytest.mark.parametrize("i", range(40))
def test_connector_metrics_param(i):
    rows = [
        {
            "connector": f"src{i % 5}",
            "candidate": True,
            "company": i % 2 == 0,
            "website": i % 2 == 0,
            "business_email": i % 4 == 0,
            "decision_maker": i % 5 == 0,
            "revenue_ready": i % 10 == 0,
            "confidence": 50 + (i % 40),
            "duplicate": 1 if i % 7 == 0 else 0,
        }
        for _ in range(8)
    ]
    scores = ConnectorQualityEngine().score(rows)
    assert scores
    yields = RevenueYieldEngine().compute(rows)
    assert yields[0].signals == 8


def test_benchmark_1000_signals_under_5s():
    payloads = []
    for i in range(1000):
        payloads.append(
            {
                "signal_id": f"b-{i}",
                "title": f"GitHub: org/p{i}",
                "source": "github_trending",
                "url": f"https://github.com/org/p{i}",
                "metadata": {"repo_homepage": f"https://p{i}.io", "company_hints": [f"P{i}"], "official_domain": f"p{i}.io"},
                "official_website": f"https://p{i}.io",
            }
        )
    t0 = time.perf_counter()
    snaps = RevenueDataAcquisitionPipeline().evaluate_many(
        payloads, fetch_github=False, recover_contacts=False, recover_dms=False
    )
    elapsed = time.perf_counter() - t0
    assert len(snaps) == 1000
    assert elapsed < 5.0


def test_benchmark_500_dossiers_under_5s():
    engine = CompanyDossierEngine()
    t0 = time.perf_counter()
    for i in range(500):
        engine.build(
            company_id=f"d{i}",
            identity={"trade_name": f"D{i}"},
            website=f"https://d{i}.io",
            domain=f"d{i}.io",
            emails=[AttributedValue(value=f"info@d{i}.io", source="company_website", confidence=90, verified=True)],
            decision_makers=[{"name": f"N{i}", "role": "CEO", "url": f"https://d{i}.io/about"}],
            payload={"title": f"D{i}", "source": "product_hunt"},
            collector="product_hunt",
        )
    assert time.perf_counter() - t0 < 5.0


def test_benchmark_connector_metrics_under_2s():
    rows = [
        {
            "connector": f"c{i % 20}",
            "candidate": True,
            "company": True,
            "website": True,
            "business_email": i % 2 == 0,
            "decision_maker": i % 3 == 0,
            "revenue_ready": i % 10 == 0,
            "confidence": 70,
        }
        for i in range(5000)
    ]
    t0 = time.perf_counter()
    scores = ConnectorQualityEngine().score(rows)
    yields = RevenueYieldEngine().compute(rows)
    elapsed = time.perf_counter() - t0
    assert scores and yields
    assert elapsed < 2.0


def test_funnel_regression_shape():
    snaps = RevenueDataAcquisitionPipeline().evaluate_many(
        [
            {
                "signal_id": f"f{i}",
                "source": "product_hunt",
                "title": f"F{i}",
                "official_website": f"https://f{i}.com",
                "metadata": {"official_domain": f"f{i}.com"},
            }
            for i in range(20)
        ],
        recover_contacts=False,
        recover_dms=False,
    )
    funnel = RdapRebuildEngine().funnel(
        snaps,
        extras={
            "verified_companies": 20,
            "business_emails": 5,
            "decision_makers": 2,
            "sales_ready": 1,
            "revenue_ready": 0,
        },
    )
    assert [s.name for s in funnel] == [
        "Signals",
        "Identity Candidates",
        "Official Websites",
        "Verified Companies",
        "Business Emails",
        "Decision Makers",
        "Sales Ready",
        "Revenue Ready",
    ]
