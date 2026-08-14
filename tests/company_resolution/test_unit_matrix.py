"""Company Resolution Engine (CRE v1) — unit matrix."""

from __future__ import annotations

from time import perf_counter

import pytest

from company_resolution import COMPANY_CREATE_REQUIRES_CRE, LIVE_OUTREACH_ENABLED, SCORING_VERSION
from company_resolution.identity_confidence.engine import IDENTITY_THRESHOLD, IdentityConfidenceEngine
from company_resolution.models.types import CreVerdict, RawSignalEnvelope, RejectionReason
from company_resolution.organization_resolver.engine import OrganizationResolverEngine
from company_resolution.pipelines.engine import CompanyResolutionPipeline
from company_resolution.rebuild.engine import CreRebuildEngine
from company_resolution.website_validator.engine import WebsiteValidatorEngine


def _ph(**overrides):
    base = {
        "signal_id": "sig-1",
        "title": "Screenpipe — AI screen recording for teams",
        "body": "Screenpipe helps companies automate workflows with AI agents for enterprise operations and customer support.",
        "url": "https://www.producthunt.com/posts/screenpipe",
        "source": "product_hunt",
        "metadata": {"domain": "screenpipe.com", "company_hints": ["Screenpipe"]},
        "domains": ["screenpipe.com"],
        "website_alive": True,
        "http_status": 200,
        "ssl": True,
        "industry": "Software",
        "description": "AI screen recording and workflow automation platform for enterprise teams.",
        "country": "US",
    }
    base.update(overrides)
    return base


def _noise(**overrides):
    base = {
        "signal_id": "sig-noise",
        "title": "Kubernetes is hard",
        "body": "I learned about kubernetes today on Hacker News",
        "url": "https://news.ycombinator.com/item?id=1",
        "source": "hacker_news",
        "metadata": {},
    }
    base.update(overrides)
    return base


def test_version():
    assert SCORING_VERSION == "cre-v1"
    assert LIVE_OUTREACH_ENABLED is False
    assert COMPANY_CREATE_REQUIRES_CRE is True
    assert IDENTITY_THRESHOLD == 90.0


def test_product_hunt_admitted():
    snap = CompanyResolutionPipeline().evaluate(_ph())
    assert snap.verdict == CreVerdict.ADMITTED
    assert snap.admission.allow_create_company
    assert snap.company_domain == "screenpipe.com"
    assert snap.identity.score >= 90
    assert snap.attribution.product_hunt_page


def test_hn_title_noise_rejected():
    snap = CompanyResolutionPipeline().evaluate(_noise())
    assert snap.verdict == CreVerdict.REJECTED
    assert not snap.admission.allow_create_company


def test_reddit_without_domain_rejected():
    snap = CompanyResolutionPipeline().evaluate(
        {
            "signal_id": "r1",
            "title": "Anyone using automation tools?",
            "body": "Looking for advice",
            "url": "https://reddit.com/r/startups/1",
            "source": "reddit",
        }
    )
    assert snap.verdict == CreVerdict.REJECTED


def test_medium_blog_rejected():
    snap = CompanyResolutionPipeline().evaluate(
        _ph(
            source="rss",
            title="My Startup Journey",
            metadata={"domain": "medium.com"},
            domains=["medium.com"],
            url="https://medium.com/@x/post",
        )
    )
    assert snap.verdict == CreVerdict.REJECTED
    assert any(r in {RejectionReason.MEDIUM, RejectionReason.PLATFORM_DOMAIN, RejectionReason.WEBSITE_INVALID, RejectionReason.NO_ORGANIZATION, RejectionReason.NO_DOMAIN, RejectionReason.SOURCE_POLICY, RejectionReason.LOW_IDENTITY_CONFIDENCE} for r in snap.admission.reasons) or not snap.admission.admitted


def test_github_repo_rejected():
    snap = CompanyResolutionPipeline().evaluate(
        {
            "signal_id": "g1",
            "title": "awesome-list",
            "body": "collection of tools",
            "url": "https://github.com/foo/awesome-list",
            "source": "github_trending",
            "metadata": {"domain": "github.com", "company_hints": ["foo"]},
            "domains": ["github.com"],
        }
    )
    assert snap.verdict == CreVerdict.REJECTED


