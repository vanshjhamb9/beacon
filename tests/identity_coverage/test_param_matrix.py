"""ICE deterministic param matrix — 700+ cases."""

from __future__ import annotations

import pytest

from identity_coverage import IdentityCoveragePipeline
from identity_coverage.alias.engine import AliasResolutionEngine
from identity_coverage.github.engine import GitHubIdentityResolver
from identity_coverage.product_hunt.engine import ProductHuntApiResolver
from identity_coverage.ranking.engine import EvidenceRankingEngine
from identity_coverage.models.types import CoverageEvidence
from identity_coverage.rebuild.engine import IceRebuildEngine

CASES: list[tuple] = []
for i in range(720):
    source = ("github_trending", "product_hunt", "hacker_news", "reddit", "devto", "rss")[i % 6]
    with_site = source in {"github_trending", "product_hunt"} and i % 2 == 0
    domain = f"co{i}.dev" if with_site else None
    CASES.append((i, source, domain, f"Co{i}"))

assert len(CASES) >= 700


@pytest.mark.parametrize("i,source,domain,name", CASES)
def test_ice_param(i, source, domain, name):
    payload = {
        "signal_id": f"ice-{i}",
        "title": name if source != "github_trending" else f"GitHub: org/{name.lower()}",
        "source": source,
        "url": f"https://example.com/{i}",
        "metadata": {"company_hints": [name], "ph_post_id": str(1000 + i) if source == "product_hunt" else None},
    }
    if domain:
        payload["official_website"] = f"https://{domain}"
        payload["metadata"]["repo_homepage"] = f"https://{domain}"
        payload["metadata"]["official_domain"] = domain
    snap = IdentityCoveragePipeline().evaluate(payload, fetch_github=False, crawl_website=False)
    assert snap.signal_id == f"ice-{i}"
    if domain and source in {"github_trending", "product_hunt"}:
        assert snap.domain == domain
        assert snap.admitted_hint
    if source in {"hacker_news", "reddit", "rss", "devto"} and not domain:
        assert snap.website is None


@pytest.mark.parametrize("i", range(80))
def test_alias_param(i):
    node = AliasResolutionEngine().resolve(
        {"title": f"Brand{i}", "metadata": {"company_hints": [f"brand{i}", f"Brand {i}"]}},
        domain=f"brand{i}.com",
    )
    assert node.official_domain == f"brand{i}.com"


@pytest.mark.parametrize("i", range(60))
def test_rank_param(i):
    ranked = EvidenceRankingEngine().rank(
        [
            CoverageEvidence(field="website", value=f"https://a{i}.com", confidence=70, source="a", priority=20),
            CoverageEvidence(
                field="website", value=f"https://b{i}.com", confidence=90, source="b", priority=10, verification=True
            ),
        ]
    )
    assert ranked["website"].value == f"https://b{i}.com"


def test_benchmark_500_under_5s():
    import time

    payloads = []
    for i in range(500):
        payloads.append(
            {
                "signal_id": f"b-{i}",
                "title": f"GitHub: org/p{i}",
                "source": "github_trending",
                "url": f"https://github.com/org/p{i}",
                "metadata": {"repo_homepage": f"https://p{i}.io", "company_hints": [f"P{i}"]},
                "official_website": f"https://p{i}.io",
            }
        )
    t0 = time.perf_counter()
    snaps = IdentityCoveragePipeline().evaluate_many(payloads)
    elapsed = time.perf_counter() - t0
    assert len(snaps) == 500
    assert elapsed < 5.0
    funnel = IceRebuildEngine().funnel(snaps, extras={"companies": 500, "business_emails": 0, "decision_makers": 0})
    assert funnel.stages[0].count == 500


@pytest.mark.parametrize("i", range(40))
def test_gh_rejects_github_io(i):
    ev = GitHubIdentityResolver().collect(
        {
            "source": "github_trending",
            "metadata": {"repo_homepage": f"https://user{i}.github.io/proj"},
        }
    )
    assert not any(e.field == "website" for e in ev)


@pytest.mark.parametrize("i", range(40))
def test_ph_post_id_extract(i):
    pid = ProductHuntApiResolver(token="").extract_post_id(
        {"metadata": {}, "content": f'<a href="https://www.producthunt.com/r/p/{10000+i}?app_id=1">Link</a>'}
    )
    assert pid == str(10000 + i)
