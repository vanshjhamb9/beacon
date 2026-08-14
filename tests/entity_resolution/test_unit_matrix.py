"""EROWD v1 — unit matrix."""

from __future__ import annotations

from entity_resolution import COMPANY_REQUIRES_OFFICIAL_WEBSITE, SCORING_VERSION
from entity_resolution.entity_resolver.engine import EntityResolverEngine
from entity_resolution.identity_confidence.engine import IDENTITY_THRESHOLD, ErowdIdentityConfidenceEngine
from entity_resolution.models.types import ErowdVerdict, RejectionReason
from entity_resolution.pipelines.engine import ErowdPipeline
from entity_resolution.rebuild.engine import ErowdRebuildEngine
from entity_resolution.website_discovery.engine import OfficialWebsiteDiscoveryEngine


def _ph(**overrides):
    base = {
        "signal_id": "sig-1",
        "title": "Screenpipe — AI screen recording for teams",
        "body": "Screenpipe helps companies automate workflows with AI agents.",
        "url": "https://www.producthunt.com/posts/screenpipe",
        "source": "product_hunt",
        "metadata": {"company_hints": ["Screenpipe"], "official_website": "https://screenpipe.com"},
        "official_website": "https://screenpipe.com",
        "website_verified": True,
        "website_title": "Screenpipe",
        "industry": "Software",
    }
    base.update(overrides)
    return base


def test_version():
    assert SCORING_VERSION == "erowd-v1"
    assert COMPANY_REQUIRES_OFFICIAL_WEBSITE is True
    assert IDENTITY_THRESHOLD == 90.0


def test_promptql_normalizes_aliases():
    entity = EntityResolverEngine().resolve(
        {
            "title": "PromptQL — analytics",
            "source": "product_hunt",
            "metadata": {"company_hints": ["Prompt QL", "promptql.ai"]},
        }
    )
    assert "promptql" in entity.normalized_key.replace(" ", "")
    keys = {entity.normalized_key, *[a.lower() for a in entity.aliases]}
    assert any("prompt" in k for k in keys)


def test_product_hunt_admitted_with_official_site():
    snap = ErowdPipeline().evaluate(_ph())
    assert snap.verdict == ErowdVerdict.ADMITTED
    assert snap.admission.allow_create_company
    assert snap.website.domain == "screenpipe.com"
    assert snap.score.score >= 90
    assert snap.attribution.discovery_source


def test_product_hunt_listing_url_never_identity():
    discovered = OfficialWebsiteDiscoveryEngine().discover(
        {
            "source": "product_hunt",
            "url": "https://www.producthunt.com/posts/promptql",
            "metadata": {"domain": "producthunt.com"},
            "official_website": "https://promptql.ai",
        }
    )
    assert discovered.discovered
    assert discovered.domain == "promptql.ai"
    assert "producthunt" not in discovered.domain


def test_hn_signal_only():
    snap = ErowdPipeline().evaluate(
        {
            "signal_id": "hn1",
            "title": "Show HN: Cool tool",
            "body": "built something",
            "url": "https://news.ycombinator.com/item?id=1",
            "source": "hacker_news",
        }
    )
    assert snap.verdict == ErowdVerdict.SIGNAL_ONLY
    assert not snap.admission.allow_create_company
    assert RejectionReason.SOURCE_SIGNAL_ONLY in snap.admission.reasons


def test_reddit_signal_only():
    snap = ErowdPipeline().evaluate(
        {
            "signal_id": "r1",
            "title": "Anyone using automation tools?",
            "body": "Looking for advice",
            "url": "https://reddit.com/r/startups/1",
            "source": "reddit",
        }
    )
    assert not snap.admission.allow_create_company
    assert snap.verdict == ErowdVerdict.SIGNAL_ONLY


def test_github_repo_url_rejected_without_homepage():
    snap = ErowdPipeline().evaluate(
        {
            "signal_id": "g1",
            "title": "GitHub: foo/awesome-list",
            "body": "collection of tools",
            "url": "https://github.com/foo/awesome-list",
            "source": "github_trending",
            "metadata": {"domain": "github.com", "company_hints": ["foo"]},
        }
    )
    assert not snap.admission.allow_create_company
    assert snap.website.discovered is False or snap.website.domain != "github.com"


