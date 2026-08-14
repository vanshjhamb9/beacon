from __future__ import annotations

from client_execution.models.types import (
    ClientExecutionInput,
    ClientHealth,
    DeliveryDashboard,
    UpsellRecommendation,
)


class DeliveryDashboardEngine:
    def build(
        self,
        item: ClientExecutionInput,
        *,
        health: ClientHealth,
        upsells: list[UpsellRecommendation],
    ) -> DeliveryDashboard:
        todays = []
        milestones = []
        blocked = []
        at_risk = []
        for p in item.projects:
            row = {
                "company_name": item.company_name,
                "project": p.name,
                "stage": p.stage,
                "milestone": p.milestone,
                "deliverable": p.deliverable,
            }
            if p.due_today or p.deliverable:
                todays.append(row)
            if p.milestone:
                milestones.append(row)
            if p.blocked:
                blocked.append(row)
            if p.at_risk or health.status == "at_risk":
                at_risk.append({**row, "reason": "Project/client risk"})
        if not todays and item.deliverables:
            todays.append({"company_name": item.company_name, "deliverable": item.deliverables[0]})
        renewals = []
        if item.renewal_due or (item.days_to_renewal is not None and item.days_to_renewal <= 90):
            renewals.append(
                {
                    "company_name": item.company_name,
                    "renewal_date": item.renewal_date,
                    "probability": health.renewal_probability,
                }
            )
        return DeliveryDashboard(
            todays_deliveries=todays[:10],
            upcoming_milestones=milestones[:10],
            blocked_projects=blocked[:10],
            at_risk_projects=at_risk[:10],
            client_health=[{"company_name": item.company_name, "status": health.status, "score": health.overall_health}],
            renewals=renewals,
            upsells=[{"service": u.service.value, "title": u.title, "confidence": u.confidence} for u in upsells[:5]],
            evidence=[f"projects:{len(item.projects)}", f"health:{health.status}"],
        )
