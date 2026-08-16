"""Cybersecurity Signal Detector — Classifies opportunities by priority.

P0 = Active buying event (direct request for security testing)
P1 = Verified security pain (actual vulnerability, incident, compliance pressure)
P2 = High-potential outbound (growing company, likely to need security)
P3 = Generic ICP match (no buying signal)
"""

from __future__ import annotations

import re
from typing import Any

from cybersecurity_engine.models import (
    BuyingEvent,
    OpportunityPriority,
    OpportunityType,
    ServiceLane,
)


# ============================================================
# P0 — ACTIVE BUYING EVENT PATTERNS
# ============================================================

P0_DIRECT_REQUEST_PATTERNS = [
    # Penetration Testing
    r"(?:looking for|need|seeking|want|require)\s+(?:a\s+)?(?:penetration test|pentest|vapt)",
    r"(?:penetration test|pentest|vapt)\s+(?:company|vendor|provider|firm|team|service)",
    r"(?:need|looking for|seeking)\s+(?:a\s+)?(?:security test|security audit|security assessment)",
    r"(?:security test|security audit|security assessment)\s+(?:company|vendor|provider|firm|service)",
    # Vulnerability Assessment
    r"(?:need|looking for|seeking)\s+(?:a\s+)?(?:vulnerability assessment|vulnerability scan)",
    r"(?:vulnerability assessment|vulnerability scan)\s+(?:company|vendor|provider|firm|service)",
    # Web Application Security
    r"(?:need|looking for|seeking)\s+(?:a\s+)?(?:web application|web app)\s+(?:penetration test|security test|pentest)",
    r"(?:web application|web app)\s+(?:penetration test|security test|pentest)\s+(?:company|vendor|provider|firm|service)",
    # API Security
    r"(?:need|looking for|seeking)\s+(?:a\s+)?(?:api security test|api penetration test|api security audit)",
    r"(?:api security test|api penetration test|api security audit)\s+(?:company|vendor|provider|firm|service)",
    # Mobile Application Security
    r"(?:need|looking for|seeking)\s+(?:a\s+)?(?:mobile app|mobile application)\s+(?:security test|penetration test|pentest)",
    r"(?:mobile app|mobile application)\s+(?:security test|penetration test|pentest)\s+(?:company|vendor|provider|firm|service)",
    # Cloud Security
    r"(?:need|looking for|seeking)\s+(?:a\s+)?(?:cloud security assessment|cloud security audit|cloud pentest)",
    r"(?:cloud security assessment|cloud security audit|cloud pentest)\s+(?:company|vendor|provider|firm|service)",
    # Network Security
    r"(?:need|looking for|seeking)\s+(?:a\s+)?(?:network penetration test|network security test|network security audit)",
    r"(?:network penetration test|network security test|network security audit)\s+(?:company|vendor|provider|firm|service)",
    # Compliance-Driven
    r"(?:need|looking for)\s+(?:security testing|penetration testing|vapt)\s+for\s+(?:soc\s*2|iso\s*27001|pci\s*dss|hipaa|gdpr)",
    r"(?:soc\s*2|iso\s*27001|pci\s*dss|hipaa|gdpr)\s+(?:compliance|certification|audit)\s+(?:requires|requires?|needs?)\s+(?:penetration test|security test|vapt)",
    # Enterprise Requirements
    r"(?:enterprise|big\s+company|client|customer)\s+(?:requires?|demands?|needs?)\s+(?:penetration test|security test|security audit|vapt)",
    r"(?:before|prior\s+to)\s+(?:launch|go[- ]live|release|enterprise\s+rollout)\s+(?:need|requires?|must\s+have)\s+(?:penetration test|security test|vapt)",
    # Remediation
    r"(?:need|looking for|seeking)\s+(?:remediation|retesting|re-test|fix\s+verification)",
    r"(?:remediation|retesting|re-test)\s+(?:after|following)\s+(?:vulnerability|pentest|security\s+assessment)",
    # Ethical Hackers
    r"(?:looking for|need|seeking)\s+(?:ethical\s+hacker|security\s+researcher|bug\s+bounty|security\s+team)",
]

