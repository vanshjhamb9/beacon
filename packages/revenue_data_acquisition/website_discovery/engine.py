"""Official website discovery — compose ICE/PH/GitHub; never guess."""

from __future__ import annotations

from typing import Any

from identity_coverage.github.engine import GitHubIdentityResolver
from identity_coverage.product_hunt.engine import ProductHuntApiResolver
from identity_coverage.ranking.engine import EvidenceRankingEngine
from identity_graph.website_discovery_v2.engine import WebsiteDiscoveryV2Engine


class OfficialWebsiteDiscoveryPipeline:
    def __init__(self) -> None:
        self.ph = ProductHuntApiResolver()
        self.gh = GitHubIdentityResolver()
        self.ranker = EvidenceRankingEngine()
        self.igf_v2 = WebsiteDiscoveryV2Engine()

    def discover(self, payload: dict[str, Any], *, fetch_github: bool = False) -> tuple[str | None, str | None, list[str]]:
        evidence = []
        evidence.extend(self.ph.collect(payload))
        evidence.extend(self.gh.collect(payload, fetch_live=fetch_github))
        ranked = self.ranker.rank(evidence)
        if ranked.get("website") and ranked.get("official_domain"):
            return ranked["website"].value, ranked["official_domain"].value, ["rdap:ice_providers"]
        # Graph / metadata / OG via IGF v2 (composes EROWD)
        website, domain, trail = self.igf_v2.discover(payload)
        return website, domain, ["rdap:website_discovery_v2", *trail]
