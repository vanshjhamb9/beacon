"""Lane A: COMAI Detector - WhatsApp + AI Customer Support for Ecommerce.

COMAI ICP IS BROAD:
- New ecommerce startups
- Small businesses
- Growing businesses
- Growing D2C brands
- Mid-size ecommerce businesses
- Shopify stores
- WooCommerce stores
- Ecommerce brands with meaningful customer interaction
- Businesses facing operational/support/customer-response problems

COMAI does NOT require the company to publicly say "I need a chatbot."
COMAI can be sold through OUTREACH PAIN DETECTION.

Classification:
A. ACTIVE_BUYING_EVENT - Explicit commercial requirement exists
B. VERIFIED_PAIN - Verified business problem (no explicit request)
C. ICP_OPPORTUNITY - Fits ICP but no verified pain
D. PARTNER_OPPORTUNITY - Agency with verified partnership potential
E. NURTURE - Interesting but insufficient evidence
F. REJECT - Wrong ICP, competitor, irrelevant
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.raw_event import RawEvent

logger = logging.getLogger(__name__)


@dataclass
class PainSignal:
    """Verified business pain (not buying intent)."""
    signal_type: str
    description: str
    evidence: list[str]
    confidence: float


@dataclass
class BuyingSignal:
    """Explicit buying intent (rare for COMAI)."""
    signal_type: str
    description: str
    evidence: list[str]
    confidence: float


@dataclass
class PartnerSignal:
    """Agency/partner opportunity."""
    signal_type: str
    agency_name: str
    services: list[str]
    client_icp: list[str]
    evidence: list[str]
    confidence: float


@dataclass
class DetectionResult:
    """Result of COMAI detection."""
    classification: str
    icp_score: float
    pain_signals: list[PainSignal]
    buying_signals: list[BuyingSignal]
    partner_signal: PartnerSignal | None
    company_name: str | None
    company_domain: str | None
    contact_info: dict[str, Any]
    evidence: list[dict[str, Any]]
    problem: str | None
    why_now: str | None
    solution_match: str | None
    outreach_reason: str | None


class LaneA_COMAI_Detector:
    """COMAI-specific detection with broad ecommerce ICP.
    
    Key distinction: "No chatbot detected" = PAIN/OUTBOUND OPPORTUNITY, NOT ACTIVE BUYING EVENT.
    "Growing ecommerce business" = ICP/GROWTH SIGNAL, NOT BUYING EVENT.
    """
    
    # ICP Definition - Broad ecommerce
    ICP_DOMAINS = {
        "shopify", "woocommerce", "bigcommerce", "squarespace",
        "etsy", "amazon", "ecommerce", "d2c", "dtc",
    }
    
    ICP_KEYWORDS = {
        "ecommerce", "e-commerce", "shopify", "woocommerce", "d2c", "dtc",
        "online store", "ecommerce brand", "ecommerce business", "ecommerce startup",
        "online shop", "retail", "direct to consumer", "consumer brand",
        "product brand", "subscription box", "subscription commerce",
    }
    
    # Pain Signals - NOT buying events, but verified business problems
    PAIN_PATTERNS = {
        "high_support_volume": [
            r"(?:too\s+many|overwhelmed|swamped|drowning|flooded)\s+(?:messages|dms|tickets|queries|questions|requests|inquiries)",
            r"(?:can'?t|cannot|unable\s+to)\s+(?:keep\s+up|handle|manage|respond\s+to)\s+(?:with\s+)?(?:all\s+)?(?:the\s+)?(?:messages|dms|tickets|customers|queries)",
            r"(?:response\s+time|reply\s+time)\s+(?:is\s+)?(?:too\s+slow|hours|days|getting\s+worse)",
        ],
        "slow_response_time": [
            r"(?:slow|delayed|late|hours|days)\s+(?:response|reply|replying|responding)",
            r"(?:customers?|clients?)\s+(?:waiting|waiting\s+for|still\s+waiting)",
            r"(?:missed|losing)\s+(?:customers?|leads?|sales?)\s+(?:because|due\s+to|from)\s+(?:slow|no|poor)\s+(?:response|support)",
        ],
        "no_automation": [
            r"(?:no|without|lack\s+of)\s+(?:automation|automated|chatbot|ai|bot|auto.?reply)",
            r"(?:manual|hand.?coded|human)\s+(?:customer\s+support|support|replies|responses)",
            r"(?:doing\s+everything|all\s+manual|manually\s+handling)",
        ],
        "customer_engagement_problems": [
            r"(?:customers?|clients?)\s+(?:leaving|churning|going|lost)\s+(?:because|due\s+to|from)",
            r"(?:poor|bad|terrible)\s+(?:customer\s+experience|cx|support\s+experience)",
            r"(?:customers?|clients?)\s+(?:complaining|frustrated|unhappy|dissatisfied)",
        ],
        "scaling_support_team": [
            r"(?:hiring|need\s+to\s+hire|looking\s+to\s+hire)\s+(?:support|customer\s+service|customer\s+success)",
            r"(?:support\s+team|customer\s+service\s+team)\s+(?:is\s+)?(?:growing|scaling|expanding|overwhelmed)",
            r"(?:can'?t|cannot|unable)\s+to\s+(?:hire|find|recruit)\s+(?:fast\s+enough|support\s+staff)",
        ],
        "whatsapp_heavy_business": [
            r"(?:whatsapp|wa)\s+(?:is\s+)?(?:our|the|primary|main|biggest)\s+(?:channel|way|method|tool)\s+(?:for|of|to)\s+(?:communication|support|customer)",
            r"(?:most|all|majority)\s+of\s+(?:our|the)\s+(?:customers?|clients?|conversations?|messages?)\s+(?:are\s+on|via|through)\s+whatsapp",
            r"(?:receiving|getting|handling)\s+(?:hundreds?|thousands?|dozens?)\s+of\s+(?:whatsapp|wa)\s+(?:messages?|dm|conversations?|chats?)",
        ],
        "high_order_volume": [
            r"(?:processing|handling|fulfilling|managing)\s+(?:hundreds?|thousands?|dozens?)\s+of\s+(?:orders?|transactions?|shipments?)",
            r"(?:high|large|massive|significant)\s+(?:order|transaction|sales)\s+volume",
            r"(?:growing|increasing|scaling)\s+(?:order|transaction|sales)\s+volume",
        ],
        "ecommerce_pain": [
            r"(?:ecommerce|e-commerce|d2c|shopify|woocommerce|magento|store|shop)\s+(?:brand|business|company|startup)",
            r"(?:growing|scaling|expanding)\s+(?:ecommerce|d2c|online\s+store|shop|brand)",
            r"(?:low|poor|bad)\s+(?:conversion|repeat\s+purchases?|customer\s+retention|retention\s+rate)",
        ],
    }
    
    # Buying Signals - Explicit intent (rare for COMAI)
    BUYING_PATTERNS = {
        "looking_for_chatbot": [
            r"(?:need|looking|want|searching|require)\s+(?:a\s+)?(?:chatbot|ai\s+chatbot|customer\s+support\s+bot|support\s+bot)",
            r"(?:looking|searching|finding)\s+(?:for\s+)?(?:chatbot|ai\s+chatbot|customer\s+support\s+bot)",
            r"(?:want|need)\s+(?:to\s+)?(?:add|implement|deploy|build)\s+(?:a\s+)?(?:chatbot|ai\s+bot)",
        ],
        "need_whatsapp_automation": [
            r"(?:need|looking|want|searching|require)\s+(?:a\s+)?(?:whatsapp|wa)\s+(?:bot|automation|api|integration|chatbot)",
            r"whatsapp\s+(?:business\s+)?(?:api|automation|bot|chatbot)\s+(?:for|to|need|help)",
            r"(?:automate|automating)\s+(?:whatsapp|customer\s+conversations|dm|messages)",
        ],
        "searching_for_ai_support": [
            r"(?:looking|searching|finding)\s+(?:for\s+)?(?:ai|artificial\s+intelligence)\s+(?:support|customer\s+service|customer\s+support)",
            r"(?:need|want)\s+(?:ai|artificial\s+intelligence)\s+(?:powered|based|driven)\s+(?:support|customer\s+service)",
        ],
    }
    
    # Partner Signals - Agency/partner opportunity
    PARTNER_PATTERNS = {
        "agency_serves_ecommerce": [
            r"(?:we\s+)?(?:are|'?re)\s+(?:a\s+)?(?:digital\s+marketing|marketing|ecommerce|shopify|performance)\s+agency",
            r"(?:our\s+)?(?:clients?|customers?)\s+(?:are|is|include|are\s+mainly)\s+(?:ecommerce|d2c|shopify|brands?|stores?)",
            r"(?:we\s+)?(?:help|serve|work\s+with)\s+(?:ecommerce|d2c|shopify|brands?|stores?|retail)",
        ],
        "builds_shopify_stores": [
            r"(?:we\s+)?(?:build|create|develop|design)\s+(?:shopify|ecommerce|online\s+store|store)s?",
            r"(?:shopify|ecommerce)\s+(?:development|design|building|agency|expert)",
        ],
        "manages_ads_for_ecommerce": [
            r"(?:we\s+)?(?:manage|run|handle)\s+(?:meta|facebook|google|tiktok)\s+(?:ads?|advertising|campaigns?)\s+(?:for|with)\s+(?:ecommerce|brands?|stores?)",
            r"(?:performance|paid|digital)\s+marketing\s+(?:for|with)\s+(?:ecommerce|brands?|d2c|stores?)",
        ],
        "provides_ecommerce_marketing": [
            r"(?:we\s+)?(?:provide|offer|deliver)\s+(?:ecommerce|digital|online)\s+marketing",
            r"(?:ecommerce|digital)\s+marketing\s+(?:agency|company|firm|services?)",
        ],
        "handles_customer_experience": [
            r"(?:we\s+)?(?:handle|manage|provide|optimize)\s+(?:customer\s+experience|cx|customer\s+success|customer\s+journey)",
            r"(?:customer\s+experience|cx)\s+(?:agency|company|consultant|expert)",
        ],
        "wants_recurring_revenue": [
            r"(?:looking|seeking|want)\s+(?:for\s+)?(?:recurring|residual|passive)\s+revenue",
            r"(?:additional|new|extra)\s+(?:recurring|monthly|residual)\s+revenue",
            r"(?:white.?label|resell|referral|partner)\s+(?:opportunity|program|arrangement)",
        ],
    }
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def detect(self, event: RawEvent) -> DetectionResult | None:
        """Detect COMAI buying signals in an event."""
        
        # Step 1: Evaluate ICP
        icp_score = self._evaluate_icp(event)
        if icp_score < 0.3:
            return None  # Not ecommerce-related
        
        # Step 2: Detect pain signals
        pain_signals = self._detect_pain_signals(event)
        
        # Step 3: Detect buying signals (explicit intent)
        buying_signals = self._detect_buying_signals(event)
        
        # Step 4: Detect partner signals
        partner_signal = self._detect_partner_signals(event)
        
        # Step 5: Classify
        classification = self._classify(icp_score, pain_signals, buying_signals, partner_signal)
        
        # Step 6: Extract company info
        company_name = self._extract_company_name(event)
        company_domain = self._extract_domain(event)
        contact_info = self._extract_contact_info(event)
        
        # Step 7: Build evidence
        evidence = self._collect_evidence(event, pain_signals, buying_signals, partner_signal)
        
        # Step 8: Build problem/why_now/solution
        problem, why_now, solution_match = self._build_problem_solution(
            classification, pain_signals, buying_signals, partner_signal
        )
        
        # Step 9: Build outreach reason
        outreach_reason = self._build_outreach_reason(
            classification, company_name, problem, pain_signals, buying_signals, partner_signal
        )
        
        return DetectionResult(
            classification=classification,
            icp_score=icp_score,
            pain_signals=pain_signals,
            buying_signals=buying_signals,
            partner_signal=partner_signal,
            company_name=company_name,
            company_domain=company_domain,
            contact_info=contact_info,
            evidence=evidence,
            problem=problem,
            why_now=why_now,
            solution_match=solution_match,
            outreach_reason=outreach_reason,
        )
    
    def _evaluate_icp(self, event: RawEvent) -> float:
        """Evaluate ICP match score (0.0-1.0).
        
        COMAI ICP: Broad ecommerce businesses with customer interaction.
        """
        text = f"{event.title} {event.content}".lower()
        metadata = event.event_metadata or {}
        
        score = 0.0
        
        # Check domain keywords
        for keyword in self.ICP_KEYWORDS:
            if keyword in text:
                score += 0.15
                break
        
        # Check for ecommerce indicators
        ecommerce_indicators = [
            "shopify", "woocommerce", "bigcommerce", "magento",
            "ecommerce", "e-commerce", "d2c", "dtc", "online store",
            "product", "brand", "retail", "consumer",
        ]
        for indicator in ecommerce_indicators:
            if indicator in text:
                score += 0.1
        
        # Check metadata for ecommerce signals
        if metadata.get("industry"):
            industry = metadata["industry"].lower()
            if any(x in industry for x in ["ecommerce", "retail", "consumer", "d2c"]):
                score += 0.2
        
        # Check for customer interaction indicators
        customer_indicators = [
            "customers", "clients", "orders", "sales", "support",
            "messages", "inquiries", "questions", "conversations",
        ]
        for indicator in customer_indicators:
            if indicator in text:
                score += 0.05
        
        # Strong signal: customer support pain (COMAI's core use case)
        support_pain_indicators = [
            "support team", "customer support", "customer service",
            "response time", "overwhelmed", "drowning", "too many",
            "can't keep up", "need automation", "looking for solution",
            "whatsapp", "chatbot", "chat messages",
        ]
        support_pain_count = sum(1 for indicator in support_pain_indicators if indicator in text)
        if support_pain_count >= 2:
            score += 0.3  # Strong signal for COMAI ICP
        
        # Strong signal: explicit ecommerce + pain
        if any(x in text for x in ["shopify", "woocommerce", "ecommerce"]) and any(x in text for x in ["support", "messages", "customers"]):
            score += 0.2
        
        return min(score, 1.0)
    
    def _detect_pain_signals(self, event: RawEvent) -> list[PainSignal]:
        """Detect verified business pain (not buying intent)."""
        text = f"{event.title} {event.content}".lower()
        signals = []
        
        for signal_type, patterns in self.PAIN_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    signals.append(PainSignal(
                        signal_type=signal_type,
                        description=self._describe_pain(signal_type),
                        evidence=[f"Pattern matched: {pattern}"],
                        confidence=0.7,
                    ))
                    break  # One match per signal type
        
        return signals
    
    def _detect_buying_signals(self, event: RawEvent) -> list[BuyingSignal]:
        """Detect explicit buying intent (rare for COMAI)."""
        text = f"{event.title} {event.content}".lower()
        signals = []
        
        for signal_type, patterns in self.BUYING_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    signals.append(BuyingSignal(
                        signal_type=signal_type,
                        description=self._describe_buying(signal_type),
                        evidence=[f"Pattern matched: {pattern}"],
                        confidence=0.8,
                    ))
                    break
        
        return signals
    
    def _detect_partner_signals(self, event: RawEvent) -> PartnerSignal | None:
        """Detect agency/partner opportunity."""
        text = f"{event.title} {event.content}".lower()
        
        matched_services = []
        for service_type, patterns in self.PARTNER_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matched_services.append(service_type)
                    break
        
        if not matched_services:
            return None
        
        # Extract agency name
        agency_name = self._extract_company_name(event)
        
        return PartnerSignal(
            signal_type="agency_partner",
            agency_name=agency_name or "Unknown Agency",
            services=matched_services,
            client_icp=["ecommerce", "d2c", "shopify", "brands"],
            evidence=[f"Matched services: {', '.join(matched_services)}"],
            confidence=0.7,
        )
    
    def _classify(
        self,
        icp_score: float,
        pain_signals: list[PainSignal],
        buying_signals: list[BuyingSignal],
        partner_signal: PartnerSignal | None,
    ) -> str:
        """Classify into 6-level system.
        
        CRITICAL RULES:
        - Website absence alone MUST NOT be called a BUYING EVENT
        - "No chatbot detected" = PAIN, NOT BUYING EVENT
        - "Growing ecommerce business" = ICP/GROWTH SIGNAL, NOT BUYING EVENT
        """
        from app.models.buying_event import BuyingEventClassification
        
        # Rule 1: Must match ICP (score > 0.4)
        if icp_score < 0.4:
            return BuyingEventClassification.REJECT
        
        # Rule 2: Check for explicit buying intent
        if buying_signals:
            return BuyingEventClassification.ACTIVE_BUYING_EVENT
        
        # Rule 3: Check for verified pain
        if pain_signals:
            return BuyingEventClassification.VERIFIED_PAIN
        
        # Rule 4: Check for partner opportunity
        if partner_signal:
            return BuyingEventClassification.PARTNER_OPPORTUNITY
        
        # Rule 5: Fits ICP but no pain/signals
        if icp_score >= 0.5:
            return BuyingEventClassification.ICP_OPPORTUNITY
        
        # Rule 6: Insufficient evidence
        return BuyingEventClassification.NURTURE
    
    def _build_problem_solution(
        self,
        classification: str,
        pain_signals: list[PainSignal],
        buying_signals: list[BuyingSignal],
        partner_signal: PartnerSignal | None,
    ) -> tuple[str | None, str | None, str | None]:
        """Build problem, why_now, and solution_match based on classification."""
        from app.models.buying_event import BuyingEventClassification
        
        if classification == BuyingEventClassification.ACTIVE_BUYING_EVENT:
            if buying_signals:
                signal = buying_signals[0]
                return (
                    signal.description,
                    "Actively seeking a solution",
                    "COMAI -- WhatsApp AI Automation",
                )
        
        elif classification == BuyingEventClassification.VERIFIED_PAIN:
            if pain_signals:
                signal = pain_signals[0]
                return (
                    signal.description,
                    "Current capacity cannot keep up with demand",
                    "COMAI -- AI Chatbot for Commerce",
                )
        
        elif classification == BuyingEventClassification.PARTNER_OPPORTUNITY:
            if partner_signal:
                return (
                    f"Agency providing {', '.join(partner_signal.services[:2])}",
                    "Agency wants additional recurring revenue",
                    "COMAI -- White-label WhatsApp Automation",
                )
        
        elif classification == BuyingEventClassification.ICP_OPPORTUNITY:
            return (
                "Ecommerce business that may benefit from automation",
                "Growing business with potential operational pressure",
                "COMAI -- WhatsApp AI Automation",
            )
        
        return None, None, None
    
    def _build_outreach_reason(
        self,
        classification: str,
        company_name: str | None,
        problem: str | None,
        pain_signals: list[PainSignal],
        buying_signals: list[BuyingSignal],
        partner_signal: PartnerSignal | None,
    ) -> str | None:
        """Build evidence-based outreach reason."""
        from app.models.buying_event import BuyingEventClassification
        
        name = company_name or "This company"
        
        if classification == BuyingEventClassification.ACTIVE_BUYING_EVENT:
            return f"{name} has an explicit need for customer support automation. They are actively looking for a solution."
        
        elif classification == BuyingEventClassification.VERIFIED_PAIN:
            pain = pain_signals[0].description if pain_signals else "operational challenges"
            return f"{name} has verified business pain: {pain}. We can help reduce their support burden with AI automation."
        
        elif classification == BuyingEventClassification.PARTNER_OPPORTUNITY:
            services = partner_signal.services[0] if partner_signal else "marketing"
            return f"{name} is an agency serving ecommerce clients. They could benefit from white-label WhatsApp automation for their clients."
        
        elif classification == BuyingEventClassification.ICP_OPPORTUNITY:
            return f"{name} is an ecommerce business that fits our ICP. They may benefit from AI-powered customer support."
        
        return None
    
    def _extract_company_name(self, event: RawEvent) -> str | None:
        """Extract company name from event."""
        metadata = event.event_metadata or {}
        
        # Try various metadata fields
        for field in ["company_name", "organization", "org", "company", "brand"]:
            if metadata.get(field):
                return metadata[field]
        
        # Try to extract from title
        title = event.title or ""
        if " - " in title:
            return title.split(" - ")[0].strip()
        if " | " in title:
            return title.split(" | ")[0].strip()
        
        return None
    
    def _extract_domain(self, event: RawEvent) -> str | None:
        """Extract company domain from event."""
        metadata = event.event_metadata or {}
        
        # Try various metadata fields
        for field in ["domain", "website", "url", "homepage", "official_website"]:
            if metadata.get(field):
                domain = metadata[field]
                # Clean up domain
                domain = domain.replace("https://", "").replace("http://", "")
                domain = domain.replace("www.", "").rstrip("/")
                return domain
        
        return None
    
    def _extract_contact_info(self, event: RawEvent) -> dict[str, Any]:
        """Extract contact information from event."""
        metadata = event.event_metadata or {}
        
        contact = {
            "author": metadata.get("author") or metadata.get("username"),
            "email": metadata.get("email"),
            "linkedin": metadata.get("linkedin"),
            "twitter": metadata.get("twitter"),
        }
        
        return contact
    
    def _collect_evidence(
        self,
        event: RawEvent,
        pain_signals: list[PainSignal],
        buying_signals: list[BuyingSignal],
        partner_signal: PartnerSignal | None,
    ) -> list[dict[str, Any]]:
        """Collect evidence items from the event."""
        evidence = []
        
        # Add content evidence
        if event.content and len(event.content.strip()) > 20:
            evidence.append({
                "type": "content",
                "source": event.source,
                "value": event.content[:500],
            })
        
        # Add pain signal evidence
        for signal in pain_signals:
            evidence.append({
                "type": "pain_signal",
                "signal": signal.signal_type,
                "description": signal.description,
                "confidence": signal.confidence,
            })
        
        # Add buying signal evidence
        for signal in buying_signals:
            evidence.append({
                "type": "buying_signal",
                "signal": signal.signal_type,
                "description": signal.description,
                "confidence": signal.confidence,
            })
        
        # Add partner evidence
        if partner_signal:
            evidence.append({
                "type": "partner_signal",
                "services": partner_signal.services,
                "confidence": partner_signal.confidence,
            })
        
        return evidence
    
    def _describe_pain(self, signal_type: str) -> str:
        """Describe a pain signal."""
        descriptions = {
            "high_support_volume": "High volume of customer support messages",
            "slow_response_time": "Slow customer response times",
            "no_automation": "No automation in customer support",
            "customer_engagement_problems": "Customer engagement problems",
            "scaling_support_team": "Difficulty scaling support team",
            "whatsapp_heavy_business": "WhatsApp-heavy business communication",
            "high_order_volume": "High order volume creating operational pressure",
            "ecommerce_pain": "Ecommerce business with operational challenges",
        }
        return descriptions.get(signal_type, "Unknown pain signal")
    
    def _describe_buying(self, signal_type: str) -> str:
        """Describe a buying signal."""
        descriptions = {
            "looking_for_chatbot": "Actively looking for a chatbot solution",
            "need_whatsapp_automation": "Needs WhatsApp automation",
            "searching_for_ai_support": "Searching for AI-powered support",
        }
        return descriptions.get(signal_type, "Unknown buying signal")
