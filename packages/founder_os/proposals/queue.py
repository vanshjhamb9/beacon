from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from founder_os.models.types import FounderOsInput, ProposalQueueItem, ProposalStatus


DEFAULT_CASE_STUDIES = {
    "COMAI": ["Ecommerce support deflection", "WhatsApp commerce lift"],
    "Custom AI": ["Ops forecasting for SaaS", "Document AI intake"],
    "Website": ["B2B rebuild + SEO", "Lead-gen redesign"],
    "Automation": ["Hire-to-onboard automation", "Invoice reconciliation"],
}


class ProposalQueueEngine:
    def build(self, data: FounderOsInput) -> list[ProposalQueueItem]:
        now = data.now or datetime.now(UTC)
        items: list[ProposalQueueItem] = []
        for row in data.proposal_candidates:
            company_id = self._uuid(row.get("company_id"))
            if company_id is None:
                continue
            service = str(row.get("recommended_service") or "Custom AI")
            services = [service] + [str(s) for s in (row.get("secondary_services") or [])]
            budget = str(row.get("budget_range") or row.get("expected_budget") or "$25k–$55k")
            timeline = str(row.get("estimated_timeline") or row.get("expected_timeline") or "6–10 weeks")
            status_raw = str(row.get("proposal_status") or ProposalStatus.NEEDED.value)
            try:
                status = ProposalStatus(status_raw)
            except ValueError:
                status = ProposalStatus.NEEDED
            architecture = str(
                row.get("suggested_architecture")
                or f"Discovery → scoped {service} MVP → integration → handoff"
            )
            cases = [str(c) for c in (row.get("case_studies") or DEFAULT_CASE_STUDIES.get(service, DEFAULT_CASE_STUDIES["Custom AI"]))]
            items.append(
                ProposalQueueItem(
                    company_id=company_id,
                    company_name=str(row.get("company_name") or "Unknown"),
                    estimated_scope=str(row.get("estimated_scope") or f"Scoped {service} engagement"),
                    recommended_services=list(dict.fromkeys(services)),
                    estimated_timeline=timeline,
                    budget_range=budget,
                    suggested_architecture=architecture,
                    case_studies=cases[:4],
                    proposal_status=status,
                    owner=str(row.get("owner") or "founder"),
                    deadline=self._deadline(row.get("deadline"), now),
                    evidence=[
                        f"service:{service}",
                        f"budget:{budget}",
                        f"status:{status.value}",
                    ],
                )
            )
        return items

    def _uuid(self, value: object) -> UUID | None:
        if value is None:
            return None
        try:
            return value if isinstance(value, UUID) else UUID(str(value))
        except (TypeError, ValueError):
            return None

    def _deadline(self, value: object, now: datetime) -> datetime:
        if isinstance(value, datetime):
            return value
        if value:
            try:
                return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                pass
        return now + timedelta(days=3)
