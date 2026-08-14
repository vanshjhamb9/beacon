from __future__ import annotations

from client_execution.models.types import ClientExecutionInput, ClientLifecycleStage, ClientWorkspace


class ClientWorkspaceEngine:
    def build(self, item: ClientExecutionInput, *, stage: ClientLifecycleStage) -> ClientWorkspace:
        services = item.services_purchased or ["Custom engagement"]
        summary = (
            f"{item.company_name} is in {stage.value.replace('_', ' ')} · "
            f"contract {item.contract_value:,.0f} · "
            f"services: {', '.join(services[:3])}."
        )
        return ClientWorkspace(
            executive_summary=summary,
            company=item.company_name,
            services_purchased=list(services)[:8],
            contract_value=float(item.contract_value),
            expected_delivery=item.expected_delivery,
            primary_contacts=list(item.primary_contacts)[:8],
            decision_makers=list(item.decision_makers)[:8],
            meeting_history=list(item.meeting_history)[:12],
            requirements=list(item.requirements)[:20],
            deliverables=list(item.deliverables)[:20],
            risks=list(item.risks)[:12],
            timeline=list(item.timeline)[:20],
            invoices_status="placeholder",
            support_requests=list(item.support_requests)[:12],
            renewal_date=item.renewal_date,
            evidence=[f"stage:{stage.value}", f"value:{item.contract_value}", "invoices:placeholder"],
        )
