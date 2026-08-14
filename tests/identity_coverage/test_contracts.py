"""ICE v1 contract tests."""

from identity_coverage import IdentityCoveragePipeline, SCORING_VERSION, ProviderAction
from identity_coverage.alias.engine import AliasResolutionEngine
from identity_coverage.collector_metrics.engine import CollectorPerformanceEngine
from identity_coverage.github.engine import GitHubIdentityResolver
from identity_coverage.product_hunt.engine import ProductHuntApiResolver
from identity_coverage.ranking.engine import EvidenceRankingEngine
from identity_coverage.models.types import CoverageEvidence


def test_version():
    assert SCORING_VERSION == "ice-v1"


def test_ph_without_token_no_fabricated_website():
    r = ProductHuntApiResolver(token="")
    ev = r.collect(
        {
            "source": "product_hunt",
            "url": "https://www.producthunt.com/products/caw",
            "metadata": {"ph_post_id": "1202953", "ph_maker": "Manuel"},
        }
    )
    assert not any(e.field == "website" for e in ev)
    assert any(e.field == "blocker" for e in ev)
    assert any(e.field == "maker" for e in ev)


def test_ph_api_with_mock_post():
    class Fake:
        def post(self, *a, **k):
            class R:
                status_code = 200

                def json(self):
                    return {
                        "data": {
                            "post": {
                                "id": "1",
                                "name": "Caw",
                                "tagline": "terminal",
                                "description": "mux",
                                "url": "https://www.producthunt.com/posts/caw",
                                "website": "https://caw.dev",
                                "makers": [{"name": "Manuel"}],
                            }
                        }
                    }

            return R()

    r = ProductHuntApiResolver(token="tok", client=Fake())  # type: ignore[arg-type]
    ev = r.collect({"source": "product_hunt", "metadata": {"ph_post_id": "1"}})
    assert any(e.field == "website" and "caw.dev" in e.value for e in ev)


def test_github_metadata_homepage():
    ev = GitHubIdentityResolver().collect(
        {
            "source": "github_trending",
            "url": "https://github.com/acme/kit",
            "title": "GitHub: acme/kit",
            "metadata": {"repo_homepage": "https://acme.dev"},
        }
    )
    assert any(e.field == "official_domain" and e.value == "acme.dev" for e in ev)


def test_alias_merge():
    a = AliasResolutionEngine().resolve(
        {"title": "ScreenPipe", "metadata": {"company_hints": ["screenpipe", "Screen Pipe"]}},
        domain="screenpipe.com",
    )
    assert a.primary_name
    assert a.official_domain == "screenpipe.com"
    assert a.confidence >= 70


def test_ranking():
    ranked = EvidenceRankingEngine().rank(
        [
            CoverageEvidence(field="website", value="https://a.com", confidence=80, source="x", priority=20),
            CoverageEvidence(field="website", value="https://b.com", confidence=95, source="y", priority=10, verification=True),
        ]
    )
    assert ranked["website"].value == "https://b.com"
    assert ranked["website"].verified


def test_collector_recommendations():
    kpis = CollectorPerformanceEngine().score(
        [
            {"collector": "reddit", "candidate": True},
            {"collector": "github_trending", "candidate": True, "admitted": True, "website": "https://x.com", "confidence": 90},
            {"collector": "github_trending", "candidate": True, "admitted": True, "website": "https://y.com", "confidence": 88},
        ]
    )
    by = {k.collector: k for k in kpis}
    assert by["reddit"].recommendation == ProviderAction.DISABLE
    assert by["github_trending"].recommendation in {ProviderAction.KEEP, ProviderAction.LIMIT}


def test_pipeline_hn_no_website_invention():
    snap = IdentityCoveragePipeline().evaluate(
        {"signal_id": "1", "source": "hacker_news", "title": "Show HN", "url": "https://news.ycombinator.com/1"}
    )
    assert snap.website is None
    assert snap.admitted_hint is False
