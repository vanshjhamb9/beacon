"""IGF v1 contract tests."""

from identity_graph import IdentityResolutionPipeline, SourceRole, SCORING_VERSION
from identity_graph.models.types import IgfVerdict, RejectionReason


def test_scoring_version():
    assert SCORING_VERSION == "igf-v1"


def test_conversation_source_never_creates_company():
    snap = IdentityResolutionPipeline().evaluate(
        {
            "signal_id": "hn1",
            "title": "Show HN: Cool",
            "source": "hacker_news",
            "url": "https://news.ycombinator.com/item?id=1",
            "official_website": "https://cool.dev",
            "homepage": "https://cool.dev",
            "website_verified": True,
        }
    )
    assert snap.source_role == SourceRole.CONVERSATION
    assert not snap.admission.allow_create_company
    assert snap.admission.verdict == IgfVerdict.SIGNAL_ONLY
    assert RejectionReason.CONVERSATION_SOURCE in snap.admission.reasons


def test_github_with_homepage_admitted():
    snap = IdentityResolutionPipeline().evaluate(
        {
            "signal_id": "g1",
            "title": "GitHub: acme/agent-kit",
            "source": "github_trending",
            "url": "https://github.com/acme/agent-kit",
            "metadata": {
                "company_hints": ["Acme"],
                "repo_homepage": "https://acme.dev",
                "owner": "acme",
                "owner_type": "Organization",
            },
            "github_homepage": "https://acme.dev",
            "website_verified": True,
            "industry": "Software",
        }
    )
    assert snap.admission.admitted
    assert snap.admission.allow_create_company
    assert snap.domain == "acme.dev"
    assert snap.canonical is not None


def test_no_website_rejected():
    snap = IdentityResolutionPipeline().evaluate(
        {
            "signal_id": "g2",
            "title": "GitHub: foo/bar",
            "source": "github_trending",
            "url": "https://github.com/foo/bar",
            "metadata": {"company_hints": ["foo"], "domain": "github.com"},
        }
    )
    assert not snap.admission.admitted
    assert RejectionReason.NO_OFFICIAL_WEBSITE in snap.admission.reasons


def test_merge_same_domain():
    pipe = IdentityResolutionPipeline()
    first = pipe.evaluate(
        {
            "signal_id": "a",
            "title": "Screenpipe",
            "source": "product_hunt",
            "official_website": "https://screenpipe.com",
            "metadata": {"company_hints": ["Screenpipe"]},
            "website_verified": True,
        }
    )
    second = pipe.evaluate(
        {
            "signal_id": "b",
            "title": "ScreenPipe AI",
            "source": "github_trending",
            "official_website": "https://screenpipe.com",
            "metadata": {"company_hints": ["ScreenPipe"], "repo_homepage": "https://screenpipe.com"},
            "website_verified": True,
        },
        existing=[
            {
                "id": "canon-1",
                "official_domain": "screenpipe.com",
                "trade_name": "Screenpipe",
                "legal_name": "Screenpipe",
                "aliases": [],
            }
        ],
    )
    assert first.admission.admitted
    assert second.admission.admitted
    assert second.merge.merged
    assert not second.admission.allow_create_company


def test_ofc_skip_blocks():
    snap = IdentityResolutionPipeline().evaluate(
        {
            "signal_id": "ph1",
            "title": "Mystery",
            "source": "product_hunt",
            "official_website": "https://mystery.app",
            "metadata": {"ofc_skip_company": True, "company_hints": ["Mystery"]},
            "website_verified": True,
        }
    )
    assert not snap.admission.admitted
