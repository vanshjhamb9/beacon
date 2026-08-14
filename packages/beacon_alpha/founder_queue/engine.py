from __future__ import annotations

from typing import Any

from beacon_alpha.models.types import (
    AlphaSnapshot,
    AlphaVerdict,
    AttributedValue,
    CompanyScore,
    ContactEnrichmentResult,
    FounderQueueCard,
    IntentV2Result,
    UNKNOWN,
)

TOP_N = 10


class FounderQueueEngine:
    """Rule 6 — Top 10 only, dense outreach cards."""

    def build_card(
        self,
        *,
        company_id: str,
        company_name: str,
        intent: IntentV2Result,
        contacts: ContactEnrichmentResult,
        score: CompanyScore,
        payload: dict[str, Any],
    ) -> FounderQueueCard:
        dm = contacts.decision_makers[0] if contacts.decision_makers else {}
        email = UNKNOWN
        phone = UNKNOWN
        if dm.get("email") and dm.get("email") != UNKNOWN:
            email = str(dm["email"])
        elif contacts.emails:
            email = str(contacts.emails[0].value)
        if dm.get("phone") and dm.get("phone") != UNKNOWN:
            phone = str(dm["phone"])
        elif contacts.phones:
            phone = str(contacts.phones[0].value)

        evidence_snip = UNKNOWN
        for item in payload.get("evidence") or []:
            if isinstance(item, dict) and (item.get("summary") or item.get("text")):
                evidence_snip = str(item.get("summary") or item.get("text"))
                break
            if isinstance(item, str):
                evidence_snip = item
                break

        who = str(dm.get("name") or "the team")
        service = intent.best_service if intent.best_service != UNKNOWN else "a focused build"
        first_line = (
            f"Hi {who.split()[0] if who != 'the team' else 'there'} — noticed {intent.why_now.lower() if intent.why_now != UNKNOWN else 'a clear ops signal'}. "
            f"We help teams like yours with {service}. Open to a 15-min call?"
        )

        meeting = min(95.0, round(score.total * 0.55 + intent.scores.urgency * 0.25 + (10.0 if email != UNKNOWN else 0), 2))

        return FounderQueueCard(
            company_id=company_id,
            company=company_name,
            why_now=intent.why_now,
            pain=intent.pain,
            estimated_budget=intent.estimated_budget,
            best_service=intent.best_service,
            decision_maker=str(dm.get("name") or UNKNOWN),
            email=email,
            phone=phone,
            source=str(payload.get("source") or UNKNOWN),
            evidence=evidence_snip,
            confidence=round(score.total, 2),
            recommended_first_line=first_line,
            meeting_probability=meeting,
            score=score.total,
        )

    def top10(self, snapshots: list[AlphaSnapshot]) -> list[FounderQueueCard]:
        eligible = [
            s
            for s in snapshots
            if s.verdict == AlphaVerdict.SALES_READY
            and s.score.founder_visible
            and s.founder_card is not None
        ]
        eligible.sort(key=lambda s: s.score.total, reverse=True)
        cards = [s.founder_card for s in eligible if s.founder_card]
        # Deduplicate by company_id
        seen: set[str] = set()
        out: list[FounderQueueCard] = []
        for c in cards:
            if c.company_id in seen:
                continue
            seen.add(c.company_id)
            out.append(c)
            if len(out) >= TOP_N:
                break
        return out
