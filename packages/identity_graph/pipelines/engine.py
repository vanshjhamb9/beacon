"""Identity Resolution Pipeline — Signal → Candidate → Evidence → Website → Score → Admit."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from identity_graph.candidate.engine import CandidateEngine
from identity_graph.evidence.engine import EvidenceEngine
from identity_graph.merge.engine import CanonicalMergeEngine
from identity_graph.models.types import (
    CanonicalCompany,
    CanonicalStatus,
    IgfAdmission,
    IgfSnapshot,
    IgfVerdict,
    RejectionReason,
    SourceRole,
)
from identity_graph.scoring.engine import IdentityScoringEngine
from identity_graph.source_roles.engine import SourceRoleEngine
from identity_graph.website_discovery_v2.engine import WebsiteDiscoveryV2Engine


class IdentityResolutionPipeline:
    def __init__(self) -> None:
        self.roles = SourceRoleEngine()
        self.candidates = CandidateEngine()
        self.evidence = EvidenceEngine()
        self.websites = WebsiteDiscoveryV2Engine()
        self.scoring = IdentityScoringEngine()
        self.merge = CanonicalMergeEngine()

    def evaluate(
        self,
        payload: dict[str, Any],
        *,
        existing: list[dict[str, Any]] | list[CanonicalCompany] | None = None,
        graph_domain: str | None = None,
    ) -> IgfSnapshot:
        signal_id = str(payload.get("signal_id") or payload.get("id") or payload.get("raw_event_id") or "unknown")
        source = str(payload.get("source") or "unknown").lower()
        role = self.roles.role(source)

        candidate = self.candidates.extract(payload)
        evidence_items = self.evidence.collect(payload)
        website, domain, trail = self.websites.discover(
            payload, graph_domain=graph_domain, evidence_items=evidence_items
        )
        score = self.scoring.score(candidate, website=website, domain=domain, evidence_items=evidence_items)
        merge = self.merge.merge(name=candidate.name, domain=domain, existing=existing)

        reasons: list[RejectionReason] = []
        if role == SourceRole.CONVERSATION:
            reasons.append(RejectionReason.CONVERSATION_SOURCE)
        if role == SourceRole.INTENT:
            reasons.append(RejectionReason.INTENT_SOURCE_ONLY)
        if not website or not domain:
            reasons.append(RejectionReason.NO_OFFICIAL_WEBSITE)
        if not candidate.name or candidate.name.lower() == "unknown":
            reasons.append(RejectionReason.NO_CANDIDATE_NAME)
        if not score.passed and RejectionReason.NO_OFFICIAL_WEBSITE not in reasons:
            reasons.append(RejectionReason.LOW_IDENTITY_CONFIDENCE)
        if payload.get("metadata", {}).get("ofc_skip_company") is True:
            reasons.append(RejectionReason.NO_OFFICIAL_WEBSITE)

        # Deduplicate reasons
        seen: set[RejectionReason] = set()
        unique: list[RejectionReason] = []
        for r in reasons:
            if r in seen:
                continue
            seen.add(r)
            unique.append(r)

        admitted = (
            role == SourceRole.IDENTITY
            and bool(website and domain)
            and bool(candidate.name and candidate.name.lower() != "unknown")
            and score.passed
            and payload.get("metadata", {}).get("ofc_skip_company") is not True
        )

        if admitted:
            unique = []
            verdict = IgfVerdict.MERGED if merge.merged else IgfVerdict.ADMITTED
        elif role == SourceRole.CONVERSATION:
            verdict = IgfVerdict.SIGNAL_ONLY
        elif role == SourceRole.INTENT:
            verdict = IgfVerdict.SIGNAL_ONLY
        else:
            verdict = IgfVerdict.REJECTED

        explanation = " → ".join(r.value for r in unique) if unique else (
            "Merged into existing canonical company" if merge.merged else "Admitted — official website verified"
        )

        canonical = None
        if admitted:
            canonical = CanonicalCompany(
                id=merge.canonical_id,
                legal_name=candidate.name,
                trade_name=candidate.name,
                aliases=list(candidate.aliases),
                official_domain=domain,
                website=website,
                linkedin_company_url=next(
                    (e.value for e in evidence_items if e.field == "linkedin_company_url"), None
                ),
                github_organization=next(
                    (e.value for e in evidence_items if e.field == "github_organization"), None
                ),
                crunchbase=next((e.value for e in evidence_items if e.field == "crunchbase"), None),
                industry=next((e.value for e in evidence_items if e.field == "industry"), None),
                country=next((e.value for e in evidence_items if e.field == "country"), None),
                description=next((e.value for e in evidence_items if e.field == "description"), None),
                evidence=evidence_items,
                confidence=score.score,
                verified_at=datetime.now(UTC).isoformat(),
                last_seen=datetime.now(UTC).isoformat(),
                collectors=[source],
                signals=[signal_id],
                status=CanonicalStatus.ACTIVE if not merge.merged else CanonicalStatus.MERGED,
            )

        admission = IgfAdmission(
            admitted=admitted,
            verdict=verdict,
            reasons=unique,
            explanation=explanation,
            allow_create_company=admitted and not merge.merged,
            evidence=[f"admitted:{admitted}", explanation, *trail[:6]],
        )

        return IgfSnapshot(
            signal_id=signal_id,
            source=source,
            source_role=role,
            candidate=candidate,
            evidence_items=evidence_items,
            website=website,
            domain=domain,
            score=score,
            merge=merge,
            canonical=canonical,
            admission=admission,
            payload={"trail": trail},
        )

    def evaluate_many(
        self,
        payloads: list[dict[str, Any]],
        *,
        existing: list[dict[str, Any]] | None = None,
    ) -> list[IgfSnapshot]:
        graph: list[dict[str, Any]] = list(existing or [])
        out: list[IgfSnapshot] = []
        for payload in payloads:
            snap = self.evaluate(payload, existing=graph)
            out.append(snap)
            if snap.admission.admitted and snap.canonical and snap.domain:
                graph.append(
                    {
                        "id": snap.canonical.id or snap.domain,
                        "official_domain": snap.domain,
                        "trade_name": snap.canonical.trade_name,
                        "legal_name": snap.canonical.legal_name,
                        "aliases": snap.canonical.aliases,
                    }
                )
        return out
