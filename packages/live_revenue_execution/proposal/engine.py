from __future__ import annotations

import base64
import hashlib

from live_revenue_execution.models.types import LREInput, ProposalPackage


class ProposalCenterEngine:
    """Deterministic proposal package + minimal PDF-like payload (no external GPT)."""

    def build(self, item: LREInput, *, version: str = "v1") -> ProposalPackage:
        tracking_id = hashlib.sha256(f"proposal:{item.company_id}:{version}".encode()).hexdigest()[:20]
        services = [item.recommended_service or "Custom engagement"]
        timeline = "6–10 weeks"
        pricing = item.expected_budget or "$25k–$55k"
        deliverables = [
            "Discovery report",
            "Solution architecture",
            "Working MVP / release",
            "Handover documentation",
            "30-day support window",
        ]
        terms = [
            "50% kickoff / 50% on delivery",
            "Change requests via written approval",
            "IP assigned to client on final payment",
        ]
        outline = [
            "Executive summary",
            "Current-state diagnosis",
            f"Recommended solution: {services[0]}",
            "Scope & deliverables",
            "Timeline & milestones",
            "Commercials & ROI",
            "Terms",
            "Next steps",
        ]
        roi = "3–6x within 12 months" if "ai" in services[0].lower() or "automation" in services[0].lower() else "2–4x within 12 months"
        pdf_text = self._pdf_text(item, services[0], timeline, pricing, deliverables, roi)
        pdf_b64 = base64.b64encode(pdf_text.encode("utf-8")).decode("ascii")
        return ProposalPackage(
            company_id=item.company_id,
            company_name=item.company_name,
            title=f"{item.company_name} — {services[0]} Proposal",
            version=version,
            services=services,
            timeline=timeline,
            pricing=pricing,
            case_studies=list(item.case_studies)[:6],
            roi=roi,
            deliverables=deliverables,
            terms=terms,
            outline=outline,
            pdf_base64=pdf_b64,
            tracking_id=tracking_id,
            evidence=[f"version:{version}", f"tracking_id:{tracking_id}", f"service:{services[0]}"],
        )

    def _pdf_text(
        self,
        item: LREInput,
        service: str,
        timeline: str,
        pricing: str,
        deliverables: list[str],
        roi: str,
    ) -> str:
        lines = [
            f"PROPOSAL — {item.company_name}",
            f"Service: {service}",
            f"Timeline: {timeline}",
            f"Pricing: {pricing}",
            f"ROI: {roi}",
            "",
            "Deliverables:",
            *[f"- {d}" for d in deliverables],
            "",
            "Prepared by Inowix via Beacon LRE",
        ]
        return "\n".join(lines)