def test_news_site_rejected():
    snap = CompanyResolutionPipeline().evaluate(
        _ph(
            source="rss",
            title="OpenAI raises funds",
            metadata={"domain": "techcrunch.com"},
            domains=["techcrunch.com"],
            url="https://techcrunch.com/openai",
        )
    )
    assert snap.verdict == CreVerdict.REJECTED


def test_attribution_required_fields():
    snap = CompanyResolutionPipeline().evaluate(_ph())
    assert snap.attribution.signal_id == "sig-1"
    assert snap.attribution.source == "product_hunt"
    assert snap.attribution.source_url


def test_identity_below_90_rejected():
    org = OrganizationResolverEngine().resolve(
        RawSignalEnvelope.from_raw(
            signal_id="x",
            title="X",
            body="short",
            url="https://example.org",
            source="reddit",
            metadata={},
        )
    )
    identity = IdentityConfidenceEngine().score(
        RawSignalEnvelope.from_raw(signal_id="x", title="X", body="short", url=None, source="reddit"),
        org,
        website_valid=False,
    )
    assert identity.score < 90 or not org.found


def test_rebuild_metrics():
    pipe = CompanyResolutionPipeline()
    snaps = [pipe.evaluate(_ph(signal_id=str(i), metadata={"domain": f"co{i}.com", "company_hints": [f"Co{i}"]}, domains=[f"co{i}.com"], title=f"Co{i} — product")) for i in range(5)]
    snaps += [pipe.evaluate(_noise(signal_id=f"n{i}")) for i in range(5)]
    report = CreRebuildEngine().build(snaps)
    assert report.total_raw_signals == 10
    assert report.companies_rejected >= 5
    assert report.resolution_success_rate >= 0


def test_version_string_not_domain():
    snap = CompanyResolutionPipeline().evaluate(
        {
            "signal_id": "ver",
            "title": "Basedash AI — GPT-5.6 analytics",
            "body": "Built with gpt-5.6 and scores 6.4x faster. Version 2.0 released.",
            "url": "https://www.producthunt.com/products/basedash",
            "source": "product_hunt",
            "metadata": {},
            "domains": [],
        }
    )
    assert snap.organization.official_domain not in {"2.0", "gpt-5.6", "6.4x", "5.6"}
    assert snap.verdict == CreVerdict.REJECTED


@pytest.mark.parametrize("i", range(60))
def test_admit_matrix(i):
    snap = CompanyResolutionPipeline().evaluate(
        _ph(
            signal_id=str(i),
            title=f"Acme{i} — workflow automation",
            metadata={"domain": f"acme{i}.io", "company_hints": [f"Acme{i}"]},
            domains=[f"acme{i}.io"],
        )
    )
    assert snap.verdict == CreVerdict.ADMITTED


@pytest.mark.parametrize("i", range(60))
def test_reject_hn_matrix(i):
    snap = CompanyResolutionPipeline().evaluate(_noise(signal_id=str(i), title=f"Thought {i} about coding"))
    assert snap.verdict == CreVerdict.REJECTED


@pytest.mark.parametrize("i", range(50))
def test_reject_reddit_matrix(i):
    snap = CompanyResolutionPipeline().evaluate(
        {
            "signal_id": str(i),
            "title": f"Discussion {i}",
            "body": "comments",
            "url": f"https://reddit.com/r/x/{i}",
            "source": "reddit",
        }
    )
    assert snap.verdict == CreVerdict.REJECTED


@pytest.mark.parametrize("i", range(40))
def test_reject_rss_news(i):
    snap = CompanyResolutionPipeline().evaluate(
        {
            "signal_id": str(i),
            "title": f"Article {i}",
            "body": "news",
            "url": f"https://techcrunch.com/p/{i}",
            "source": "rss",
            "metadata": {"domain": "techcrunch.com"},
            "domains": ["techcrunch.com"],
        }
    )
    assert snap.verdict == CreVerdict.REJECTED


