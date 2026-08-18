"""Lane C: CYBER Detector — high-intent cybersecurity buyers.

Finds businesses currently requesting pentest/VAPT/audit/remediation help.
Industry, missing badges, and inferred risk are NOT buying events.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.raw_event import RawEvent
from packages.cybersecurity_discovery.classifier import (
    classify_opportunity_type,
    match_buying_events,
    match_service,
)
from packages.cybersecurity_discovery.competitors import is_competitor
from packages.cybersecurity_discovery.rejects import first_reject_reason

logger = logging.getLogger(__name__)


@dataclass
class BuyingSignal:
    signal_type: str
    description: str
    evidence: list[str]
    confidence: float


@dataclass
class SupportingSignal:
    signal_type: str
    description: str
    evidence: list[str]
    confidence: float


@dataclass
class PartnerSignal:
    signal_type: str
    agency_name: str
    services: list[str]
    client_icp: list[str]
    evidence: list[str]
    confidence: float


@dataclass
class DetectionResult:
    classification: str
    icp_score: float
    buying_signals: list[BuyingSignal]
    supporting_signals: list[SupportingSignal]
    partner_signal: PartnerSignal | None
    company_name: str | None
    company_domain: str | None
    contact_info: dict[str, Any]
    evidence: list[dict[str, Any]]
    problem: str | None
    why_now: str | None
    solution_match: str | None
    outreach_reason: str | None
    opportunity_type: str = "REJECT"


class LaneC_CYBER_Detector:
    """Cybersecurity-specific detection. Quality over quantity."""

    ICP_KEYWORDS = {
        "pentest",
        "penetration test",
        "vapt",
        "security audit",
        "vulnerability assessment",
        "cybersecurity",
        "appsec",
        "soc 2",
        "iso 27001",
        "security consultant",
        "security testing",
    }

    def __init__(self, session: AsyncSession):
        self.session = session

    async def detect(self, event: RawEvent) -> DetectionResult | None:
        text = f"{event.title} {event.content}"
        reject = first_reject_reason(text)
        icp_score = self._evaluate_icp(text)
        buying_hits = match_buying_events(text)
        buying_signals = [
            BuyingSignal(
                signal_type=category,
                description=snippet,
                evidence=[snippet],
                confidence=0.85,
            )
            for category, snippet in buying_hits
        ]
        partner_signal = None
        opp_type = classify_opportunity_type(text, buying_hits)
        if opp_type == "SECURITY_PARTNER":
            partner_signal = PartnerSignal(
                signal_type="security_partner",
                agency_name=self._extract_company_name(event) or "Unknown Agency",
                services=["cybersecurity", "vapt"],
                client_icp=["saas", "agencies"],
                evidence=["Partner request matched"],
                confidence=0.8,
            )

        classification = self._classify(reject, icp_score, buying_signals, partner_signal, text)
        if classification == "REJECT" and not buying_signals:
            return None

        service, reason, _conf = match_service(text)
        company_name = self._extract_company_name(event)
        if is_competitor(company_name or "") or (is_competitor(text) and "we offer" in text.lower()):
            classification = "REJECT"

        problem = buying_signals[0].description if buying_signals else None
        why_now = "Public cybersecurity buying request" if buying_signals else None
        solution_match = service
        outreach_reason = None
        if classification in {"ACTIVE_BUYING_EVENT", "VERIFIED_PAIN"} and company_name:
            outreach_reason = (
                f"{company_name} published a cybersecurity buying event. "
                f"Matched service: {service or 'undetermined'}."
            )
        evidence = [{"type": "content", "source": event.source, "value": (event.content or "")[:500]}]
        for signal in buying_signals:
            evidence.append(
                {
                    "type": "buying_signal",
                    "signal": signal.signal_type,
                    "description": signal.description,
                    "confidence": signal.confidence,
                    "cyber_opportunity_type": opp_type,
                }
            )
        if reason:
            evidence.append({"type": "service_match", "value": service, "reason": reason})
        if reject:
            evidence.append({"type": "reject", "reason": reject})

        return DetectionResult(
            classification=classification,
            icp_score=icp_score,
            buying_signals=buying_signals,
            supporting_signals=[],
            partner_signal=partner_signal,
            company_name=company_name,
            company_domain=self._extract_domain(event),
            contact_info=self._extract_contact_info(event),
            evidence=evidence,
            problem=problem,
            why_now=why_now,
            solution_match=solution_match,
            outreach_reason=outreach_reason,
            opportunity_type=opp_type,
        )

    def _evaluate_icp(self, text: str) -> float:
        lowered = text.lower()
        score = 0.0
        if any(k in lowered for k in self.ICP_KEYWORDS):
            score += 0.4
        if any(t in lowered for t in ("saas", "startup", "founder", "cto", "app", "platform", "api")):
            score += 0.2
        if any(t in lowered for t in ("need", "looking for", "seeking", "require", "hiring")):
            score += 0.3
        return min(score, 1.0)

    def _classify(
        self,
        reject: str | None,
        icp_score: float,
        buying_signals: list[BuyingSignal],
        partner_signal: PartnerSignal | None,
        text: str,
    ) -> str:
        from app.models.buying_event import BuyingEventClassification

        if reject and not buying_signals:
            return BuyingEventClassification.REJECT
        if partner_signal and not buying_signals:
            return BuyingEventClassification.PARTNER_OPPORTUNITY
        if partner_signal and "partner" in text.lower():
            return BuyingEventClassification.PARTNER_OPPORTUNITY
        if buying_signals:
            return BuyingEventClassification.ACTIVE_BUYING_EVENT
        if icp_score >= 0.5:
            return BuyingEventClassification.NURTURE
        return BuyingEventClassification.REJECT

    def _extract_company_name(self, event: RawEvent) -> str | None:
        metadata = event.event_metadata or {}
        for field_name in ("company_name", "organization", "org", "company", "brand"):
            if metadata.get(field_name):
                return str(metadata[field_name])
        title = event.title or ""
        if " - " in title:
            return title.split(" - ")[0].strip()
        return None

    def _extract_domain(self, event: RawEvent) -> str | None:
        metadata = event.event_metadata or {}
        for field_name in ("domain", "website", "url", "homepage", "official_website"):
            if metadata.get(field_name):
                domain = str(metadata[field_name])
                domain = domain.replace("https://", "").replace("http://", "")
                domain = domain.replace("www.", "").rstrip("/")
                return domain
        return None

    def _extract_contact_info(self, event: RawEvent) -> dict[str, Any]:
        metadata = event.event_metadata or {}
        return {
            "author": metadata.get("author") or metadata.get("username"),
            "email": metadata.get("email"),
            "linkedin": metadata.get("linkedin"),
        }
