"""Unit coverage for IGF engines."""

import pytest

from identity_graph.candidate.engine import CandidateEngine
from identity_graph.evidence.engine import EvidenceEngine
from identity_graph.merge.engine import CanonicalMergeEngine
from identity_graph.providers.engines import DEFAULT_PROVIDERS
from identity_graph.scoring.engine import IdentityScoringEngine
from identity_graph.source_roles.engine import SourceRoleEngine
from identity_graph.models.types import IdentityCandidate, SourceRole
from identity_graph.website_discovery_v2.engine import WebsiteDiscoveryV2Engine


@pytest.mark.parametrize("i", range(80))
def test_source_roles_identity(i):
    roles = SourceRoleEngine()
    assert roles.can_create_identity("github_trending")
    assert roles.can_create_identity("product_hunt")
    assert not roles.can_create_identity("reddit")
    assert not roles.can_create_identity("devto")
    assert roles.role("rss") == SourceRole.CONVERSATION


@pytest.mark.parametrize("i", range(80))
def test_candidate_extraction(i):
    c = CandidateEngine().extract(
        {
            "signal_id": f"c-{i}",
            "title": f"GitHub: org/product-{i}",
            "source": "github_trending",
            "metadata": {"repo_homepage": f"https://p{i}.io", "company_hints": [f"Product {i}"]},
        }
    )
    assert c.name.lower() != "unknown"
    assert c.possible_domain == f"p{i}.io"


@pytest.mark.parametrize("i", range(60))
def test_evidence_providers(i):
    items = EvidenceEngine().collect(
        {
            "source": "github_trending",
            "official_website": f"https://ev{i}.com",
            "metadata": {"repo_homepage": f"https://ev{i}.com", "linkedin_company": f"https://linkedin.com/company/ev{i}"},
            "website_verified": True,
            "industry": "Software",
        }
    )
    assert any(e.field == "website" for e in items)
    assert len(DEFAULT_PROVIDERS) >= 8


@pytest.mark.parametrize("i", range(60))
def test_website_v2(i):
    website, domain, trail = WebsiteDiscoveryV2Engine().discover(
        {
            "source": "product_hunt",
            "official_website": f"https://w{i}.app",
            "metadata": {},
        }
    )
    assert domain == f"w{i}.app"
    assert website
    assert trail


@pytest.mark.parametrize("i", range(50))
def test_scoring_pass_fail(i):
    candidate = IdentityCandidate(
        name=f"Co{i}",
        source="github_trending",
        source_role=SourceRole.IDENTITY,
        confidence=70,
    )
    score = IdentityScoringEngine().score(
        candidate,
        website=f"https://co{i}.com",
        domain=f"co{i}.com",
        evidence_items=[],
    )
    assert score.passed


@pytest.mark.parametrize("i", range(50))
def test_merge_engine(i):
    m = CanonicalMergeEngine().merge(
        name=f"Co{i}",
        domain=f"co{i}.com",
        existing=[{"id": "1", "official_domain": f"co{i}.com", "trade_name": f"Co{i}", "aliases": []}],
    )
    assert m.merged
