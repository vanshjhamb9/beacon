"""EROWD benchmark — synthetic multi-source corpus (≥1800 signals)."""

from __future__ import annotations

import pytest

from entity_resolution.pipelines.engine import ErowdPipeline
from entity_resolution.rebuild.engine import ErowdRebuildEngine


def _ph(i: int, *, with_site: bool = True) -> dict:
    slug = f"product{i}"
    domain = f"{slug}.io"
    payload = {
        "signal_id": f"ph-{i}",
        "title": f"Product{i} — AI ops platform",
        "body": f"Product{i} automates enterprise workflows with AI agents for support teams.",
        "url": f"https://www.producthunt.com/posts/{slug}",
        "source": "product_hunt",
        "metadata": {"company_hints": [f"Product{i}"]},
        "industry": "Software",
    }
    if with_site:
        payload["official_website"] = f"https://{domain}"
        payload["metadata"]["official_website"] = f"https://{domain}"
        payload["website_verified"] = True
        payload["website_title"] = f"Product{i}"
    return payload


def _gh(i: int, *, with_site: bool = True) -> dict:
    payload = {
        "signal_id": f"gh-{i}",
        "title": f"GitHub: org{i}/repo{i}",
        "body": f"Open source toolkit from Org{i}",
        "url": f"https://github.com/org{i}/repo{i}",
        "source": "github_trending",
        "metadata": {"company_hints": [f"Org{i}"]},
        "industry": "Software",
    }
    if with_site:
        payload["github_homepage"] = f"https://org{i}.dev"
        payload["metadata"]["repo_homepage"] = f"https://org{i}.dev"
        payload["website_verified"] = True
        payload["website_title"] = f"Org{i}"
    return payload


def _rss(i: int, *, with_site: bool = False) -> dict:
    payload = {
        "signal_id": f"rss-{i}",
        "title": f"Article about startup {i}",
        "body": "Publisher coverage of market trends",
        "url": f"https://techblog.example/articles/{i}",
        "source": "rss",
        "metadata": {"article_only": not with_site},
    }
    if with_site:
        payload["canonical_website"] = f"https://startup{i}.com"
        payload["metadata"]["canonical_website"] = f"https://startup{i}.com"
        payload["metadata"]["company_hints"] = [f"Startup{i}"]
        payload["website_verified"] = True
        payload["website_title"] = f"Startup{i}"
        payload["industry"] = "Software"
    return payload


def _reddit(i: int) -> dict:
    return {
        "signal_id": f"rd-{i}",
        "title": f"Looking for tools {i}",
        "body": "discussion only",
        "url": f"https://reddit.com/r/startups/{i}",
        "source": "reddit",
    }


def _hn(i: int) -> dict:
    return {
        "signal_id": f"hn-{i}",
        "title": f"Ask HN: opinions {i}",
        "body": "thread",
        "url": f"https://news.ycombinator.com/item?id={i}",
        "source": "hacker_news",
    }


def _devto(i: int, *, with_site: bool = False) -> dict:
    payload = {
        "signal_id": f"dv-{i}",
        "title": f"Building agents {i}",
        "body": "tutorial post",
        "url": f"https://dev.to/user/post-{i}",
        "source": "devto",
    }
    if with_site:
        payload["devto_website"] = f"https://devshop{i}.com"
        payload["website_verified"] = True
        payload["website_title"] = f"Devshop{i}"
        payload["metadata"] = {"company_hints": [f"Devshop{i}"]}
        payload["industry"] = "Software"
    return payload


@pytest.fixture(scope="module")
def corpus() -> list[dict]:
    signals: list[dict] = []
    # 500 Product Hunt — 120 with official websites (admission candidates)
    for i in range(500):
        signals.append(_ph(i, with_site=i < 120))
    # 500 GitHub — 80 with repo homepage
    for i in range(500):
        signals.append(_gh(i, with_site=i < 80))
    # 200 RSS — 30 with org website
    for i in range(200):
        signals.append(_rss(i, with_site=i < 30))
    # 200 Reddit — signal only
    for i in range(200):
        signals.append(_reddit(i))
    # 200 HN — signal only
    for i in range(200):
        signals.append(_hn(i))
    # 200 Dev.to — 20 with profile website
    for i in range(200):
        signals.append(_devto(i, with_site=i < 20))
    assert len(signals) == 1800
    return signals


@pytest.fixture(scope="module")
def report(corpus: list[dict]):
    pipe = ErowdPipeline()
    snaps = [pipe.evaluate(s) for s in corpus]
    return ErowdRebuildEngine().build(snaps), snaps


def test_corpus_sizes(corpus: list[dict]):
    by = {}
    for s in corpus:
        by[s["source"]] = by.get(s["source"], 0) + 1
    assert by["product_hunt"] == 500
    assert by["github_trending"] == 500
    assert by["rss"] == 200
    assert by["reddit"] == 200
    assert by["hacker_news"] == 200
    assert by["devto"] == 200


def test_discovery_rate(report):
    metrics, _ = report
    assert metrics.official_websites >= 120
    assert metrics.discovery_rate > 0
    # With-site fixtures should discover
    assert metrics.discovery_rate >= 10.0


def test_verification_and_admission(report):
    metrics, snaps = report
    assert metrics.verified_companies >= 100
    assert metrics.admitted >= 100
    assert metrics.false_positives == 0
    # Reddit/HN never admitted
    for s in snaps:
        if s.source in {"reddit", "hacker_news"}:
            assert not s.admission.allow_create_company


def test_no_platform_domains_as_identity(report):
    _, snaps = report
    forbidden = {"producthunt.com", "github.com", "reddit.com", "news.ycombinator.com", "dev.to", "techcrunch.com"}
    for s in snaps:
        if s.admission.allow_create_company:
            assert s.website.domain not in forbidden
            assert s.identity.domain not in forbidden


def test_identity_confidence_distribution(report):
    metrics, _ = report
    dist = metrics.identity_confidence_distribution
    assert sum(dist.values()) == 1800
    assert dist["90-100"] >= 100


def test_funnel_shape_vs_target(report):
    """Target shape: 1000 signals → 150 candidates → 120 websites → 100 verified.

    Benchmark uses 1800 signals with known website evidence density.
    """
    metrics, _ = report
    assert metrics.entity_candidates >= 150
    assert metrics.official_websites >= 120
    assert metrics.verified_companies >= 100
    # sales_ready left to downstream engines (0 here by design)
    assert metrics.sales_ready == 0


def test_source_precision_signal_only_zero(report):
    metrics, _ = report
    assert metrics.source_precision["reddit"]["admitted"] == 0
    assert metrics.source_precision["hacker_news"]["admitted"] == 0
    # OFC Priority 4 — RSS never admits until ER is reliable
    assert metrics.source_precision["rss"]["admitted"] == 0
