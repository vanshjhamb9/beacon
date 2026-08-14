from __future__ import annotations

import hashlib

from revenue_operations.models.types import (
    AlertKind,
    AlertLifecycle,
    OpportunitySignal,
    RadarSignal,
    RadarSignalKind,
    RevenueAlert,
    RevenueOperationsInput,
)


class SmartAlertEngine:
    """Deterministic alerts with dedupe keys and lifecycle starting at NEW."""

    def detect(
        self,
        item: RevenueOperationsInput,
        *,
        radar: list[RadarSignal] | None = None,
    ) -> list[RevenueAlert]:
        existing = set(item.existing_alert_keys)
        alerts: list[RevenueAlert] = []
        for opp in item.opportunities:
            alerts.extend(self._from_opportunity(opp))
        for signal in radar or []:
            alerts.extend(self._from_radar(signal))

        unique: list[RevenueAlert] = []
        seen: set[str] = set()
        for a in alerts:
            if a.dedupe_key in existing or a.dedupe_key in seen:
                continue
            seen.add(a.dedupe_key)
            unique.append(a)
        unique.sort(key=lambda a: (a.severity != "high", a.kind.value, a.title))
        return unique

    def transition(self, current: AlertLifecycle, target: AlertLifecycle) -> AlertLifecycle:
        allowed = {
            AlertLifecycle.NEW: {AlertLifecycle.VIEWED, AlertLifecycle.DISMISSED, AlertLifecycle.ARCHIVED},
            AlertLifecycle.VIEWED: {
                AlertLifecycle.RESOLVED,
                AlertLifecycle.DISMISSED,
                AlertLifecycle.ARCHIVED,
            },
            AlertLifecycle.RESOLVED: {AlertLifecycle.ARCHIVED},
            AlertLifecycle.DISMISSED: {AlertLifecycle.ARCHIVED},
            AlertLifecycle.ARCHIVED: set(),
        }
        if target == current:
            return current
        if target not in allowed.get(current, set()):
            raise ValueError(f"Invalid alert lifecycle: {current.value} -> {target.value}")
        return target

    def _from_opportunity(self, opp: OpportunitySignal) -> list[RevenueAlert]:
        out: list[RevenueAlert] = []
        if opp.reply_waiting and opp.probability >= 70:
            out.append(self._alert(AlertKind.HIGH_INTENT_REPLY, opp, "Respond to high-intent reply", "high"))
        if opp.meeting_today:
            out.append(self._alert(AlertKind.MEETING_BOOKED, opp, "Prepare meeting pack", "high"))
        if opp.stage and "stopped" in opp.stage.lower():
            out.append(self._alert(AlertKind.CAMPAIGN_STOPPED, opp, "Review campaign stop reason", "medium"))
        if opp.reply_waiting and opp.days_in_stage >= 2:
            out.append(self._alert(AlertKind.REPLY_OVERDUE, opp, "Reply overdue — contact now", "high"))
        if opp.probability > 0 and opp.probability < 35 and opp.days_in_stage >= 5:
            out.append(self._alert(AlertKind.LEAD_QUALITY_DROPPED, opp, "Re-qualify or archive", "medium"))
        if opp.proposal_pending and opp.days_in_stage >= 5:
            out.append(self._alert(AlertKind.PROPOSAL_OVERDUE, opp, "Send or update proposal", "high"))
        if opp.at_risk:
            out.append(self._alert(AlertKind.LOST_DEAL_RISK, opp, "Mitigate loss risk", "high"))
        if opp.probability >= 80 and opp.pipeline_value >= 25000:
            out.append(
                self._alert(AlertKind.REVENUE_OPPORTUNITY_INCREASED, opp, "Prioritize high-value opportunity", "medium")
            )
        return out

    def _from_radar(self, signal: RadarSignal) -> list[RevenueAlert]:
        mapping = {
            RadarSignalKind.FUNDING: AlertKind.FUNDING_DETECTED,
            RadarSignalKind.HIRING: AlertKind.LARGE_HIRING_DETECTED,
            RadarSignalKind.HIRING_AI_ENGINEERS: AlertKind.LARGE_HIRING_DETECTED,
            RadarSignalKind.DECISION_MAKER_CHANGE: AlertKind.DECISION_MAKER_CHANGED,
            RadarSignalKind.LEADERSHIP_CHANGE: AlertKind.DECISION_MAKER_CHANGED,
        }
        kind = mapping.get(signal.kind)
        if kind is None:
            return []
        dedupe = self._dedupe(kind.value, str(signal.company_id or signal.company_name), signal.kind.value)
        return [
            RevenueAlert(
                alert_id=dedupe[:16],
                kind=kind,
                title=f"{kind.value.replace('_', ' ').title()}: {signal.company_name}",
                severity="medium" if signal.intensity < 70 else "high",
                company_id=signal.company_id,
                company_name=signal.company_name,
                recommendation=signal.detail,
                lifecycle=AlertLifecycle.NEW,
                evidence=list(signal.evidence),
                dedupe_key=dedupe,
            )
        ]

    def _alert(self, kind: AlertKind, opp: OpportunitySignal, recommendation: str, severity: str) -> RevenueAlert:
        dedupe = self._dedupe(kind.value, str(opp.company_id or opp.company_name), opp.stage or "")
        return RevenueAlert(
            alert_id=dedupe[:16],
            kind=kind,
            title=f"{kind.value.replace('_', ' ').title()}: {opp.company_name}",
            severity=severity,
            company_id=opp.company_id,
            company_name=opp.company_name,
            recommendation=recommendation,
            lifecycle=AlertLifecycle.NEW,
            evidence=[f"prob:{opp.probability}", f"stage:{opp.stage or 'n/a'}"],
            dedupe_key=dedupe,
        )

    def _dedupe(self, *parts: str) -> str:
        raw = "|".join(parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
