"""Currentness, intent, SALES_READY hard gates, and CTO 15-minute test."""

from __future__ import annotations

from datetime import UTC, datetime

from packages.cybersecurity_discovery.schema import (
    Currentness,
    CyberOpportunity,
    FinalVerdict,
    IntentLevel,
    OpportunityType,
    OutsourcingIntent,
    evidence_item,
)

FUNNEL_STAGES = (
    "DISCOVERED",
    "BUYING_EVENT",
    "SECURITY_PROBLEM_VERIFIED",
    "BUYER_VERIFIED",
    "CURRENT",
    "COMMERCIAL_INTENT",
    "SERVICE_MATCH",
    "CONTACT_VERIFIED",
    "SALES_READY",
)

SALES_READY_GATES = (
    "real_buying_event",
    "requirement_verified",
    "current_enough",
    "buyer_or_company_identifiable",
    "security_problem_verified",
    "external_commercial_intent",
    "service_match",
    "contact_path",
    "not_competitor",
    "safety_clear",
    "not_partner",
)


def classify_currentness(published_at: str | None, observed_at: str, still_active: bool = False) -> tuple[str, int]:
    """0-7 HOT, 8-30 CURRENT, 31-60 AGING, 61-90 STALE, 90+ REJECT unless still active.

    Missing/unparseable dates are CURRENT, not 90-day rejects. A live collector
    observed the post today; killing it for lack of a timestamp throws away buyers.
    """
    if not published_at:
        return Currentness.CURRENT.value, 0
    parsed = _parse_dt(published_at)
    if parsed is None:
        return Currentness.CURRENT.value, 0
    now = _parse_dt(observed_at) or datetime.now(UTC)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    days = max(0, (now - parsed).days)
    if days <= 7:
        return Currentness.HOT.value, days
    if days <= 30:
        return Currentness.CURRENT.value, days
    if days <= 60:
        return Currentness.AGING.value, days
    if days <= 90:
        return Currentness.STALE.value, days
    if still_active:
        return Currentness.STALE.value, days
    return Currentness.REJECT.value, days


def classify_intent(opp: CyberOpportunity) -> str:
    """HOT/HIGH require explicit or strong commercial purchase intent."""
    if opp.opportunity_type == OpportunityType.REJECT.value:
        return IntentLevel.UNKNOWN.value
    text = f"{opp.title} {opp.body_snippet} {opp.buying_event or ''}".lower()
    explicit_hire = any(
        t in text
        for t in (
            "looking for cybersecurity",
            "looking for a cybersecurity",
            "looking for pentest",
            "looking for penetration",
            "looking for a pentest",
            "need pentest",
            "need a pentest",
            "need penetration testing",
            "need vapt",
            "need a vapt",
            "recommend a pentest",
            "recommend a vapt",
            "looking for recommendations",
            "vapt provider",
            "security consultant",
            "vulnerability assessment",
            "security remediation",
            "external security team",
            "penetration testing company",
            "cybersecurity company",
        )
    )
    if explicit_hire and opp.outsourcing_intent == OutsourcingIntent.EXPLICIT.value:
        return IntentLevel.HOT.value
    if opp.outsourcing_intent in {OutsourcingIntent.EXPLICIT.value, OutsourcingIntent.HIGH.value} and opp.buying_event_verified:
        return IntentLevel.HIGH.value
    if opp.buying_event_verified:
        return IntentLevel.MEDIUM.value
    if opp.security_problem:
        return IntentLevel.LOW.value
    return IntentLevel.UNKNOWN.value