P0_PROCUREMENT_PATTERNS = [
    r"(?:rfp|request\s+for\s+proposal)\s+(?:for\s+)?(?:security|penetration|vapt|vulnerability)",
    r"(?:security|penetration|vapt|vulnerability)\s+(?:rfp|request\s+for\s+proposal|tender|procurement)",
    r"(?:procurement|purchasing)\s+(?:security\s+testing|penetration\s+testing|vapt|security\s+audit)",
    r"(?:tender|bid|proposal)\s+(?:for\s+)?(?:security\s+assessment|penetration\s+test|vapt)",
]


# ============================================================
# P1 — VERIFIED SECURITY PAIN PATTERNS
# ============================================================

P1_VULNERABILITY_PATTERNS = [
    # Direct vulnerability mentions
    r"(?:discovered|found|identified|detected)\s+(?:a\s+)?(?:vulnerability|vuln|security\s+flaw|security\s+issue)",
    r"(?:critical|high|severe|major)\s+(?:vulnerability|vuln|security\s+flaw|security\s+issue)",
    r"(?:sql\s+injection|xss|cross[- ]site\s+scripting|csrf|ssrf|idor|bola|broken\s+access)",
    r"(?:authentication\s+bug|authorization\s+bug|privilege\s+escalation)",
    r"(?:data\s+exposure|data\s+leak|data\s+breach|security\s+incident)",
    r"(?:unpatched|outdated|end[- ]of[- ]life)\s+(?:software|component|dependency|library)",
    r"(?:penetration\s+test|pentest|security\s+audit)\s+(?:revealed|found|showed|uncovered|missed)",
    r"(?:failed|failing|did\s+not\s+pass)\s+(?:security\s+review|compliance\s+review|audit|assessment)",
    r"(?:previous|last|prior)\s+(?:pentest|security\s+test|audit)\s+(?:was|is|has\s+been)\s+(?:inadequate|incomplete|missed|incomplete|insufficient)",
]

P1_COMPLIANCE_PRESSURE_PATTERNS = [
    r"(?:enterprise|big|major)\s+(?:customer|client|partner)\s+(?:requires?|demands?|needs?|mandates?)\s+(?:security|penetration|pentest|vapt|audit)",
    r"(?:investor|board|investor\s+relations)\s+(?:requires?|demands?|needs?)\s+(?:security|penetration|audit)",
    r"(?:customer|client|prospect)\s+(?:security\s+questionnaire|vendor\s+security\s+assessment|due\s+diligence)",
    r"(?:soc\s*2|iso\s*27001|pci\s*dss|hipaa|gdpr)\s+(?:deadline|certification|audit|compliance)\s+(?:approaching|upcoming|date|deadline)",
    r"(?:compliance|regulatory)\s+(?:deadline|requirement|obligation)\s+(?:approaching|upcoming|missed|failed)",
    r"(?:failed|failing)\s+(?:compliance|regulatory)\s+(?:audit|review|assessment|certification)",
]

P1_OPERATIONAL_PRESSURE_PATTERNS = [
    r"(?:security\s+team|infosec|security\s+department)\s+(?:overwhelmed|understaffed|overloaded|short[- ]staffed|too\s+busy)",
    r"(?:need|require|must)\s+(?:external|outside|third[- ]party)\s+(?:security|penetration|vulnerability)\s+(?:help|testing|assessment|support)",
    r"(?:need|require)\s+(?:independent|third[- ]party)\s+(?:validation|verification|assessment|review)",
    r"(?:product|platform|feature|release|launch|deployment)\s+(?:requires?|needs?|must\s+have)\s+(?:security\s+assessment|penetration\s+test|security\s+audit|vapt)",
    r"(?:need|require)\s+(?:remediation|fix|patch|remediate)\s+(?:support|help|guidance|assistance)",
    r"(?:need|require)\s+(?:retesting|re[- ]test|regression\s+test)\s+(?:after|post|following)\s+(?:fix|patch|remediation|update)",
]


# ============================================================
# P2 — HIGH-POTENTIAL OUTBOUND PATTERNS
# ============================================================

P2_SIGNAL_PATTERNS = [
    r"(?:series\s+[a-d]|seed|pre[- ]seed|ipo)\s+(?:funding|round|raised)",
    r"(?:rapid|fast|hyper)\s+(?:growth|scaling|expanding)",
    r"(?:new|launching|launched|launch)\s+(?:product|feature|platform|api|mobile\s+app|service)",
    r"(?:enterprise|corporate)\s+(?:customer|client|expansion|sales|deals?)",
    r"(?:hiring|looking\s+for|seeking)\s+(?:security\s+engineer|security\s+analyst|appsec|devsecops|ciso|security\s+architect)",
    r"(?:preparing|preparing\s+for|getting\s+ready|working\s+toward)\s+(?:soc\s*2|iso\s*27001|pci\s*dss|hipaa|gdpr)",
    r"(?:compliance|certification)\s+(?:journey|process|program|initiative)",
    r"(?:sensitive|private|personal|pii|phi)\s+(?:data|information|customer\s+data)",
    r"(?:b2b|enterprise)\s+(?:saas|software|platform|product)",
]


