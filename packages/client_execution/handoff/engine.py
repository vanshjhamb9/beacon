from __future__ import annotations

from client_execution.models.types import ClientExecutionInput, ClientLifecycleStage, ProjectHandoff


class ProjectHandoffEngine:
    def generate(self, item: ClientExecutionInput, *, stage: ClientLifecycleStage) -> ProjectHandoff:
        services = ", ".join(item.services_purchased[:3]) or "Agreed engagement"
        dossier = (
            f"Client dossier for {item.company_name} ({item.industry or 'Unknown industry'}). "
            f"Stage: {stage.value}. Contract value: {item.contract_value:,.0f}."
        )
        meeting = (
            item.meeting_history[-1].get("summary")
            if item.meeting_history and isinstance(item.meeting_history[-1], dict)
            else "Kickoff / discovery context captured from sales handoff."
        )
        return ProjectHandoff(
            client_dossier=dossier,
            meeting_summary=str(meeting),
            business_goals=list(item.business_goals)[:10] or ["Deliver measurable operational outcomes"],
            pain_points=list(item.pain_points)[:10] or ["Manual processes"],
            agreed_solution=item.agreed_solution or f"Deliver {services}",
            scope_summary=item.scope_summary or f"Scoped delivery of {services} for {item.company_name}",
            timeline=[str(t.get("title") if isinstance(t, dict) else t) for t in item.timeline][:12]
            or ["Kickoff", "Requirements", "Build", "Launch"],
            known_objections=list(item.known_objections)[:8],
            decision_history=list(item.decision_history)[:12] or ["Won via Beacon sales motion"],
            sales_notes=list(item.sales_notes)[:12],
            founder_notes=list(item.founder_notes)[:12],
            evidence=["handoff:auto", f"stage:{stage.value}", "delivery_team:ready"],
        )
