"""Quality dashboard — aggregated metrics for /quality endpoint."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from discovery_quality_engine.quality_engine import (
    QualityDecision,
    QualityEvent,
    QualitySnapshot,
)


class QualityDashboard:
    def __init__(self) -> None:
        self._events: list[QualityEvent] = []

    def record(self, event: QualityEvent) -> None:
        self._events.append(event)

    def record_batch(self, events: list[QualityEvent]) -> None:
        self._events.extend(events)

    def snapshot(self, *, now: datetime | None = None) -> QualitySnapshot:
        current = now or datetime.now(UTC)
        total = len(self._events)
        accepted = sum(1 for e in self._events if e.decision == QualityDecision.ACCEPT)
        rejected = sum(1 for e in self._events if e.decision == QualityDecision.REJECT)

        freshness_fails = sum(
            1 for e in self._events
            if e.decision == QualityDecision.REJECT and "STALE_SIGNAL" in e.rejection_reasons
        )
        duplicate_fails = sum(
            1 for e in self._events
            if e.decision == QualityDecision.REJECT and any(
                r.startswith("DUPLICATE_") for r in e.rejection_reasons
            )
        )
        competitor_fails = sum(
            1 for e in self._events
            if e.decision == QualityDecision.REJECT and "COMPETITOR" in e.rejection_reasons
        )
        website_fails = sum(
            1 for e in self._events
            if e.decision == QualityDecision.REJECT and any(
                r in ("PARKED_DOMAIN", "COMING_SOON", "NOT_FOUND_404", "MAINTENANCE",
                      "SPAM_WEBSITE", "NO_HTTPS", "LOW_CONTENT", "DOMAIN_FOR_SALE", "INACTIVE_WEBSITE")
                for r in e.rejection_reasons
            )
        )
        buying_signal_fails = sum(
            1 for e in self._events
            if e.decision == QualityDecision.REJECT and "NO_BUYING_SIGNAL" in e.rejection_reasons
        )
        ai_fails = sum(
            1 for e in self._events
            if e.decision == QualityDecision.REJECT and "AI_COMPANY" in e.rejection_reasons
        )
        icp_fails = sum(
            1 for e in self._events
            if e.decision == QualityDecision.REJECT and "OUTSIDE_ICP" in e.rejection_reasons
        )
        region_fails = sum(
            1 for e in self._events
            if e.decision == QualityDecision.REJECT and "UNSUPPORTED_REGION" in e.rejection_reasons
        )
        source_fails = sum(
            1 for e in self._events
            if e.decision == QualityDecision.REJECT and "LOW_SOURCE_TRUST" in e.rejection_reasons
        )
        activity_fails = sum(
            1 for e in self._events
            if e.decision == QualityDecision.REJECT and "NO_RECENT_ACTIVITY" in e.rejection_reasons
        )
        expired = sum(
            1 for e in self._events
            if e.decision == QualityDecision.REJECT and "EXPIRED_OPPORTUNITY" in e.rejection_reasons
        )

        acceptance_rate = (accepted / total * 100) if total > 0 else 0.0

        reason_counts: dict[str, int] = {}
        for event in self._events:
            for reason in event.rejection_reasons:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
        top_reasons = sorted(reason_counts.items(), key=lambda x: -x[1])[:10]

        connector_quality: dict[str, float] = {}
        connector_counts: dict[str, dict[str, int]] = {}
        for event in self._events:
            source = event.source
            if source not in connector_counts:
                connector_counts[source] = {"total": 0, "accepted": 0}
            connector_counts[source]["total"] += 1
            if event.decision == QualityDecision.ACCEPT:
                connector_counts[source]["accepted"] += 1
        for source, counts in connector_counts.items():
            connector_quality[source] = (
                counts["accepted"] / counts["total"] * 100 if counts["total"] > 0 else 0.0
            )

        return QualitySnapshot(
            signals_collected=total,
            signals_accepted=accepted,
            signals_rejected=rejected,
            acceptance_rate=acceptance_rate,
            freshness_failures=freshness_fails,
            duplicate_failures=duplicate_fails,
            competitor_failures=competitor_fails,
            website_failures=website_fails,
            buying_signal_failures=buying_signal_fails,
            ai_company_failures=ai_fails,
            icp_failures=icp_fails,
            region_failures=region_fails,
            source_trust_failures=source_fails,
            activity_failures=activity_fails,
            expired_opportunities=expired,
            connector_quality=connector_quality,
            top_rejection_reasons=[{"reason": r, "count": c} for r, c in top_reasons],
            created_at=current,
        )

    def summary(self) -> dict[str, Any]:
        snap = self.snapshot()
        return {
            "signals_collected": snap.signals_collected,
            "signals_accepted": snap.signals_accepted,
            "signals_rejected": snap.signals_rejected,
            "acceptance_rate": round(snap.acceptance_rate, 2),
            "freshness_failures": snap.freshness_failures,
            "duplicate_failures": snap.duplicate_failures,
            "competitor_failures": snap.competitor_failures,
            "website_failures": snap.website_failures,
            "buying_signal_failures": snap.buying_signal_failures,
            "ai_company_failures": snap.ai_company_failures,
            "icp_failures": snap.icp_failures,
            "region_failures": snap.region_failures,
            "source_trust_failures": snap.source_trust_failures,
            "activity_failures": snap.activity_failures,
            "expired_opportunities": snap.expired_opportunities,
            "connector_quality": snap.connector_quality,
            "top_rejection_reasons": snap.top_rejection_reasons,
        }

    def events_by_decision(self, decision: QualityDecision) -> list[QualityEvent]:
        return [e for e in self._events if e.decision == decision]

    def events_by_gate(self, gate: str) -> list[QualityEvent]:
        return [e for e in self._events if gate in e.gates_failed]

    def rejection_reasons_summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in self._events:
            for reason in event.rejection_reasons:
                counts[reason] = counts.get(reason, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: -x[1]))

    def clear(self) -> None:
        self._events.clear()
