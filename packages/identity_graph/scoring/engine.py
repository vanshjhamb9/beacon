"""Identity scoring — admit only with official website + name + identity source."""

from __future__ import annotations

from identity_graph.models.types import IdentityCandidate, IdentityEvidence, IdentityScore, SourceRole


class IdentityScoringEngine:
    PASS_THRESHOLD = 70.0

    def score(
        self,
        candidate: IdentityCandidate,
        *,
        website: str | None,
        domain: str | None,
        evidence_items: list[IdentityEvidence],
    ) -> IdentityScore:
        breakdown: dict[str, float] = {}
        evidence: list[str] = []

        name_pts = 25.0 if candidate.name and candidate.name.lower() != "unknown" else 0.0
        breakdown["name"] = name_pts
        if name_pts:
            evidence.append("name_present")

        website_pts = 40.0 if website and domain else 0.0
        breakdown["website"] = website_pts
        if website_pts:
            evidence.append(f"website:{domain}")

        role_pts = 20.0 if candidate.source_role == SourceRole.IDENTITY else 0.0
        if candidate.source_role == SourceRole.INTENT:
            role_pts = 5.0
        breakdown["source_role"] = role_pts
        evidence.append(f"role:{candidate.source_role.value}")

        ev_pts = min(15.0, 3.0 * len(evidence_items))
        breakdown["evidence_volume"] = ev_pts
        evidence.append(f"evidence_count:{len(evidence_items)}")

        total = sum(breakdown.values())
        passed = total >= self.PASS_THRESHOLD and bool(website and domain) and name_pts > 0
        if candidate.source_role != SourceRole.IDENTITY:
            passed = False
            evidence.append("non_identity_source_cannot_admit")
        return IdentityScore(score=total, passed=passed, breakdown=breakdown, evidence=evidence)