def test_github_with_repo_homepage_admitted():
    snap = ErowdPipeline().evaluate(
        {
            "signal_id": "g2",
            "title": "GitHub: acme/agent-kit",
            "body": "Acme agent kit for enterprise automation",
            "url": "https://github.com/acme/agent-kit",
            "source": "github_trending",
            "metadata": {"company_hints": ["Acme"], "repo_homepage": "https://acme.dev"},
            "github_homepage": "https://acme.dev",
            "website_verified": True,
            "website_title": "Acme",
            "industry": "Software",
        }
    )
    assert snap.admission.allow_create_company
    assert snap.website.domain == "acme.dev"


def test_rss_article_only_rejected():
    snap = ErowdPipeline().evaluate(
        {
            "signal_id": "rss1",
            "title": "OpenAI raises funds",
            "body": "news article",
            "url": "https://techcrunch.com/2026/openai",
            "source": "rss",
            "metadata": {"article_only": True},
        }
    )
    assert not snap.admission.allow_create_company
    assert RejectionReason.NO_OFFICIAL_WEBSITE in snap.admission.reasons or RejectionReason.ARTICLE_ONLY in snap.admission.reasons


def test_rss_signal_only_under_ofc_policy():
    """OFC Priority 4: RSS stays signal-only until entity resolution is reliable."""
    snap = ErowdPipeline().evaluate(
        {
            "signal_id": "rss2",
            "title": "Acme ships v2",
            "body": "Acme release notes",
            "url": "https://blog.acme.io/v2",
            "source": "rss",
            "metadata": {"company_hints": ["Acme"], "canonical_website": "https://acme.io"},
            "canonical_website": "https://acme.io",
            "website_verified": True,
            "website_title": "Acme",
            "industry": "Software",
        }
    )
    assert not snap.admission.allow_create_company
    assert snap.verdict == ErowdVerdict.SIGNAL_ONLY
    assert snap.website.domain == "acme.io"


def test_ofc_skip_company_blocks_admission_even_if_website_present():
    snap = ErowdPipeline().evaluate(
        {
            "signal_id": "ph-skip",
            "title": "Mystery Launch",
            "body": "A product on Product Hunt",
            "url": "https://www.producthunt.com/posts/mystery",
            "source": "product_hunt",
            "metadata": {
                "ofc_skip_company": True,
                "ofc_reason": "no_official_website",
                "canonical_website": "https://mystery.app",
            },
            "canonical_website": "https://mystery.app",
            "website_verified": True,
            "website_title": "Mystery",
            "industry": "Software",
        }
    )
    assert not snap.admission.allow_create_company
    assert RejectionReason.NO_OFFICIAL_WEBSITE in snap.admission.reasons


def test_devto_without_website_rejected():
    snap = ErowdPipeline().evaluate(
        {
            "signal_id": "d1",
            "title": "How I built an AI agent",
            "body": "tutorial",
            "url": "https://dev.to/user/post",
            "source": "devto",
        }
    )
    assert not snap.admission.allow_create_company


def test_never_fabricate_domain():
    discovered = OfficialWebsiteDiscoveryEngine().discover(
        {
            "source": "product_hunt",
            "title": "MysteryCo",
            "url": "https://www.producthunt.com/posts/mysteryco",
            "metadata": {},
        }
    )
    assert discovered.discovered is False
    assert discovered.domain is None


def test_identity_score_threshold():
    engine = ErowdIdentityConfidenceEngine()
    from entity_resolution.models.types import DomainValidation, EntityCandidate, OfficialWebsite

    score = engine.score(
        EntityCandidate(name="Screenpipe", normalized_key="screenpipe"),
        OfficialWebsite(discovered=True, website="https://screenpipe.com", domain="screenpipe.com", source="product_hunt_official_website", confidence=98),
        DomainValidation(verified=True, https=True, domain="screenpipe.com", title="Screenpipe"),
        payload={"source": "product_hunt", "industry": "Software"},
    )
    assert score.score >= 90
    assert score.passed


def test_attribution_stored():
    snap = ErowdPipeline().evaluate(_ph())
    assert snap.attribution.website
    assert snap.attribution.collector == "product_hunt"
    assert snap.attribution.confidence >= 70


def test_rebuild_metrics():
    pipe = ErowdPipeline()
    snaps = [
        pipe.evaluate(_ph(signal_id=f"a{i}", official_website=f"https://co{i}.com", metadata={"company_hints": [f"Co{i}"], "official_website": f"https://co{i}.com"}))
        for i in range(5)
    ] + [
        pipe.evaluate({"signal_id": f"n{i}", "title": "noise", "body": "x", "url": "https://reddit.com/r/x", "source": "reddit"})
        for i in range(5)
    ]
    report = ErowdRebuildEngine().build(snaps)
    assert report.total_signals == 10
    assert report.admitted >= 1
    assert report.false_positives == 0
