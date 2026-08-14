"""Evidence graph — Signal → Website → Evidence → Company (not Signal → Company)."""

from __future__ import annotations

from typing import Any

from entity_resolution.models.types import EntityCandidate, EvidenceEdge, OfficialWebsite, UNKNOWN


class EvidenceGraphEngine:
    def build(
        self,
        *,
        signal_id: str,
        source: str,
        website: OfficialWebsite,
        entity: EntityCandidate,
        payload: dict[str, Any] | None = None,
    ) -> list[EvidenceEdge]:
        payload = payload or {}
        edges = [
            EvidenceEdge(
                signal_id=signal_id,
                website=website.website,
                company_key=None,
                edge_type="signal_to_website",
                source=source,
                evidence=[f"url:{payload.get('url')}", f"discovery:{website.source}"],
            )
        ]
        if website.discovered:
            edges.append(
                EvidenceEdge(
                    signal_id=signal_id,
                    website=website.website,
                    company_key=entity.normalized_key if entity.normalized_key != UNKNOWN else None,
                    edge_type="website_to_evidence",
                    source=website.source,
                    evidence=list(website.evidence[:6]),
                )
            )
            if entity.name != UNKNOWN:
                edges.append(
                    EvidenceEdge(
                        signal_id=signal_id,
                        website=website.website,
                        company_key=entity.normalized_key,
                        edge_type="evidence_to_company",
                        source=source,
                        evidence=[f"company:{entity.name}", f"domain:{website.domain}"],
                    )
                )
        return edges
