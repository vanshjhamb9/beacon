from __future__ import annotations

import hashlib

from client_execution.models.types import ClientExecutionInput, UpsellRecommendation, UpsellService


SIGNAL_MAP: list[tuple[list[str], UpsellService, str, float]] = [
    (["hiring", "engineer", "team growth"], UpsellService.INTERNAL_TOOLS, "Hiring growth suggests internal tooling needs", 78.0),
    (["funding", "raised", "series"], UpsellService.CUSTOM_SAAS, "Funding enables product / platform investment", 82.0),
    (["usage", "adoption", "active users"], UpsellService.ANALYTICS, "Usage growth benefits from analytics", 76.0),
    (["support", "ticket", "incident"], UpsellService.AI_AUTOMATION, "Support load can be automated", 80.0),
    (["expansion", "new market", "new office"], UpsellService.WEBSITE_UPGRADE, "Expansion often needs digital presence upgrade", 74.0),
    (["mobile", "app", "ios", "android"], UpsellService.MOBILE_APP, "Mobile signals detected", 85.0),
    (["crm", "salesforce", "pipeline"], UpsellService.CRM, "CRM modernization opportunity", 79.0),
    (["automation", "manual", "ops"], UpsellService.AI_AUTOMATION, "Automation opportunity from ops signals", 81.0),
]


class UpsellEngine:
    """Deterministic upsell suggestions — founder approval required, never auto-applied."""

    def recommend(self, item: ClientExecutionInput) -> list[UpsellRecommendation]:
        blob = " ".join(
            item.growth_signals
            + item.hiring_signals
            + item.funding_signals
            + item.usage_signals
            + item.expansion_signals
            + [str(s.get("summary") if isinstance(s, dict) else s) for s in item.support_requests]
            + item.pain_points
        ).lower()
        if item.upsell_signal and not blob:
            blob = "growth expansion automation"

        out: list[UpsellRecommendation] = []
        seen: set[UpsellService] = set()
        for patterns, service, reason, conf in SIGNAL_MAP:
            hits = [p for p in patterns if p in blob]
            if not hits and not (item.upsell_signal and service == UpsellService.AI_AUTOMATION):
                continue
            if service in seen:
                continue
            seen.add(service)
            rid = hashlib.sha256(f"{item.company_id}|{service.value}|{reason}".encode()).hexdigest()[:16]
            out.append(
                UpsellRecommendation(
                    recommendation_id=rid,
                    service=service,
                    title=f"Upsell {service.value} to {item.company_name}",
                    reason=reason if hits else "Client flagged for upsell review",
                    confidence=min(95.0, conf + len(hits) * 2.0),
                    requires_founder_approval=True,
                    modifies_production=False,
                    evidence=[f"hits:{','.join(hits[:3])}" if hits else "flag:upsell_signal", "founder_approval:required"],
                )
            )
        out.sort(key=lambda r: (-r.confidence, r.service.value))
        return out[:7]
