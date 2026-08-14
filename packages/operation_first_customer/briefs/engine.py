"""Deterministic Outreach Brief — existing evidence only. No GPT."""

from __future__ import annotations

from typing import Any

from operation_first_customer.models.types import UNKNOWN, OutreachBrief


PAIN_BY_SERVICE = {
    "AI Recruiting Automation": ["Hiring velocity", "Manual screening load"],
    "AI Customer Support Automation": ["Support ticket volume", "Onboarding latency"],
    "AI Ops Automation": ["Ops toil", "Manual reconciliation"],
    "AI Research Ops Automation": ["Research workflow friction"],
    "AI Community Support Automation": ["Community moderation load"],
    "AI Product Analytics Automation": ["Insight lag", "Manual reporting"],
}

CTA_BY_STATUS_HINT = (
    ("hiring", "Offer a 15-min hiring workflow audit"),
    ("support", "Offer a support automation pilot"),
    ("yc", "Reference shared YC context; ask for a short intro call"),
    ("funding", "Ask how they're scaling ops post-raise"),
)


class OutreachBriefEngine:
    def build(self, company: dict[str, Any]) -> OutreachBrief:
        attrs = dict(company.get("attributes") or {})
        name = str(company.get("name") or UNKNOWN)
        domain = str(company.get("primary_domain") or company.get("domain") or "")
        website = f"https://{domain}" if domain else (attrs.get("official_website") or None)
        opp = dict(attrs.get("rrp_opportunity") or {})
        dm = attrs.get("rrp_decision_maker") or {}
        dm_display = attrs.get("decision_maker") or (
            f"{dm.get('full_name')} ({dm.get('job_title')})" if dm.get("full_name") else UNKNOWN
        )
        service = str(
            opp.get("recommended_service")
            or attrs.get("cir_best_service")
            or "AI Customer Support Automation"
        )
        why_now = str(attrs.get("rrp_why_now") or opp.get("why_now") or UNKNOWN)
        signals = list(attrs.get("buying_signals") or attrs.get("rrp_why_now_evidence") or [])
        evidence = list(opp.get("evidence") or attrs.get("rrp_why_now_evidence") or [])
        if website:
            evidence = list(dict.fromkeys([*evidence, f"website:{website}"]))
        if dm.get("source_url"):
            evidence = list(dict.fromkeys([*evidence, f"dm_url:{dm.get('source_url')}"]))

        confidence = float(attrs.get("rrp_confidence") or opp.get("confidence") or 0)
        trust = float(attrs.get("rrp_trust") or opp.get("trust") or 0)
        score = min(99.0, (confidence * 0.55) + (trust * 0.45))

        pain = list(PAIN_BY_SERVICE.get(service, ["Growth ops friction"]))
        blob = " ".join([why_now, *signals, service]).lower()
        cta = "Send first outreach using the template; request a 15-min call"
        for cue, text in CTA_BY_STATUS_HINT:
            if cue in blob:
                cta = text
                break

        first_msg = opp.get("recommended_first_message") or (
            f"Hi {{first_name}} — noticed {name} ({why_now[:80]}). "
            f"We help teams with {service}. Open to a 15-min look?"
        )

        return OutreachBrief(
            company=name,
            website=website,
            industry=str(attrs.get("industry") or opp.get("industry") or "Software"),
            decision_maker=str(dm_display),
            decision_maker_email=attrs.get("rrp_decision_maker_email") or opp.get("decision_maker_email"),
            business_email=attrs.get("business_email")
            or attrs.get("ofc_business_email")
            or opp.get("business_email"),
            why_now=why_now,
            recommended_service=service,
            evidence=[str(e) for e in evidence[:12]],
            confidence=confidence,
            trust=trust,
            revenue_ready_score=round(score, 1),
            recent_signals=[str(s) for s in signals[:8]],
            pain_points=pain,
            recommended_cta=cta,
            first_message_template=str(first_msg),
        )
