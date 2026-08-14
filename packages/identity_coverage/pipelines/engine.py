"""ICE coverage pipeline — compose providers → rank → recovery hints → IGF payload enrichment."""

from __future__ import annotations

from typing import Any

from identity_coverage.alias.engine import AliasResolutionEngine
from identity_coverage.domain_intel.engine import DomainIntelligenceEngine
from identity_coverage.github.engine import GitHubIdentityResolver
from identity_coverage.models.types import IceSnapshot, RecoveryReason
from identity_coverage.product_hunt.engine import ProductHuntApiResolver
from identity_coverage.ranking.engine import EvidenceRankingEngine
from identity_coverage.recovery.engine import RecoveryQueueEngine
from identity_coverage.website_intel.engine import WebsiteIntelligenceEngine


class IdentityCoveragePipeline:
    def __init__(self) -> None:
        self.ph = ProductHuntApiResolver()
        self.gh = GitHubIdentityResolver()
        self.website = WebsiteIntelligenceEngine()
        self.domain = DomainIntelligenceEngine()
        self.alias = AliasResolutionEngine()
        self.ranker = EvidenceRankingEngine()
        self.recovery = RecoveryQueueEngine()

    def evaluate(
        self,
        payload: dict[str, Any],
        *,
        fetch_github: bool = False,
        crawl_website: bool = False,
        probe_dns: bool = False,
    ) -> IceSnapshot:
        signal_id = str(payload.get("signal_id") or payload.get("id") or "unknown")
        source = str(payload.get("source") or "unknown").lower()
        evidence = []
        evidence.extend(self.ph.collect(payload))
        evidence.extend(self.gh.collect(payload, fetch_live=fetch_github))

        ranked_pre = self.ranker.rank(evidence)
        website = ranked_pre.get("website").value if ranked_pre.get("website") else None
        domain = ranked_pre.get("official_domain").value if ranked_pre.get("official_domain") else None
        if not website:
            website = payload.get("official_website") or (payload.get("metadata") or {}).get("official_website")
        if not domain and website:
            domain = str(website).replace("https://", "").replace("http://", "").split("/")[0].removeprefix("www.")

        enrich_payload = {
            **payload,
            "official_website": website,
            "website": website,
            "official_domain": domain,
            "domain": domain,
        }
        if crawl_website and website:
            evidence.extend(self.website.collect(enrich_payload))
        if domain:
            evidence.extend(self.domain.collect(enrich_payload, probe=probe_dns))

        ranked = self.ranker.rank(evidence)
        website = ranked.get("website").value if ranked.get("website") else website
        domain = ranked.get("official_domain").value if ranked.get("official_domain") else domain
        alias = self.alias.resolve(enrich_payload, domain=domain)
        recovery_items = self.recovery.enqueue_from_payload(enrich_payload, ranked=ranked)
        recovery_reasons = [i.reason for i in recovery_items]

        admitted_hint = bool(website and domain and alias.primary_name.lower() != "unknown")
        return IceSnapshot(
            signal_id=signal_id,
            source=source,
            evidence=evidence,
            ranked=ranked,
            alias=alias,
            website=website if website and website != "unknown" else None,
            domain=domain if domain and domain != "unknown" else None,
            recovery=recovery_reasons,
            admitted_hint=admitted_hint,
            payload={
                "igf_enrichment": {
                    "official_website": website,
                    "homepage": website,
                    "official_domain": domain,
                    "domain": domain,
                    "company_hints": [alias.primary_name, *alias.aliases] if alias else [],
                    "business_email": ranked.get("business_email").value if ranked.get("business_email") else None,
                    "decision_maker": ranked.get("decision_maker").value if ranked.get("decision_maker") else None,
                    "linkedin_company": ranked.get("linkedin_company").value if ranked.get("linkedin_company") else None,
                    "ice_evidence_count": len(evidence),
                },
                "recovery": [r.value for r in recovery_reasons],
            },
        )

    def evaluate_many(self, payloads: list[dict[str, Any]], **kwargs: Any) -> list[IceSnapshot]:
        return [self.evaluate(p, **kwargs) for p in payloads]

    def to_igf_payload(self, payload: dict[str, Any], snap: IceSnapshot) -> dict[str, Any]:
        out = dict(payload)
        enrich = snap.payload.get("igf_enrichment") or {}
        meta = dict(out.get("metadata") or {})
        for k, v in enrich.items():
            if v:
                meta[k] = v
                out[k] = v
        out["metadata"] = meta
        out["website_verified"] = bool(snap.domain)
        return out
