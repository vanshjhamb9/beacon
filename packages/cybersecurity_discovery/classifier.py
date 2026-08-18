"""Classify buying events, opportunity type, and Inowix service match."""

from __future__ import annotations

import hashlib

from packages.cybersecurity_discovery.competitors import is_competitor
from packages.cybersecurity_discovery.patterns import (
    COMPILED_BUYING,
    COMPILED_PARTNER,
    COMPILED_SERVICES,
    COUNTRY_HINTS,
    INDUSTRY_HINTS,
)
from packages.cybersecurity_discovery.rejects import reject_raw
from packages.cybersecurity_discovery.schema import (
    CyberOpportunity,
    FinalVerdict,
    OpportunityType,
    OutsourcingIntent,
    RawDiscovery,
    evidence_item,
)

BUYING_EVENT_LABELS = {
    "vulnerability_security_issue": "Security vulnerability / incident / pentest need",
    "external_security_team": "External cybersecurity team request",
    "compliance_vapt": "Compliance / VAPT requirement",
    "prelaunch_enterprise": "Pre-launch / enterprise security requirement",
    "security_contractor": "External security contractor / hire",
}


def match_buying_events(text: str) -> list[tuple[str, str]]:
    """Return list of (category, snippet) for matched buying patterns."""
    hits: list[tuple[str, str]] = []
    for category, patterns in COMPILED_BUYING.items():
        for pattern in patterns:
            found = pattern.search(text)
            if found:
                snippet = found.group(0)[:180]
                hits.append((category, snippet))
                break
    return hits


def is_partner_request(text: str) -> bool:
    return any(p.search(text) for p in COMPILED_PARTNER)


def match_service(text: str) -> tuple[str | None, str | None, str]:
    """Map stated requirement to one Inowix service. No evidence → no service."""
    matched: list[tuple[str, str]] = []
    for name, patterns in COMPILED_SERVICES:
        for pattern in patterns:
            found = pattern.search(text)
            if found:
                matched.append((name, found.group(0)))
                break
    if not matched:
        return None, None, "LOW"
    # Prefer the most specific non-generic service when both generic pentest and a flavor match.
    preferred = next(
        (m for m in matched if m[0] not in {"Penetration Testing", "Vulnerability Assessment", "Security Audit"}),
        matched[0],
    )
    name, snippet = preferred
    confidence = "HIGH" if len(matched) >= 1 and any(
        token in text.lower()
        for token in (
            "need",
            "looking for",
            "seeking",
            "require",
            "hiring",
            "customer requires",
            "recommend",
            "quote",
            "vendor",
            "hire",
        )
    ) else "MEDIUM"
    return name, f"Buyer stated '{snippet}'", confidence


def classify_opportunity_type(text: str, buying_hits: list[tuple[str, str]]) -> str:
    lowered = text.lower()
    if is_partner_request(text):
        return OpportunityType.SECURITY_PARTNER.value
    categories = {c for c, _ in buying_hits}
    if "compliance_vapt" in categories:
        return OpportunityType.SECURITY_COMPLIANCE_CLIENT.value
    if "vulnerability_security_issue" in categories and any(
        t in lowered for t in ("fix", "remediat", "compromised", "incident", "breached")
    ):
        return OpportunityType.SECURITY_REMEDIATION_CLIENT.value
    if "security_contractor" in categories:
        return OpportunityType.SECURITY_CONTRACTOR_CLIENT.value
    if "prelaunch_enterprise" in categories or "vulnerability_security_issue" in categories:
        return OpportunityType.SECURITY_TESTING_CLIENT.value
    if "external_security_team" in categories:
        return OpportunityType.DIRECT_SECURITY_CLIENT.value
    if buying_hits:
        return OpportunityType.DIRECT_SECURITY_CLIENT.value
    return OpportunityType.REJECT.value


def infer_country(text: str, hint: str | None = None) -> str | None:
    blob = f"{hint or ''} {text}".lower()
    for key, country in COUNTRY_HINTS.items():
        if key in blob:
            return country
    return None


def infer_industry(text: str) -> str | None:
    lowered = text.lower()
    for key, industry in INDUSTRY_HINTS.items():
        if key in lowered:
            return industry
    return None


