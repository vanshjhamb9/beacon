"""IGF benchmark corpus — identity vs conversation separation."""

import pytest

from identity_graph import IdentityResolutionPipeline, IgfRebuildEngine


def _gh(i: int, *, with_site: bool) -> dict:
    domain = f"ghco{i}.dev" if with_site else None
    meta = {"company_hints": [f"GhCo{i}"], "owner": f"org{i}", "owner_type": "Organization"}
    payload = {
        "signal_id": f"gh-{i}",
        "title": f"GitHub: org{i}/product-{i}",
        "source": "github_trending",
        "url": f"https://github.com/org{i}/product-{i}",
        "metadata": meta,
        "website_verified": with_site,
    }
    if domain:
        payload["official_website"] = f"https://{domain}"
        payload["github_homepage"] = f"https://{domain}"
        meta["repo_homepage"] = f"https://{domain}"
    return payload


def _ph(i: int, *, with_site: bool) -> dict:
    domain = f"phco{i}.app" if with_site else None
    payload = {
        "signal_id": f"ph-{i}",
        "title": f"PhCo{i}",
        "source": "product_hunt",
        "url": f"https://www.producthunt.com/products/phco{i}",
        "metadata": {"company_hints": [f"PhCo{i}"]},
        "website_verified": with_site,
    }
    if domain:
        payload["official_website"] = f"https://{domain}"
        payload["homepage"] = f"https://{domain}"
    return payload


def _hn(i: int) -> dict:
    return {
        "signal_id": f"hn-{i}",
        "title": f"Show HN item {i}",
        "source": "hacker_news",
        "url": f"https://news.ycombinator.com/item?id={i}",
        "official_website": f"https://hn{i}.dev",
        "website_verified": True,
    }


@pytest.fixture(scope="module")
def corpus() -> list[dict]:
    signals: list[dict] = []
    for i in range(200):
        signals.append(_gh(i, with_site=i < 120))
    for i in range(200):
        signals.append(_ph(i, with_site=i < 80))
    for i in range(100):
        signals.append(_hn(i))
    assert len(signals) == 500
    return signals


@pytest.fixture(scope="module")
def report(corpus: list[dict]):
    snaps = IdentityResolutionPipeline().evaluate_many(corpus)
    return IgfRebuildEngine().build(snaps), snaps


def test_benchmark_websites(report):
    metrics, _ = report
    assert metrics.official_websites >= 100
    assert metrics.verified_companies >= 100


def test_hn_never_admitted(report):
    _, snaps = report
    for s in snaps:
        if s.source == "hacker_news":
            assert not s.admission.allow_create_company


def test_precision(report):
    metrics, _ = report
    assert metrics.identity_precision > 0
    assert metrics.signals == 500
