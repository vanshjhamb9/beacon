"""Deterministic opportunity summary — template only, no GPT."""

from __future__ import annotations

from revenue_readiness_perfection.models.types import OpportunitySummary, UNKNOWN

SERVICE_BY_SIGNAL = (
    ("hiring", "AI Recruiting Automation"),
    ("customer support", "AI Customer Support Automation"),
    ("support", "AI Customer Support Automation"),
    ("onboarding", "AI Customer Support Automation"),
    ("payments", "AI Ops Automation"),
    ("genomics", "AI Research Ops Automation"),
    ("game", "AI Community Support Automation"),
    ("analytics", "AI Product Analytics Automation"),
)


class OpportunitySummaryEngine:
    def build(
        self,
        *,
        company: str,
        industry: str,
        website: str,
        decision_maker: str,
        business_email: str,
        dm_email: str | None,
        why_now: str,
        signals: list[str],
        evidence: list[str],
        confidence: float,
        trust: float,
        revenue_ready: bool,
    ) -> OpportunitySummary:
        blob = " ".join([why_now, industry, *signals]).lower()
        service = "AI Customer Support Automation"
        for cue, svc in SERVICE_BY_SIGNAL:
            if cue in blob:
                service = svc
                break
        reason = why_now if why_now and why_now != UNKNOWN else f"{company} matches {service}"
        intent = min(99.0, 70.0 + (10.0 if signals else 0) + (8.0 if "hiring" in blob else 0) + (5.0 if "yc" in blob else 0))
        first_msg = (
            f"Hi {{first_name}} — noticed {company} ({why_now[:80]}). "
            f"We help teams like yours with {service}. Open to a 15-min look?"
        )
        return OpportunitySummary(
            company=company,
            industry=industry or "Software",
            employees=UNKNOWN,
            recommended_service=service,
            reason=reason,
            buying_intent=intent,
            decision_maker=decision_maker,
            business_email=business_email,
            decision_maker_email=dm_email,
            website=website,
            evidence=evidence[:8],
            recommended_first_message=first_msg,
            why_now=why_now,
            confidence=confidence,
            trust=trust,
            revenue_ready=revenue_ready,
        )