def classify_raw(raw: RawDiscovery, observed_at: str) -> CyberOpportunity:
    """Turn a discovered post into a gated-but-not-yet-enriched opportunity."""
    opp_id = _opportunity_id(raw.source_url)
    reject_reason = reject_raw(raw)
    buying_hits = match_buying_events(raw.text)

    opp = CyberOpportunity(
        opportunity_id=opp_id,
        source_name=raw.source_name,
        source_url=raw.source_url,
        source_status="VERIFIED" if raw.source_url else "UNVERIFIED",
        published_at=raw.published_at,
        observed_at=observed_at,
        title=raw.title,
        body_snippet=raw.body[:400],
        company=raw.company_hint,
        company_url=raw.company_url_hint,
        country=infer_country(raw.text, raw.country_hint),
        industry=infer_industry(raw.text),
        buyer_name=raw.author if raw.author and raw.author.lower() not in {"unknown", "[deleted]", "none"} else None,
        buyer_profile_url=raw.author_profile_url,
        competitor=is_competitor(raw.company_hint or "") or (
            is_competitor(raw.text) and "we offer" in raw.text.lower()
        ),
        safety_clear=True,
        funnel_stage="DISCOVERED",
    )

    if reject_reason:
        opp.opportunity_type = OpportunityType.REJECT.value
        opp.final_verdict = "REJECT"
        opp.rejection_reason = reject_reason
        opp.funnel_stage = "REJECT"
        return opp

    if not buying_hits and not is_partner_request(raw.text):
        opp.opportunity_type = OpportunityType.REJECT.value
        opp.final_verdict = "REJECT"
        opp.rejection_reason = "no_buying_event"
        opp.funnel_stage = "REJECT"
        return opp

    opp.buying_event_verified = True
    opp.funnel_stage = "BUYING_EVENT"
    opp.final_verdict = FinalVerdict.NEEDS_RESEARCH.value
    opp.buying_event = BUYING_EVENT_LABELS.get(buying_hits[0][0], buying_hits[0][0] if buying_hits else "Partner request")
    opp.requirement_verified = True
    for category, snippet in buying_hits:
        opp.requirement_evidence.append(
            evidence_item(
                "requirement_verified",
                snippet,
                raw.source_name,
                raw.source_url,
                "HIGH",
                observed_at,
            )
        )

    opp.opportunity_type = classify_opportunity_type(raw.text, buying_hits)
    opp.problem = opp.buying_event
    opp.security_problem = buying_hits[0][1] if buying_hits else "Partner requested cybersecurity capacity"
    opp.security_problem_evidence = list(opp.requirement_evidence)
    opp.why_now = _why_now(raw.text, buying_hits)

    service, reason, conf = match_service(raw.text)
    opp.service_match = service
    opp.service_match_reason = reason
    opp.service_match_confidence = conf if service else "LOW"

    explicit = any(
        token in raw.text.lower()
        for token in (
            "looking for",
            "need a",
            "need an",
            "hiring",
            "seeking",
            "external",
            "vendor",
            "company to",
            "agency",
            "consultant",
            "quote",
            "rfp",
            "recommend",
            "anyone know",
            "suggestions for",
        )
    )
    if is_partner_request(raw.text) or explicit:
        opp.outsourcing_intent = OutsourcingIntent.EXPLICIT.value
        opp.outsourcing_evidence.append(
            evidence_item(
                "outsourcing_intent",
                "EXPLICIT",
                raw.source_name,
                raw.source_url,
                "HIGH",
                observed_at,
            )
        )
    elif buying_hits:
        opp.outsourcing_intent = OutsourcingIntent.HIGH.value
        opp.outsourcing_evidence.append(
            evidence_item(
                "outsourcing_intent",
                "HIGH",
                raw.source_name,
                raw.source_url,
                "MEDIUM",
                observed_at,
            )
        )
    if opp.buyer_name and opp.buyer_profile_url:
        opp.identity_confidence = "MEDIUM"
    elif opp.buyer_name:
        opp.identity_confidence = "LOW"
    if not opp.service_match and buying_hits:
        opp.service_match = "Penetration Testing"
        opp.service_match_reason = "Buying event implies paid security testing"
        opp.service_match_confidence = "MEDIUM"
    return opp


def _why_now(text: str, buying_hits: list[tuple[str, str]]) -> str:
    lowered = text.lower()
    if any(t in lowered for t in ("incident", "compromised", "breached", "hacked")):
        return "Active security incident or compromise reported"
    if any(t in lowered for t in ("before launch", "going live", "go-live", "production")):
        return "Pre-launch or production deadline"
    if any(t in lowered for t in ("soc 2", "iso 27001", "pci", "hipaa", "gdpr", "compliance", "customer requires")):
        return "Compliance or customer-required security testing"
    if buying_hits:
        return f"Public request: {buying_hits[0][1]}"
    return "Public cybersecurity partner request"


def _opportunity_id(url: str) -> str:
    digest = hashlib.sha256((url or "").encode("utf-8")).hexdigest()[:10]
    return f"CYBER-{digest}"