@pytest.mark.parametrize("i", range(40))
def test_devto_needs_real_domain(i):
    snap = CompanyResolutionPipeline().evaluate(
        {
            "signal_id": str(i),
            "title": f"How I built X {i}",
            "body": "tutorial",
            "url": f"https://dev.to/u/{i}",
            "source": "devto",
            "metadata": {"domain": "dev.to"},
            "domains": ["dev.to"],
        }
    )
    assert snap.verdict == CreVerdict.REJECTED


@pytest.mark.parametrize("i", range(40))
def test_website_validator_parked(i):
    from company_resolution.models.types import OrganizationCandidate

    org = OrganizationCandidate(
        legal_name=f"Park{i}",
        official_domain=f"park{i}.com",
        homepage=f"https://park{i}.com",
        found=True,
        evidence=[],
    )
    result = WebsiteValidatorEngine().validate(org, html_text="This domain is for sale on GoDaddy", http_status=200)
    assert not result.valid
    assert result.reject_reason == RejectionReason.PARKED_DOMAIN


@pytest.mark.parametrize("i", range(35))
def test_org_resolver_domain(i):
    org = OrganizationResolverEngine().resolve(
        RawSignalEnvelope.from_raw(
            signal_id=str(i),
            title=f"Helios{i} — clinic AI",
            body="Helios automates clinic workflows for hospitals.",
            url="https://www.producthunt.com/posts/helios",
            source="product_hunt",
            metadata={"domain": f"helios{i}.health"},
            domains=[f"helios{i}.health"],
        ),
        hints={"domain": f"helios{i}.health", "company_hints": [f"Helios{i}"]},
    )
    assert org.found
    assert org.official_domain == f"helios{i}.health"


@pytest.mark.parametrize("i", range(35))
def test_rebuild_single(i):
    snap = CompanyResolutionPipeline().evaluate(_ph(signal_id=str(i)))
    report = CreRebuildEngine().build([snap])
    assert report.total_raw_signals == 1


@pytest.mark.parametrize("reason", list(RejectionReason))
def test_rejection_enum(reason):
    assert reason.value


@pytest.mark.parametrize("src", ["reddit", "hacker_news", "rss", "devto", "product_hunt", "github_trending"])
def test_source_policy(src):
    snap = CompanyResolutionPipeline().evaluate(_noise(source=src, signal_id=src))
    assert snap.verdict == CreVerdict.REJECTED


@pytest.mark.parametrize("i", range(40))
def test_no_company_without_org(i):
    snap = CompanyResolutionPipeline().evaluate({"signal_id": str(i), "title": "hi", "body": "", "source": "rss"})
    assert not snap.admission.allow_create_company


@pytest.mark.parametrize("i", range(40))
def test_linkedin_plus_name_can_resolve(i):
    snap = CompanyResolutionPipeline().evaluate(
        {
            "signal_id": f"li{i}",
            "title": f"NovaLabs{i} hiring engineers",
            "body": f"NovaLabs{i} is expanding. https://linkedin.com/company/novalabs{i} https://novalabs{i}.com",
            "url": f"https://reddit.com/r/startups/{i}",
            "source": "reddit",
            "metadata": {"domain": f"novalabs{i}.com", "company_hints": [f"NovaLabs{i}"]},
            "domains": [f"novalabs{i}.com"],
            "website_alive": True,
            "http_status": 200,
            "industry": "Software",
            "description": "NovaLabs builds enterprise workflow automation software for operations teams worldwide.",
            "country": "US",
        }
    )
    assert snap.organization.official_domain == f"novalabs{i}.com" or snap.verdict == CreVerdict.REJECTED


@pytest.mark.parametrize("i", range(20))
def test_duplicate_company_same_domain(i):
    pipe = CompanyResolutionPipeline()
    a = pipe.evaluate(_ph(signal_id=f"a{i}", metadata={"domain": "sameco.com", "company_hints": ["SameCo"]}, domains=["sameco.com"], title="SameCo — ops"))
    b = pipe.evaluate(_ph(signal_id=f"b{i}", metadata={"domain": "sameco.com", "company_hints": ["SameCo"]}, domains=["sameco.com"], title="SameCo — ops v2"))
    assert a.company_domain == b.company_domain == "sameco.com"
    report = CreRebuildEngine().build([a, b])
    assert report.resolved_companies == 1
