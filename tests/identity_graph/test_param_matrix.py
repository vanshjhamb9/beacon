"""Deterministic IGF param matrix — 500+ cases."""

from __future__ import annotations

import pytest

from identity_graph import IdentityResolutionPipeline, SourceRole
from identity_graph.models.types import IgfVerdict

INDUSTRIES = ["Software", "AI", "SaaS", "Fintech", "DevTools", "Healthcare", "Commerce", "Security"]
NAMES = [f"Acme{i}" for i in range(40)] + [f"Nova{i}" for i in range(40)] + [f"Pulse{i}" for i in range(40)]

CASES: list[tuple] = []
idx = 0
for industry in INDUSTRIES:
    for i, name in enumerate(NAMES):
        source = ("github_trending", "product_hunt", "hacker_news", "reddit", "devto", "rss")[i % 6]
        with_site = i % 3 != 0 or source in {"github_trending", "product_hunt"}
        domain = f"{name.lower()}.dev" if with_site and source in {"github_trending", "product_hunt"} else None
        CASES.append((idx, name, industry, source, domain))
        idx += 1
        if len(CASES) >= 520:
            break
    if len(CASES) >= 520:
        break

assert len(CASES) >= 500


@pytest.mark.parametrize("i,name,industry,source,domain", CASES)
def test_param_pipeline(i, name, industry, source, domain):
    payload = {
        "signal_id": f"igf-{i}",
        "title": name if source != "github_trending" else f"GitHub: org/{name.lower()}",
        "source": source,
        "url": f"https://example.com/{i}",
        "metadata": {"company_hints": [name], "industry": industry},
        "industry": industry,
        "website_verified": bool(domain),
    }
    if domain:
        payload["official_website"] = f"https://{domain}"
        payload["homepage"] = f"https://{domain}"
        payload["metadata"]["repo_homepage"] = f"https://{domain}"
        payload["metadata"]["official_domain"] = domain

    snap = IdentityResolutionPipeline().evaluate(payload)
    assert snap.signal_id == f"igf-{i}"
    assert snap.source_role in {SourceRole.IDENTITY, SourceRole.INTENT, SourceRole.CONVERSATION}

    if source in {"hacker_news", "reddit", "devto", "rss"}:
        assert not snap.admission.allow_create_company
        assert snap.admission.verdict in {IgfVerdict.SIGNAL_ONLY, IgfVerdict.REJECTED}
    elif domain and source in {"github_trending", "product_hunt"}:
        assert snap.admission.admitted
        assert snap.domain == domain
    elif not domain:
        assert not snap.admission.admitted
