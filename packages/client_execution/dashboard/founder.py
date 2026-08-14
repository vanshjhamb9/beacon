from __future__ import annotations

from client_execution.models.types import (
    ClientExecutionInput,
    ClientHealth,
    FounderExecutiveView,
    UpsellRecommendation,
)


class FounderExecutiveEngine:
    def build(
        self,
        item: ClientExecutionInput,
        *,
        health: ClientHealth,
        upsells: list[UpsellRecommendation],
    ) -> FounderExecutiveView:
        running = sum(1 for p in item.projects if not p.blocked) or (1 if item.won and not item.archived else 0)
        renewals = 1 if item.renewal_due or (item.days_to_renewal is not None and item.days_to_renewal <= 90) else 0
        risks = 1 if health.status in {"at_risk", "lost"} or item.open_issues >= 3 else 0
        return FounderExecutiveView(
            revenue_closed=float(item.contract_value),
            projects_running=int(running),
            revenue_delivered=float(item.revenue_delivered),
            pending_payments="placeholder",
            renewals=renewals,
            upsells=len(upsells),
            client_risks=risks,
            team_capacity="placeholder",
            evidence=[
                f"closed:{item.contract_value}",
                f"delivered:{item.revenue_delivered}",
                "payments:placeholder",
                "capacity:placeholder",
            ],
        )
