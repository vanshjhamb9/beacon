"""EROWD pipeline — Signal → Entity → Official Website → Verify → Company."""

from __future__ import annotations

from typing import Any

from entity_resolution.canonical_identity.engine import CanonicalIdentityEngine
from entity_resolution.domain_validator.engine import OfficialDomainValidator
from entity_resolution.entity_resolver.engine import EntityResolverEngine
from entity_resolution.evidence_graph.engine import EvidenceGraphEngine
from entity_resolution.identity_confidence.engine import ErowdIdentityConfidenceEngine
from entity_resolution.models.types import (
    ErowdAdmission,
    ErowdSnapshot,
    ErowdVerdict,
    RejectionReason,
)
from entity_resolution.website_attribution.engine import WebsiteAttributionEngine
from entity_resolution.website_discovery.engine import OfficialWebsiteDiscoveryEngine

# OFC: weak entity-resolution sources stay signal-only until ER is reliable
SIGNAL_ONLY_SOURCES = frozenset(
    {
        "reddit",
        "hacker_news",
        "hn",
        "rss",
        "indie_hackers",
        "sec_edgar",
        "sec",
    }
)


class ErowdPipeline:
    def __init__(self) -> None:
        self.discovery = OfficialWebsiteDiscoveryEngine()
        self.entities = EntityResolverEngine()
        self.validator = OfficialDomainValidator()
        self.attribution = WebsiteAttributionEngine()
        self.confidence = ErowdIdentityConfidenceEngine()
        self.canonical = CanonicalIdentityEngine()
        self.graph = EvidenceGraphEngine()

    def evaluate(self, payload: dict[str, Any]) -> ErowdSnapshot:
        signal_id = str(payload.get("signal_id") or payload.get("id") or payload.get("raw_event_id") or "unknown")
        source = str(payload.get("source") or "unknown").lower()
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}

        website = self.discovery.discover(payload)
        entity = self.entities.resolve(payload, website=website if website.discovered else None)
        validation = self.validator.validate(website, payload=payload)
        attribution = self.attribution.attribute(website, collector=source, payload=payload)
        score = self.confidence.score(entity, website, validation, payload=payload)
        identity = self.canonical.build(entity, website, validation, score, payload=payload)
        edges = self.graph.build(signal_id=signal_id, source=source, website=website, entity=entity, payload=payload)

        reasons: list[RejectionReason] = []
        # Collector explicit skip (e.g. Product Hunt with no official site) — never create company
        if meta.get("ofc_skip_company") is True:
            reasons.append(RejectionReason.NO_OFFICIAL_WEBSITE)
        if source in SIGNAL_ONLY_SOURCES and not (website.discovered and validation.verified and score.passed):
            reasons.append(RejectionReason.SOURCE_SIGNAL_ONLY)
        if not website.discovered:
            reasons.append(RejectionReason.NO_OFFICIAL_WEBSITE)
        if entity.name == "unknown" or not entity.name:
            reasons.append(RejectionReason.NO_ENTITY_NAME)
        if website.discovered and not validation.verified:
            reasons.append(RejectionReason.WEBSITE_UNVERIFIED)
        if not score.passed:
            reasons.append(RejectionReason.LOW_IDENTITY_CONFIDENCE)
        if source in {"rss", "devto"} and not website.discovered:
            reasons.append(RejectionReason.ARTICLE_ONLY)

        # Deduplicate
        seen: set[RejectionReason] = set()
        unique: list[RejectionReason] = []
        for r in reasons:
            if r in seen:
                continue
            seen.add(r)
            unique.append(r)

        admitted = (
            website.discovered
            and validation.verified
            and score.passed
            and entity.name not in {"", "unknown"}
            and source not in SIGNAL_ONLY_SOURCES
            and meta.get("ofc_skip_company") is not True
        )
        # Weak sources never create companies (OFC Priority 4)
        if source in SIGNAL_ONLY_SOURCES:
            admitted = False
            if RejectionReason.SOURCE_SIGNAL_ONLY not in unique:
                unique.insert(0, RejectionReason.SOURCE_SIGNAL_ONLY)

        if meta.get("ofc_skip_company") is True:
            admitted = False

        # Dev.to only if official website exists (already covered by website.discovered)
        if source == "devto" and not website.discovered:
            admitted = False

        if admitted:
            unique = []
            verdict = ErowdVerdict.ADMITTED
        elif source in SIGNAL_ONLY_SOURCES:
            verdict = ErowdVerdict.SIGNAL_ONLY
        else:
            verdict = ErowdVerdict.REJECTED

        explanation = " → ".join(r.value for r in unique) if unique else "Admitted — official website verified"
        admission = ErowdAdmission(
            admitted=admitted,
            verdict=verdict,
            reasons=unique,
            explanation=explanation,
            allow_create_company=admitted,
            evidence=[f"admitted:{admitted}", explanation],
        )

        return ErowdSnapshot(
            signal_id=signal_id,
            source=source,
            verdict=verdict,
            entity=entity,
            website=website,
            attribution=attribution,
            validation=validation,
            identity=identity,
            score=score,
            admission=admission,
            evidence_edges=edges,
            evidence=[
                f"verdict:{verdict.value}",
                f"website:{website.domain}",
                f"score:{score.score}",
                f"verified:{validation.verified}",
            ],
        )

    def evaluate_many(self, payloads: list[dict[str, Any]]) -> list[ErowdSnapshot]:
        return [self.evaluate(p) for p in payloads]
