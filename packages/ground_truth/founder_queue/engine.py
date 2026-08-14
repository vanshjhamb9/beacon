from __future__ import annotations

from typing import Any

from ground_truth.models.types import (
    CompanyTruthProfile,
    FounderQueueItem,
    GtSnapshot,
    GtVerdict,
    IntelligenceCard,
    UNKNOWN,
)

TOP_N = 10


class GtFounderQueueEngine:
    """Rule 7 — only 10 companies. Dense cards. Nothing else."""

    def build_item(
        self,
        *,
        truth: CompanyTruthProfile,
        card: IntelligenceCard,
        payload: dict[str, Any],
    ) -> FounderQueueItem:
        dm = truth.decision_makers[0].value if truth.decision_makers else UNKNOWN
        email = truth.contacts_email[0].value if truth.contacts_email else UNKNOWN
        phone = truth.contacts_phone[0].value if truth.contacts_phone else UNKNOWN
        evidence = truth.evidence_sources[0].value if truth.evidence_sources else (
            card.evidence[0] if card.evidence else UNKNOWN
        )
        deal = str(payload.get("estimated_deal") or payload.get("estimated_budget") or UNKNOWN)
        if deal == UNKNOWN and truth.employees.value not in (UNKNOWN, None):
            deal = "$25k-$60k"
        return FounderQueueItem(
            company_id=truth.company_id,
            company=truth.company_name,
            reason=str(truth.intent_reason.value if truth.intent_reason.value != UNKNOWN else card.pain),
            evidence=str(evidence),
            contact=str(dm if dm != UNKNOWN else email),
            email=str(email),
            phone=str(phone),
            decision_maker=str(dm),
            service=card.recommended_service,
            estimated_deal=deal,
            next_step=card.next_action,
            open_profile=f"/ground-truth/company/{truth.company_id}",
            approve=False,
            trust=truth.trust,
            score=card.probability,
        )

    def top10(self, snapshots: list[GtSnapshot]) -> list[FounderQueueItem]:
        # Compose-only CIR gate: when CIR classification is present, require Revenue Ready / Priority Account.
        # Absence of CIR data preserves prior GT behavior (no regression).
        _cir_ok = frozenset({"Revenue Ready", "Priority Account"})

        def _cir_allows(s: GtSnapshot) -> bool:
            cir = None
            for item in s.evidence or []:
                text = str(item)
                if text.startswith("cir_classification:"):
                    cir = text.split(":", 1)[-1].strip()
                    break
            if cir is None and s.card is not None:
                for item in s.card.evidence or []:
                    text = str(item)
                    if text.startswith("cir_classification:"):
                        cir = text.split(":", 1)[-1].strip()
                        break
            if cir is None:
                return True
            return cir in _cir_ok

        eligible = [
            s
            for s in snapshots
            if s.verdict in {GtVerdict.SALES_READY, GtVerdict.ENTERPRISE_READY}
            and s.founder_item is not None
            and s.questions.all_answered
            and s.production_lock.unlocked
            and _cir_allows(s)
        ]
        eligible.sort(key=lambda s: (s.trust, s.readiness), reverse=True)
        out: list[FounderQueueItem] = []
        seen: set[str] = set()
        for s in eligible:
            if s.company_id in seen or not s.founder_item:
                continue
            seen.add(s.company_id)
            out.append(s.founder_item)
            if len(out) >= TOP_N:
                break
        return out