def evaluate_gates(opp: CyberOpportunity) -> CyberOpportunity:
    """Apply sequential funnel + hard SALES_READY gate. Partners never become SALES_READY."""
    if opp.final_verdict == FinalVerdict.REJECT.value and opp.rejection_reason:
        return opp

    currentness, days = classify_currentness(
        opp.published_at,
        opp.observed_at,
        still_active=_still_active(opp),
    )
    opp.currentness = currentness
    opp.currentness_evidence.append(
        evidence_item(
            "currentness",
            currentness,
            opp.source_name,
            opp.source_url,
            "HIGH" if opp.published_at else "LOW",
            opp.observed_at,
        )
    )
    if days != 999:
        opp.currentness_evidence.append(
            evidence_item("days_old", days, "beacon", "", "HIGH", opp.observed_at)
        )

    opp.intent_level = classify_intent(opp)
    failed: list[str] = []

    real_buying = opp.buying_event_verified and opp.opportunity_type != OpportunityType.REJECT.value
    if not real_buying:
        failed.append("real_buying_event")

    if not opp.requirement_verified:
        failed.append("requirement_verified")

    security_ok = bool(opp.security_problem and opp.security_problem_evidence)
    if security_ok:
        opp.funnel_stage = "SECURITY_PROBLEM_VERIFIED"
    else:
        failed.append("security_problem_verified")

    identity_ok = _identifiable(opp)
    if identity_ok:
        opp.funnel_stage = "BUYER_VERIFIED"
    else:
        failed.append("buyer_or_company_identifiable")

    current_ok = currentness in {
        Currentness.HOT.value,
        Currentness.CURRENT.value,
        Currentness.AGING.value,
    } or (currentness == Currentness.STALE.value and _still_active(opp))
    if current_ok:
        opp.funnel_stage = "CURRENT"
    else:
        failed.append("current_enough")

    commercial_ok = opp.outsourcing_intent in {
        OutsourcingIntent.EXPLICIT.value,
        OutsourcingIntent.HIGH.value,
        OutsourcingIntent.IMPLICIT.value,
    } and opp.intent_level in {IntentLevel.HOT.value, IntentLevel.HIGH.value, IntentLevel.MEDIUM.value}
    if commercial_ok:
        opp.funnel_stage = "COMMERCIAL_INTENT"
    else:
        failed.append("external_commercial_intent")

    service_ok = bool(opp.service_match) and opp.service_match_confidence in {"HIGH", "MEDIUM"}
    if service_ok:
        opp.funnel_stage = "SERVICE_MATCH"
    else:
        failed.append("service_match")

    contact_ok = opp.contactability in {"HIGH", "MEDIUM", "LOW"}
    if contact_ok:
        opp.funnel_stage = "CONTACT_VERIFIED"
    else:
        failed.append("contact_path")

    if opp.competitor:
        failed.append("not_competitor")
    if not opp.safety_clear:
        failed.append("safety_clear")

    is_partner = opp.opportunity_type == OpportunityType.SECURITY_PARTNER.value
    if is_partner:
        failed.append("not_partner")

    opp.failed_gates = sorted(set(failed))

    if not real_buying:
        opp.final_verdict = FinalVerdict.REJECT.value
        opp.rejection_reason = opp.rejection_reason or "no_buying_event"
        opp.funnel_stage = "REJECT"
        opp.cto_15_minute_test = "NO"
        opp.cto_decision_reason = "No real buying event"
        return opp

    if currentness == Currentness.REJECT.value and not _still_active(opp):
        opp.final_verdict = FinalVerdict.REJECT.value
        opp.rejection_reason = "stale_over_90_days"
        opp.funnel_stage = "REJECT"
        opp.cto_15_minute_test = "NO"
        opp.cto_decision_reason = "Requirement is older than 90 days without evidence it is still active"
        return opp

    if is_partner:
        opp.final_verdict = FinalVerdict.NEEDS_RESEARCH.value
        opp.outreach_priority = "P3"
        opp.rejection_reason = "partner_not_direct_client"
        opp.cto_15_minute_test, opp.cto_decision_reason = cto_test(opp)
        return opp

    if not opp.failed_gates:
        opp.final_verdict = FinalVerdict.SALES_READY.value
        opp.funnel_stage = "SALES_READY"
        opp.outreach_priority = "P1" if opp.intent_level == IntentLevel.HOT.value else "P2"
        opp.cto_15_minute_test, opp.cto_decision_reason = cto_test(opp)
        if opp.cto_15_minute_test != "YES":
            opp.final_verdict = FinalVerdict.NEEDS_RESEARCH.value
            opp.funnel_stage = "CONTACT_VERIFIED"
            opp.failed_gates.append("cto_15_minute_test")
        return opp

    opp.final_verdict = FinalVerdict.NEEDS_RESEARCH.value
    opp.rejection_reason = "failed_gates: " + ", ".join(opp.failed_gates)
    opp.cto_15_minute_test, opp.cto_decision_reason = cto_test(opp)
    if opp.intent_level in {IntentLevel.HOT.value, IntentLevel.HIGH.value}:
        opp.outreach_priority = "P2"
    return opp


