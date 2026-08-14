"""Founder Queue v3 — top 10 Revenue Ready only."""

from __future__ import annotations

from revenue_execution_validation.models.types import UNKNOWN, FounderQueueCardV3, RevSnapshot

TOP_N = 10


class FounderQueueV3Engine:
    def build(self, snapshots: list[RevSnapshot]) -> list[FounderQueueCardV3]:
        ready = [s for s in snapshots if s.check.is_revenue_ready]
        ready.sort(key=lambda s: (s.check.confidence, 1 if s.check.decision_maker else 0), reverse=True)
        cards: list[FounderQueueCardV3] = []
        seen: set[str] = set()
        for s in ready:
            if s.company_id in seen:
                continue
            seen.add(s.company_id)
            c = s.check
            readiness = "Ready" if c.business_email and c.decision_maker else ("Email only" if c.business_email else "Incomplete")
            cards.append(
                FounderQueueCardV3(
                    company_id=s.company_id,
                    company=c.company_name,
                    logo_url=UNKNOWN,
                    website=c.website,
                    industry=c.industry,
                    country=c.country,
                    why_now=c.why_now,
                    opportunity=c.opportunity,
                    service_match=c.best_service,
                    verified_email=c.email,
                    decision_maker=c.decision_maker_name,
                    confidence=c.confidence,
                    source=c.source or s.source,
                    evidence=[
                        f"source:{e.source}"
                        for e in c.evidence[:3]
                    ]
                    + [f"why:{c.why_now}", f"service:{c.best_service}"],
                    contact_readiness=readiness,
                    dossier_url=f"/companies/{s.company_id}",
                    revenue_ready=True,
                )
            )
            if len(cards) >= TOP_N:
                break
        return cards
