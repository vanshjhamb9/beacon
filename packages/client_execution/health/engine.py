from __future__ import annotations

from client_execution.models.types import ClientExecutionInput, ClientHealth, ClientLifecycleStage


class ClientHealthEngine:
    def score(self, item: ClientExecutionInput, *, stage: ClientLifecycleStage) -> ClientHealth:
        communication = max(0.0, min(100.0, float(item.communication_score)))
        delivery = max(0.0, min(100.0, float(item.delivery_progress)))
        delay = max(0.0, min(100.0, item.delay_days * 8.0))
        risk = max(0.0, min(100.0, len(item.risks) * 12.0 + item.open_issues * 10.0 + delay * 0.4))
        satisfaction = max(0.0, min(100.0, float(item.satisfaction)))
        meeting_freq = max(0.0, min(100.0, item.meetings_last_30d * 20.0))
        renewal = 55.0 + (satisfaction * 0.25) + (communication * 0.1) - (risk * 0.2)
        if item.renewal_due or (item.days_to_renewal is not None and item.days_to_renewal <= 60):
            renewal += 8.0
        if stage == ClientLifecycleStage.LOST_CLIENT:
            renewal = 5.0
        upsell = 30.0 + len(item.growth_signals + item.hiring_signals + item.funding_signals) * 8.0
        if item.upsell_signal:
            upsell += 15.0
        overall = max(
            0.0,
            min(
                100.0,
                communication * 0.2
                + delivery * 0.25
                + satisfaction * 0.25
                + meeting_freq * 0.1
                + (100.0 - risk) * 0.2,
            ),
        )
        status = "healthy"
        if overall < 40 or risk >= 60:
            status = "at_risk"
        elif overall < 60:
            status = "watch"
        if stage == ClientLifecycleStage.LOST_CLIENT:
            status = "lost"
        return ClientHealth(
            communication_score=round(communication, 2),
            delivery_score=round(delivery, 2),
            risk_score=round(risk, 2),
            delay_score=round(delay, 2),
            satisfaction_score=round(satisfaction, 2),
            meeting_frequency_score=round(meeting_freq, 2),
            open_issues=int(item.open_issues),
            renewal_probability=round(max(0.0, min(100.0, renewal)), 2),
            upsell_probability=round(max(0.0, min(100.0, upsell)), 2),
            overall_health=round(overall, 2),
            status=status,
            evidence=[f"overall:{overall}", f"risk:{risk}", f"status:{status}"],
        )
