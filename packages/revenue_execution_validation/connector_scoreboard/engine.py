"""Connector Scoreboard — live grades from observed outcomes. No hardcoded thresholds per-connector."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from revenue_execution_validation.models.types import ConnectorGrade, ConnectorScore, RevSnapshot


class ConnectorScoreboardEngine:
    def score(
        self,
        snapshots: list[RevSnapshot],
        *,
        qa_by_source: dict[str, float] | None = None,
    ) -> list[ConnectorScore]:
        qa_by_source = qa_by_source or {}
        groups: dict[str, list[RevSnapshot]] = defaultdict(list)
        for s in snapshots:
            groups[s.source or "unknown"].append(s)

        out: list[ConnectorScore] = []
        for connector, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            signals = len(items)
            admitted = sum(1 for i in items if i.check.website_verified or i.check.checks.get("erowd"))
            ready = sum(1 for i in items if i.check.is_revenue_ready)
            dms = sum(1 for i in items if i.check.decision_maker)
            emails = sum(1 for i in items if i.check.business_email)
            dups = sum(1 for i in items if RejectionHasDuplicate(i))
            dup_rate = round(100.0 * dups / max(signals, 1), 2)
            ready_pct = round(100.0 * ready / max(signals, 1), 2)
            avg_quality = round(
                sum(i.check.confidence for i in items) / max(signals, 1),
                2,
            )
            qa = float(qa_by_source.get(connector) or 0.0)
            # Relative grade from observed rates (no per-connector constants)
            grade = self._grade(ready_pct=ready_pct, dup_rate=dup_rate, qa=qa, avg_quality=avg_quality)
            out.append(
                ConnectorScore(
                    connector=connector,
                    signals=signals,
                    companies_admitted=admitted,
                    revenue_ready=ready,
                    decision_makers=dms,
                    emails=emails,
                    duplicate_rate=dup_rate,
                    manual_qa_score=qa,
                    average_quality=avg_quality,
                    revenue_ready_pct=ready_pct,
                    grade=grade,
                    evidence=[
                        f"signals:{signals}",
                        f"ready_pct:{ready_pct}",
                        f"dup_rate:{dup_rate}",
                        f"grade:{grade.value}",
                    ],
                )
            )
        return out

    def _grade(self, *, ready_pct: float, dup_rate: float, qa: float, avg_quality: float) -> ConnectorGrade:
        score = ready_pct * 0.5 + avg_quality * 0.3 + qa * 0.2 - dup_rate * 0.4
        if score >= 40 and ready_pct >= 20 and dup_rate < 15:
            return ConnectorGrade.EXCELLENT
        if score >= 20 and ready_pct >= 8 and dup_rate < 30:
            return ConnectorGrade.GOOD
        if ready_pct < 2 and dup_rate >= 40:
            return ConnectorGrade.DISABLE_CANDIDATE
        return ConnectorGrade.WEAK


def RejectionHasDuplicate(snap: RevSnapshot) -> bool:
    from revenue_execution_validation.models.types import RejectionReason

    return RejectionReason.DUPLICATE in (snap.rejection_reasons or snap.check.rejection_reasons)
