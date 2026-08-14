"""Website Discovery v2 — Identity Graph first; never guess domains."""

from __future__ import annotations

from typing import Any

from identity_graph.evidence.engine import EvidenceEngine
from identity_graph.models.types import IdentityEvidence
from entity_resolution.website_discovery.engine import OfficialWebsiteDiscoveryEngine
from intelligence.entity_resolution.platform_domains import is_platform_domain


class WebsiteDiscoveryV2Engine:
    """Priority: graph hint → official metadata → GitHub → LinkedIn → Crunchbase → OG/JSON-LD → never guess."""

    def __init__(self) -> None:
        self.evidence = EvidenceEngine()
        self.erowd_discovery = OfficialWebsiteDiscoveryEngine()

    def discover(
        self,
        payload: dict[str, Any],
        *,
        graph_domain: str | None = None,
        evidence_items: list[IdentityEvidence] | None = None,
    ) -> tuple[str | None, str | None, list[str]]:
        trail: list[str] = []

        # 1) Existing Identity Graph
        if graph_domain and not is_platform_domain(graph_domain):
            trail.append("priority:identity_graph")
            return f"https://{graph_domain}", graph_domain, trail

        items = evidence_items if evidence_items is not None else self.evidence.collect(payload)

        # 2–5) Provider evidence by confidence (official / github / linkedin / crunchbase already in providers)
        website_ev = self.evidence.best(items, "website")
        if website_ev:
            domain_ev = self.evidence.best(items, "official_domain")
            domain = domain_ev.value if domain_ev else website_ev.value.replace("https://", "").replace("http://", "").split("/")[0]
            domain = domain.lower().removeprefix("www.")
            if domain and not is_platform_domain(domain):
                trail.append(f"priority:provider:{website_ev.source}")
                trail.extend(website_ev.evidence)
                return website_ev.value, domain, trail

        # 6–9) Compose EROWD discovery (OG / JSON-LD / PH / GitHub HTML) — never invent
        discovered = self.erowd_discovery.discover(payload)
        if discovered.discovered and discovered.domain and not is_platform_domain(discovered.domain):
            trail.append(f"priority:erowd:{discovered.source}")
            trail.extend(discovered.evidence)
            return discovered.website, discovered.domain, trail

        trail.append("no_official_website_evidence")
        return None, None, trail
