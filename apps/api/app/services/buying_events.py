"""Buying Event Detection Service - Two-Lane Architecture.

CRITICAL RULES:
1. Keywords are ONLY discovery triggers - they NEVER qualify a lead
2. The original source must prove an actual business problem
3. Three lanes: COMAI, INOWIX, and CYBER with separate ICPs
4. 6-level classification system
5. QUALITY > QUANTITY
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.raw_event import RawEvent
from app.models.company_universe import CompanyUniverse
from app.models.buying_event import (
    BuyingEvent,
    BuyingEventClassification,
    BuyingEventDepartment,
    BuyingEventStatus,
    BusinessType,
    ContactType,
    FreshnessStatus,
)

logger = logging.getLogger(__name__)


# ── Freshness Classification ──

class FreshnessGate:
    CURRENT = "CURRENT"          # 0-7 days - eligible
    NEEDS_RESEARCH = "NEEDS_RESEARCH"  # 8-14 days - needs verification
    REJECT = "REJECT"            # >14 days - rejected


def classify_freshness(published_at: datetime, lane: str | None = None) -> tuple[str, int]:
    """Classify event freshness. Returns (status, days_old).

    CYBER keeps a 90-day window (HOT/CURRENT 0-30, research 31-90).
    Other lanes keep 0-7 CURRENT, 8-14 NEEDS_RESEARCH, >14 REJECT.
    """
    if not published_at:
        return FreshnessGate.REJECT, 999
    days_old = (datetime.now(UTC) - published_at).days
    if lane == "CYBER":
        if days_old <= 30:
            return FreshnessGate.CURRENT, days_old
        if days_old <= 90:
            return FreshnessGate.NEEDS_RESEARCH, days_old
        return FreshnessGate.REJECT, days_old
    if days_old <= 7:
        return FreshnessGate.CURRENT, days_old
    elif days_old <= 14:
        return FreshnessGate.NEEDS_RESEARCH, days_old
    else:
        return FreshnessGate.REJECT, days_old


# ── Contact Quality Classification ──

GENERIC_EMAIL_PREFIXES = ("info@", "sales@", "hello@", "contact@", "support@", "help@", "admin@", "office@", "team@")


class ContactTypeClassifier:
    DECISION_MAKER_DIRECT = "DECISION_MAKER_DIRECT"
    VERIFIED_WORK_EMAIL = "VERIFIED_WORK_EMAIL"
    LINKEDIN_DIRECT = "LINKEDIN_DIRECT"
    PLATFORM_DM = "PLATFORM_DM"
    GENERIC_COMPANY_EMAIL = "GENERIC_COMPANY_EMAIL"
    UNKNOWN = "UNKNOWN"


def classify_contact(contact_info: dict, evidence: list[dict]) -> tuple[str, bool]:
    """Classify contact quality. Returns (contact_type, is_high_contactability)."""
    email = contact_info.get("email", "")
    linkedin = contact_info.get("linkedin", "")

    # Check for decision maker indicators
    is_decision_maker = False
    if email:
        local_part = email.split("@")[0].lower()
        # Personal email patterns: firstname, first.last, firstlast
        if "." in local_part and not any(local_part.startswith(p) for p in ["info", "support", "help", "admin", "sales", "hello", "contact", "office", "team"]):
            is_decision_maker = True
        elif local_part in ("founder", "ceo", "cto", "director", "manager", "head", "lead"):
            is_decision_maker = True

    # Check for generic email
    is_generic = any(email.lower().startswith(p) for p in GENERIC_EMAIL_PREFIXES) if email else False

    # Determine contact type
    if is_decision_maker and email:
        contact_type = ContactTypeClassifier.DECISION_MAKER_DIRECT
        is_high = True
    elif email and not is_generic:
        contact_type = ContactTypeClassifier.VERIFIED_WORK_EMAIL
        is_high = False
    elif linkedin:
        contact_type = ContactTypeClassifier.LINKEDIN_DIRECT
        is_high = False
    elif is_generic:
        contact_type = ContactTypeClassifier.GENERIC_COMPANY_EMAIL
        is_high = False
    else:
        contact_type = ContactTypeClassifier.UNKNOWN
        is_high = False

    return contact_type, is_high


# ── False Positive Protection ──

FALSE_POSITIVE_PATTERNS = {
    "discussing_topic": [
        r"(?:discussing|talking\s+about|writing\s+about|blog\s+post\s+about|article\s+about)\s+(?:chatbot|automation|development|agency)",
        r"(?:what\s+is|how\s+to|guide\s+to|tutorial)\s+(?:chatbot|automation|development|agency)",
        r"(?:top|best|list\s+of)\s+(?:chatbot|automation|development)\s+(?:tools?|platforms?|services?|companies?)",
    ],
    "selling_service": [
        r"(?:we\s+(?:offer|provide|sell|deliver|build)\s+(?:chatbot|automation|development|agency))",
        r"(?:our\s+(?:chatbot|automation|development|agency)\s+(?:service|platform|tool|product|solution))",
        r"(?:looking\s+for\s+clients?|need\s+more\s+clients?|client\s+acquisition)",
    ],
    "third_party_mention": [
        r"(?:according\s+to|as\s+reported\s+by|source:|via)\s+(?:techcrunch|venturebeat|forbes|bloomberg|reuters)",
        r"(?:study|report|survey|research)\s+(?:shows?|finds?|reveals?|suggests?)",
    ],
    "job_seeker": [
        r"(?:looking|seeking|hunting)\s+for\s+(?:a\s+)?(?:job|work|position|role|employment)",
        r"(?:available|open)\s+(?:for\s+)?(?:hire|work|employment)",
        r"(?:hire\s+me|my\s+resume|my\s+portfolio)",
    ],
    "competitor_selling": [
        r"(?:we\s+are\s+a\s+(?:chatbot|saas|software|tech)\s+(?:company|startup|provider))",
        r"(?:our\s+(?:chatbot|saas|platform|tool|product))",
    ],
}


def check_false_positive(event: RawEvent) -> tuple[bool, str | None]:
    """Check if event is a false positive. Returns (is_false_positive, reason)."""
    text = f"{event.title} {event.content}".lower()

    for category, patterns in FALSE_POSITIVE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True, category

    return False, None


class BuyingEventDetector:
    """Routes to lane-specific detectors for COMAI, INOWIX, and CYBER.
    
    Three-Lane Architecture:
    - Lane A: COMAI (WhatsApp + AI Customer Support for Ecommerce)
    - Lane B: INOWIX (SaaS + Custom Software + AI + Mobile/Web Development)
    - Lane C: CYBER (high-intent cybersecurity buyers)
    """

    def __init__(self, session: AsyncSession, lane: str = None):
        self.session = session
        self.lane = lane
        
        # Import lane-specific detectors
        from app.services.lane_a_comai_detector import LaneA_COMAI_Detector
        from app.services.lane_b_inowix_detector import LaneB_INOWIX_Detector
        from app.services.lane_c_cyber_detector import LaneC_CYBER_Detector
        
        if lane == "COMAI":
            self.detector = LaneA_COMAI_Detector(session)
        elif lane == "INOWIX":
            self.detector = LaneB_INOWIX_Detector(session)
        elif lane == "CYBER":
            self.detector = LaneC_CYBER_Detector(session)
        else:
            self.detector = None

    async def detect_buying_events(
        self,
        department: str,
        batch_size: int = 2000,
    ) -> list[dict[str, Any]]:
        """Detect and verify buying events with two-lane architecture."""
        
        # Route to lane-specific detector
        if department == "COMAI":
            from app.services.lane_a_comai_detector import LaneA_COMAI_Detector
            detector = LaneA_COMAI_Detector(self.session)
        elif department == "CYBER":
            from app.services.lane_c_cyber_detector import LaneC_CYBER_Detector
            detector = LaneC_CYBER_Detector(self.session)
        else:
            from app.services.lane_b_inowix_detector import LaneB_INOWIX_Detector
            detector = LaneB_INOWIX_Detector(self.session)

        # CYBER: 90-day cutoff. Other lanes: 14-day hard cutoff.
        lookback_days = 90 if department == "CYBER" else 14
        cutoff_date = datetime.now(UTC) - timedelta(days=lookback_days)
        result = await self.session.execute(
            select(RawEvent).where(
                RawEvent.status == "RECEIVED",
                RawEvent.published_at >= cutoff_date,
            ).order_by(RawEvent.created_at.desc()).limit(batch_size)
        )
        raw_events = result.scalars().all()

        verified_events = []

        for event in raw_events:
            # STEP 1: Freshness gate
            freshness, days_old = classify_freshness(event.published_at, lane=department)

            # STEP 2: Platform-only filter
            if self._is_platform_only_event(event):
                continue

            # STEP 3: False positive check
            is_fp, fp_reason = check_false_positive(event)
            if is_fp:
                logger.debug(f"Rejected false positive: {fp_reason} for {event.url}")
                continue

            # STEP 4: Lane-specific detection
            detection_result = await detector.detect(event)
            if not detection_result:
                continue

            # STEP 5: Skip if rejected
            if detection_result.classification == BuyingEventClassification.REJECT:
                continue

            # STEP 6: Collect evidence (min 1 item required)
            if len(detection_result.evidence) < 1:
                continue

            # STEP 7: Extract company info
            company_name = detection_result.company_name
            company_domain = detection_result.company_domain

            if not company_name:
                continue

            # STEP 8: Classify contact quality
            contact_info = detection_result.contact_info
            contact_type, is_high_contactability = classify_contact(contact_info, detection_result.evidence)

            # STEP 9: Calculate confidence
            confidence = self._calculate_confidence(
                detection_result.evidence, detection_result.icp_score, freshness
            )

            # STEP 10: Build outreach preparation
            from app.services.outreach_preparation import OutreachPreparationEngine
            outreach_engine = OutreachPreparationEngine()
            
            # Create temporary buying event for outreach preparation
            temp_event = BuyingEvent(
                raw_event_id=event.id,
                department=BuyingEventDepartment(department),
                event_type=detection_result.classification,
                confidence=confidence,
                evidence=detection_result.evidence,
                company_name=company_name,
                company_domain=company_domain,
                contact_info=contact_info,
                problem=detection_result.problem,
                why_now=detection_result.why_now,
                solution_match=detection_result.solution_match,
                outreach_reason=detection_result.outreach_reason,
                classification=BuyingEventClassification(detection_result.classification),
                freshness=FreshnessStatus(freshness),
                days_old=days_old,
                contact_type=ContactType(contact_type),
                is_high_contactability=is_high_contactability,
                pain_signals=[{"type": s.signal_type, "description": s.description} for s in detection_result.pain_signals] if hasattr(detection_result, 'pain_signals') else [],
                buying_signals=[{"type": s.signal_type, "description": s.description} for s in detection_result.buying_signals] if hasattr(detection_result, 'buying_signals') else [],
                partner_signals=[{"type": s.signal_type, "services": s.services} for s in [detection_result.partner_signal]] if detection_result.partner_signal else [],
                icp_match_score=detection_result.icp_score,
            )
            
            outreach_preparation = outreach_engine.prepare_outreach(temp_event)

            # CTO 15-minute test
            cto_test = self._cto_test(detection_result, outreach_preparation)

            # Build the buying event
            event_data = {
                "id": str(uuid.uuid4()),
                "raw_event_id": str(event.id),
                "department": department,
                "event_type": detection_result.classification,
                "confidence": confidence,
                "evidence": detection_result.evidence,
                "company_name": company_name,
                "company_domain": company_domain,
                "contact_info": contact_info,
                "source": event.source,
                "status": "verified",
                "verified_at": datetime.now(UTC),
                # Freshness
                "freshness": freshness,
                "days_old": days_old,
                # Contact quality
                "contact_type": contact_type,
                "is_high_contactability": is_high_contactability,
                # Two-lane fields
                "classification": detection_result.classification,
                "business_type": self._determine_business_type(detection_result.classification),
                "problem": detection_result.problem,
                "why_now": detection_result.why_now,
                "solution_match": detection_result.solution_match,
                "outreach_reason": detection_result.outreach_reason,
                "pain_signals": [{"type": s.signal_type, "description": s.description} for s in detection_result.pain_signals] if hasattr(detection_result, 'pain_signals') else [],
                "buying_signals": [{"type": s.signal_type, "description": s.description} for s in detection_result.buying_signals] if hasattr(detection_result, 'buying_signals') else [],
                "partner_signals": [{"type": s.signal_type, "services": s.services} for s in [detection_result.partner_signal]] if detection_result.partner_signal else [],
                "icp_match_score": detection_result.icp_score,
                "outreach_preparation": self._serialize_outreach(outreach_preparation),
                "cto_test_result": cto_test,
            }
            verified_events.append(event_data)

        logger.info(
            f"Detected {len(verified_events)} {department} buying events "
            f"from {len(raw_events)} raw events"
        )

        await self._update_company_universe(verified_events)

        return verified_events

    def _is_platform_only_event(self, event: RawEvent) -> bool:
        """Reject events that are just blog articles on platforms."""
        metadata = event.event_metadata or {}
        platform_sources = {"devto", "medium"}
        if event.source not in platform_sources:
            return False

        # Reddit posts with domain/company_name are real businesses, not blog articles
        if event.source == "reddit":
            if metadata.get("domain") or metadata.get("company_name"):
                return False
            # Check if it has pain/buying signals — these are real people asking for help
            if metadata.get("lead_eligible") or metadata.get("pain_signals") or metadata.get("buying_signals"):
                return False

        has_company_website = False
        for field in ["official_website", "homepage", "official_domain"]:
            val = metadata.get(field)
            if val and isinstance(val, str):
                platform_domains = {"dev.to", "medium.com", "reddit.com", "github.com", "news.ycombinator.com"}
                if not any(pd in val for pd in platform_domains):
                    has_company_website = True
                    break

        if not has_company_website:
            wa = metadata.get("website_attribution", {})
            if isinstance(wa, dict) and wa.get("website"):
                platform_domains = {"dev.to", "medium.com", "reddit.com", "github.com", "news.ycombinator.com"}
                if not any(pd in wa["website"] for pd in platform_domains):
                    has_company_website = True

        if not has_company_website and event.url:
            platform_domains = {"dev.to", "medium.com", "reddit.com", "github.com"}
            if not any(pd in event.url for pd in platform_domains):
                has_company_website = True

        return not has_company_website

    def _calculate_confidence(
        self,
        evidence: list[dict],
        icp_score: float,
        freshness: str,
    ) -> float:
        """Calculate confidence score."""
        base = 0.5
        
        # Evidence factor
        evidence_factor = min(len(evidence) * 0.1, 0.25)
        
        # ICP score factor
        icp_factor = icp_score * 0.3
        
        # Freshness factor
        freshness_factor = 0.15 if freshness == "CURRENT" else 0.0
        
        return min(base + evidence_factor + icp_factor + freshness_factor, 1.0)

    def _cto_test(self, detection_result, outreach_preparation) -> bool:
        """CTO 15-minute test: Would Vansh spend 15 minutes contacting this person?"""
        
        # Must have specific problem
        if not detection_result.problem:
            return False
        
        # Must have contact
        if not outreach_preparation.contact or outreach_preparation.contact == "N/A":
            return False
        
        # Must have evidence-based outreach reason
        if not detection_result.outreach_reason:
            return False
        
        # Must have personalization points
        if not outreach_preparation.personalization_points:
            return False
        
        return True

    def _determine_business_type(self, classification: str) -> str | None:
        """Determine business type from classification."""
        if classification in ["ACTIVE_BUYING_EVENT", "VERIFIED_PAIN", "ICP_OPPORTUNITY"]:
            return BusinessType.DIRECT_CUSTOMER.value
        elif classification == "PARTNER_OPPORTUNITY":
            return BusinessType.PARTNER.value
        return None

    def _serialize_outreach(self, outreach_preparation) -> dict:
        """Serialize outreach preparation to dict."""
        from dataclasses import asdict
        return asdict(outreach_preparation)

    async def _update_company_universe(self, verified_events: list[dict]):
        """Update company universe with verified buying events."""
        for event_data in verified_events:
            domain = event_data.get("company_domain")
            if not domain:
                continue

            result = await self.session.execute(
                select(CompanyUniverse).where(CompanyUniverse.domain == domain)
            )
            companies = result.scalars().all()

            if companies:
                # Update existing (keep first if duplicates exist)
                companies[0].has_buying_event = True
                companies[0].buying_event_id = event_data["id"]
            else:
                new_company = CompanyUniverse(
                    domain=domain,
                    company_name=event_data.get("company_name"),
                    source="beacon",
                    has_buying_event=True,
                    buying_event_id=event_data["id"],
                )
                try:
                    self.session.add(new_company)
                    await self.session.flush()
                except Exception:
                    # Domain already exists (race condition), just update it
                    await self.session.rollback()
                    result2 = await self.session.execute(
                        select(CompanyUniverse).where(CompanyUniverse.domain == domain)
                    )
                    existing = result2.scalars().first()
                    if existing:
                        existing.has_buying_event = True
                        existing.buying_event_id = event_data["id"]