# ============================================================
# SERVICE MATCHING
# ============================================================

SERVICE_KEYWORDS = {
    "penetration_testing": [
        "penetration test", "pentest", "pen test", "pen-test",
    ],
    "vulnerability_assessment": [
        "vulnerability assessment", "vulnerability scan", "vuln assessment",
    ],
    "web_app_security": [
        "web application security", "web app security", "web app pentest",
        "web application penetration", "web security",
    ],
    "api_security": [
        "api security", "api pentest", "api penetration test",
        "api vulnerability", "rest api security", "graphql security",
    ],
    "mobile_security": [
        "mobile application security", "mobile app security", "mobile pentest",
        "ios security", "android security",
    ],
    "cloud_security": [
        "cloud security", "cloud assessment", "cloud pentest",
        "aws security", "azure security", "gcp security",
    ],
    "network_security": [
        "network security", "network pentest", "network penetration",
        "infrastructure security", "perimeter security",
    ],
    "security_audit": [
        "security audit", "security review", "security assessment",
    ],
    "compliance": [
        "soc 2", "iso 27001", "pci dss", "hipaa", "gdpr", "compliance",
    ],
    "remediation": [
        "remediation", "remediate", "fix vulnerabilities", "retesting", "retest",
    ],
}


def detect_service_needs(text: str) -> list[str]:
    """Detect which cybersecurity services are needed from text."""
    text_lower = text.lower()
    services = []
    for service, keywords in SERVICE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            services.append(service)
    return services


def calculate_service_match(services_needed: list[str]) -> str:
    """Calculate overall service match level."""
    if len(services_needed) >= 3:
        return "HIGH"
    elif len(services_needed) >= 1:
        return "HIGH"
    return "LOW"


# ============================================================
# MAIN SIGNAL DETECTOR
# ============================================================