def cto_test(opp: CyberOpportunity) -> tuple[str, str]:
    """Would a CTO spend 15 minutes contacting this buyer from public evidence?

    Yes if someone publicly asked to buy security testing recently and we can
    reach them (email, LinkedIn, company site, or a named public-thread profile).
    """
    reasons: list[str] = []
    if not opp.security_problem:
        reasons.append("no real security problem")
    if opp.intent_level not in {IntentLevel.HOT.value, IntentLevel.HIGH.value, IntentLevel.MEDIUM.value}:
        reasons.append("buying intent not commercial")
    if not _identifiable(opp):
        reasons.append("buyer not identifiable")
    if opp.currentness not in {
        Currentness.HOT.value,
        Currentness.CURRENT.value,
        Currentness.AGING.value,
    } and not (opp.currentness == Currentness.STALE.value and _still_active(opp)):
        reasons.append("requirement not current enough")
    if not opp.service_match:
        reasons.append("no service match")
    if opp.contactability not in {"HIGH", "MEDIUM", "LOW"}:
        reasons.append("no public contact path")
    if not opp.requirement_evidence:
        reasons.append("evidence not reproducible")
    if opp.competitor:
        reasons.append("competitor")
    if not opp.safety_clear:
        reasons.append("safety not clear")
    if opp.opportunity_type == OpportunityType.SECURITY_PARTNER.value:
        reasons.append("partner not a direct buyer")
    if reasons:
        return "NO", "; ".join(reasons)
    return "YES", "Public buying request, still current, reachable, and Inowix can deliver the asked service"


def _identifiable(opp: CyberOpportunity) -> bool:
    named = bool(opp.buyer_name) and opp.identity_confidence in {"HIGH", "MEDIUM", "LOW"}
    company = bool(opp.company) and (bool(opp.company_url) or opp.company_verified)
    return named or company


def _still_active(opp: CyberOpportunity) -> bool:
    blob = f"{opp.title} {opp.body_snippet} {opp.why_now or ''}".lower()
    return any(
        t in blob
        for t in (
            "deadline",
            "this week",
            "urgent",
            "incident",
            "compromised",
            "going live",
            "currently looking",
            "still looking",
            "still need",
            "currently looking",
            "asap",
        )
    )


def _parse_dt(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def email_is_generic(email: str | None) -> bool:
    if not email or "@" not in email:
        return True
    local = email.split("@", 1)[0].lower()
    return local in {
        "info",
        "sales",
        "hello",
        "contact",
        "support",
        "help",
        "admin",
        "office",
        "team",
        "security",
        "privacy",
        "noreply",
        "no-reply",
    }


def classify_contactability(opp: CyberOpportunity) -> None:
    """Any real public path counts. Never inferred from a guessed address."""
    has_named_buyer = bool(opp.buyer_name)
    has_profile = bool(opp.buyer_profile_url)
    has_email = bool(opp.email) and "@" in (opp.email or "")
    named_inbox = has_email and not email_is_generic(opp.email)
    linkedin = opp.linkedin_status in {"VERIFIED", "PUBLIC"} and bool(opp.linkedin_url)
    form = any(e.get("claim") == "contact_form" for e in opp.contactability_evidence)
    company_site = bool(opp.company_url)

    if has_email and (named_inbox or has_named_buyer or company_site):
        opp.contactability = "HIGH" if named_inbox else "MEDIUM"
    elif has_named_buyer and (linkedin or has_profile or form or company_site):
        opp.contactability = "MEDIUM"
    elif linkedin or form or company_site or has_email:
        opp.contactability = "LOW"
    elif has_named_buyer and has_profile:
        opp.contactability = "MEDIUM"
    elif has_named_buyer:
        opp.contactability = "LOW"
    else:
        opp.contactability = "NONE"

    opp.contactability_evidence.append(
        evidence_item(
            "contactability",
            opp.contactability,
            "beacon",
            opp.source_url,
            "HIGH" if opp.contactability == "HIGH" else "MEDIUM",
            opp.observed_at,
        )
    )