class CybersecuritySignalDetector:
    """Detects and classifies cybersecurity buying signals."""

    def detect_priority(
        self,
        text: str,
        source_tier: int = 3,
        company_context: dict[str, Any] | None = None,
    ) -> tuple[OpportunityPriority, BuyingEvent]:
        """Classify a signal into priority and create a buying event.

        Args:
            text: The text content to analyze (post, article, etc.)
            source_tier: Source tier (1=direct, 2=strong, 3=discovery)
            company_context: Optional company context for better classification

        Returns:
            Tuple of (priority, buying_event)
        """
        text_lower = text.lower()

        # P0 — Active Buying Event
        p0_score = 0
        p0_matches = []
        for pattern in P0_DIRECT_REQUEST_PATTERNS + P0_PROCUREMENT_PATTERNS:
            if re.search(pattern, text_lower):
                p0_score += 1
                p0_matches.append(pattern)

        if p0_score >= 1 and source_tier <= 2:
            services = detect_service_needs(text)
            return (
                OpportunityPriority.P0,
                BuyingEvent(
                    event_type="active_buying",
                    description=self._extract_buying_description(text, p0_matches),
                    service_match=calculate_service_match(services),
                    service_lane=ServiceLane.CYBERSECURITY,
                    services_needed=services,
                    why_now=self._extract_why_now(text),
                    urgency="urgent" if source_tier == 1 else "normal",
                ),
            )

        # P0 from Tier 3 sources with strong signals (2+ pattern matches)
        if p0_score >= 2 and source_tier == 3:
            services = detect_service_needs(text)
            return (
                OpportunityPriority.P0,
                BuyingEvent(
                    event_type="active_buying",
                    description=self._extract_buying_description(text, p0_matches),
                    service_match=calculate_service_match(services),
                    service_lane=ServiceLane.CYBERSECURITY,
                    services_needed=services,
                    why_now=self._extract_why_now(text),
                    urgency="normal",
                ),
            )

        # P1 — Verified Security Pain
        p1_score = 0
        p1_matches = []
        for pattern in (
            P1_VULNERABILITY_PATTERNS
            + P1_COMPLIANCE_PRESSURE_PATTERNS
            + P1_OPERATIONAL_PRESSURE_PATTERNS
        ):
            if re.search(pattern, text_lower):
                p1_score += 1
                p1_matches.append(pattern)

        if p1_score >= 1 and source_tier <= 2:
            services = detect_service_needs(text)
            return (
                OpportunityPriority.P1,
                BuyingEvent(
                    event_type="verified_pain",
                    description=self._extract_pain_description(text, p1_matches),
                    service_match=calculate_service_match(services),
                    service_lane=ServiceLane.CYBERSECURITY,
                    services_needed=services,
                    why_now=self._extract_why_now(text),
                    urgency="normal",
                ),
            )

        # P1 from Tier 3 sources with strong signals (2+ pattern matches)
        if p1_score >= 2 and source_tier == 3:
            services = detect_service_needs(text)
            return (
                OpportunityPriority.P1,
                BuyingEvent(
                    event_type="verified_pain",
                    description=self._extract_pain_description(text, p1_matches),
                    service_match=calculate_service_match(services),
                    service_lane=ServiceLane.CYBERSECURITY,
                    services_needed=services,
                    why_now=self._extract_why_now(text),
                    urgency="normal",
                ),
            )

        # P2 — High-Potential Outbound
        p2_score = 0
        for pattern in P2_SIGNAL_PATTERNS:
            if re.search(pattern, text_lower):
                p2_score += 1

        if p2_score >= 1:  # Reduced from 2 to 1 for better coverage
            services = detect_service_needs(text)
            return (
                OpportunityPriority.P2,
                BuyingEvent(
                    event_type="outbound_signal",
                    description=self._extract_outbound_description(text),
                    service_match="MEDIUM" if services else "LOW",
                    service_lane=ServiceLane.CYBERSECURITY,
                    services_needed=services,
                    why_now="Growing company with likely security needs",
                    urgency="low",
                ),
            )

        # P3 — Generic ICP (no buying signal)
        return (
            OpportunityPriority.P3,
            BuyingEvent(
                event_type="no_signal",
                description="No cybersecurity buying signal detected",
                service_match="LOW",
                service_lane=ServiceLane.CYBERSECURITY,
            ),
        )

    def _extract_buying_description(self, text: str, patterns: list[str]) -> str:
        """Extract a clean description of the buying event."""
        # Try to find the most relevant sentence
        sentences = re.split(r'[.!?\n]', text)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(
                kw in sentence_lower
                for kw in ["penetration", "pentest", "vapt", "security test",
                           "vulnerability", "audit", "rfp", "tender"]
            ):
                return sentence.strip()[:200]
        return text[:200]

    def _extract_pain_description(self, text: str, patterns: list[str]) -> str:
        """Extract a clean description of the security pain."""
        sentences = re.split(r'[.!?\n]', text)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(
                kw in sentence_lower
                for kw in ["vulnerability", "breach", "incident", "failed",
                           "compliance", "deadline", "overwhelmed", "remediation"]
            ):
                return sentence.strip()[:200]
        return text[:200]

    def _extract_outbound_description(self, text: str) -> str:
        """Extract a clean description of the outbound signal."""
        sentences = re.split(r'[.!?\n]', text)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(
                kw in sentence_lower
                for kw in ["funding", "growth", "launch", "hiring",
                           "enterprise", "compliance", "soc 2", "iso"]
            ):
                return sentence.strip()[:200]
        return text[:200]

    def _extract_why_now(self, text: str) -> str:
        """Extract why now urgency from text."""
        text_lower = text.lower()
        urgency_signals = [
            (r"(?:deadline|due\s+date|must\s+be\s+done|time[\s-]sensitive|urgent|asap)", "Time-sensitive requirement"),
            (r"(?:before|prior\s+to|ahead\s+of)\s+(?:launch|go[- ]live|release|meeting|audit)", "Pre-launch/pre-audit requirement"),
            (r"(?:just|recently|yesterday|today|this\s+week)\s+(?:discovered|found|learned)", "Recent discovery"),
            (r"(?:failed|failing)\s+(?:audit|review|compliance|assessment)", "Failed previous assessment"),
            (r"(?:series\s+[a-d]|funding|raised)", "Recent funding enables security investment"),
        ]
        for pattern, reason in urgency_signals:
            if re.search(pattern, text_lower):
                return reason
        return "Current security requirement"
