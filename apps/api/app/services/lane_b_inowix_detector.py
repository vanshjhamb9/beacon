"""Lane B: INOWIX Detector - SaaS + Custom Software + AI + Mobile/Web Development.

INOWIX TARGET:
- Startup founders
- New startups
- Growing startups
- Bootstrapped SaaS companies
- Funded startups
- Small businesses
- Mid-size businesses
- Companies launching new products
- Companies needing internal software
- Companies needing automation
- Companies needing AI integration
- Companies needing MVP development
- Companies needing web/mobile development
- Companies with technical bottlenecks

IMPORTANT:
- Funding alone ≠ buying event
- Hiring alone ≠ outsourcing
- Company growth alone ≠ buying event
These are SUPPORTING SIGNALS that increase outbound priority.

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
class BuyingSignal:
    """Explicit development requirement."""
    signal_type: str
    description: str
    evidence: list[str]
    confidence: float


@dataclass
class SupportingSignal:
    """Supporting signal (funding, hiring, etc.) - increases priority but NOT buying event."""
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
    """Result of INOWIX detection."""
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


class LaneB_INOWIX_Detector:
    """INOWIX-specific detection with technical company ICP.
    
    Key distinction:
    - Funding alone ≠ buying event (supporting signal only)
    - Hiring alone ≠ outsourcing (supporting signal only)
    - Company growth alone ≠ buying event (supporting signal only)
    """
    
    # ICP Definition - Technical/startup companies
    ICP_KEYWORDS = {
        "startup", "saas", "founder", "bootstrapped", "funded",
        "mvp", "web app", "mobile app", "ai development", "automation",
        "software", "technical", "engineering", "development",
    }
    
    # Buying Signals - Explicit development requirements
    BUYING_PATTERNS = {
        "looking_for_developer": [
            r"(?:looking|searching|finding|need|want)\s+(?:for\s+)?(?:a\s+)?(?:developer|development\s+team|technical\s+team|engineering\s+team)",
            r"(?:need|looking|want)\s+(?:to\s+)?(?:hire|find|bring\s+on)\s+(?:a\s+)?(?:developer|engineer|technical\s+lead)",
            r"(?:looking|searching)\s+(?:for\s+)?(?:freelancer|contractor|consultant)\s+(?:for|to)\s+(?:build|develop|create)",
        ],
        "need_mvp_built": [
            r"(?:need|looking|want)\s+(?:to\s+)?(?:build|develop|create|launch)\s+(?:an?\s+)?(?:mvp|minimum\s+viable\s+product|prototype)",
            r"(?:mvp|prototype|proof\s+of\s+concept)\s+(?:development|build|create)",
            r"(?:looking|searching)\s+(?:for\s+)?(?:someone|team|agency)\s+(?:to\s+)?(?:build|develop|create)\s+(?:our|an?\s+)?(?:mvp|product)",
        ],
        "need_saas_development": [
            r"(?:need|looking|want)\s+(?:to\s+)?(?:build|develop|create|launch)\s+(?:a\s+)?(?:saas|software\s+as\s+a\s+service|platform|application)",
            r"(?:saas|platform|application)\s+(?:development|build|create|launch)",
            r"(?:looking|searching)\s+(?:for\s+)?(?:someone|team|agency)\s+(?:to\s+)?(?:build|develop|create)\s+(?:our|a)\s+(?:saas|platform)",
        ],
        "need_mobile_app": [
            r"(?:need|looking|want)\s+(?:to\s+)?(?:build|develop|create|launch)\s+(?:a\s+)?(?:mobile\s+app|ios\s+app|android\s+app|react\s+native\s+app|flutter\s+app)",
            r"(?:mobile|ios|android|react\s+native|flutter)\s+(?:app|application)\s+(?:development|build|create)",
        ],
        "need_web_application": [
            r"(?:need|looking|want)\s+(?:to\s+)?(?:build|develop|create|launch)\s+(?:a\s+)?(?:web\s+app|web\s+application|web\s+platform|web\s+portal)",
            r"(?:web|frontend|full.?stack)\s+(?:app|application|platform)\s+(?:development|build|create)",
        ],
        "need_ai_development": [
            r"(?:need|looking|want)\s+(?:to\s+)?(?:build|develop|create|implement|integrate)\s+(?:ai|machine\s+learning|ml|llm|gpt|chatgpt|openai)",
            r"(?:ai|machine\s+learning|ml|llm|gpt)\s+(?:development|integration|implementation|solution)",
        ],
        "need_automation": [
            r"(?:need|looking|want)\s+(?:to\s+)?(?:automate|build|create)\s+(?:a\s+)?(?:workflow|automation|pipeline|system)",
            r"(?:workflow|process|task)\s+automation\s+(?:development|build|create|solution)",
        ],
        "need_technical_team": [
            r"(?:need|looking|want)\s+(?:to\s+)?(?:hire|find|bring\s+on)\s+(?:a\s+)?(?:technical\s+team|development\s+team|engineering\s+team)",
            r"(?:looking|searching)\s+(?:for\s+)?(?:external\s+)?(?:development\s+team|technical\s+team|engineering\s+partner)",
        ],
        "project_delayed": [
            r"(?:project|product|launch)\s+(?:is\s+)?(?:delayed|behind|stuck|blocked)\s+(?:because|due\s+to|from)\s+(?:technical|development|engineering)",
            r"(?:can'?t|cannot|unable)\s+to\s+(?:launch|ship|deliver)\s+(?:because|due\s+to|from)\s+(?:technical|development|lack\s+of)",
            r"(?:technical|development|engineering)\s+(?:bottleneck|limitation|constraint|blocker)",
        ],
        "team_overloaded": [
            r"(?:existing|current|our)\s+(?:development|engineering|technical)\s+team\s+(?:is\s+)?(?:overloaded|overwhelmed|busy|swamped|backed\s+up)",
            r"(?:can'?t|cannot|unable)\s+to\s+(?:keep\s+up|handle|manage|deliver)\s+(?:with\s+)?(?:all\s+)?(?:the\s+)?(?:work|projects?|tasks?|requests?)",
            r"(?:need|looking)\s+(?:for\s+)?(?:additional|extra|more|outside)\s+(?:development|technical|engineering)\s+(?:capacity|help|support|resources?)",
        ],
    }
    
    # Supporting Signals - Increase priority but NOT buying events
    SUPPORTING_PATTERNS = {
        "funding": [
            r"(?:raised|securing|closed|got)\s+(?:a\s+)?(?:seed|series\s+[a-z]|pre.?seed|angel|round)\s+(?:of\s+)?(?:funding|investment|capital)",
            r"(?:funded|backed|invested)\s+(?:by|with)\s+(?:\$[\d,.]+|[a-z]+\s+ventures?|[a-z]+\s+capital)",
            r"(?:looking|seeking)\s+(?:for\s+)?(?:funding|investment|investors?|capital)",
        ],
        "hiring_engineers": [
            r"(?:hiring|recruiting|looking\s+for)\s+(?:a\s+)?(?:software\s+engineer|developer|full.?stack|backend|frontend|mobile)",
            r"(?:engineering|development)\s+(?:team|department)\s+(?:is\s+)?(?:growing|expanding|hiring)",
        ],
        "new_product_launch": [
            r"(?:launching|launched|shipping|shipped|releasing|released)\s+(?:a\s+)?(?:new\s+)?(?:product|feature|platform|service|tool)",
            r"(?:product|feature|platform)\s+(?:launch|release|ship)",
        ],
        "rapid_growth": [
            r"(?:growing|scaling|expanding)\s+(?:rapidly|quickly|fast|significantly)",
            r"(?:revenue|users?|customers?|growth)\s+(?:is\s+)?(?:growing|increasing|scaling)\s+(?:rapidly|quickly|fast)",
        ],
        "technical_hiring": [
            r"(?:hiring|recruiting|looking\s+for)\s+(?:a\s+)?(?:cto|vp\s+of\s+engineering|head\s+of\s+engineering|tech\s+lead)",
            r"(?:technical|engineering)\s+(?:leadership|head|director)\s+(?:role|position|hire)",
        ],
    }
    
    # Partner Signals - Agency/partner opportunity
    PARTNER_PATTERNS = {
        "software_agency": [
            r"(?:we\s+)?(?:are|'?re)\s+(?:a\s+)?(?:software|development|tech|digital)\s+(?:agency|company|firm|studio|consultancy)",
            r"(?:software|development|tech)\s+(?:agency|company|firm|studio|consultancy)",
        ],
        "it_consultant": [
            r"(?:we\s+)?(?:are|'?re)\s+(?:an?\s+)?(?:it|technical|technology)\s+(?:consultant|consulting|advisor)",
            r"(?:it|technical|technology)\s+(?:consultant|consulting|consultancy)",
        ],
        "product_studio": [
            r"(?:we\s+)?(?:are|'?re)\s+(?:a\s+)?(?:product|digital|design)\s+(?:studio|lab|agency)",
            r"(?:product|digital|design)\s+(?:studio|lab|agency)",
        ],
        "no_code_agency": [
            r"(?:we\s+)?(?:build|create|develop)\s+(?:with\s+)?(?:no.?code|low.?code|bubble|webflow|airtable)",
            r"(?:no.?code|low.?code)\s+(?:agency|company|studio|consultant)",
        ],
        "development_agency_needs_capacity": [
            r"(?:looking|seeking|need)\s+(?:for\s+)?(?:white.?label|subcontract|outsource|partner)\s+(?:development|technical|engineering)",
            r"(?:white.?label|resell|referral|partner)\s+(?:development|technical|engineering)\s+(?:opportunity|program|arrangement)",
        ],
    }
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def detect(self, event: RawEvent) -> DetectionResult | None:
        """Detect INOWIX buying signals in an event."""
        
        # Step 1: Evaluate ICP
        icp_score = self._evaluate_icp(event)
        if icp_score < 0.3:
            return None  # Not technical/startup-related
        
        # Step 2: Detect buying signals (explicit intent)
        buying_signals = self._detect_buying_signals(event)
        
        # Step 3: Detect supporting signals (funding, hiring, etc.)
        supporting_signals = self._detect_supporting_signals(event)
        
        # Step 4: Detect partner signals
        partner_signal = self._detect_partner_signals(event)
        
        # Step 5: Classify
        classification = self._classify(icp_score, buying_signals, supporting_signals, partner_signal)
        
        # Step 6: Extract company info
        company_name = self._extract_company_name(event)
        company_domain = self._extract_domain(event)
        contact_info = self._extract_contact_info(event)
        
        # Step 7: Build evidence
        evidence = self._collect_evidence(event, buying_signals, supporting_signals, partner_signal)
        
        # Step 8: Build problem/why_now/solution
        problem, why_now, solution_match = self._build_problem_solution(
            classification, buying_signals, supporting_signals, partner_signal
        )
        
        # Step 9: Build outreach reason
        outreach_reason = self._build_outreach_reason(
            classification, company_name, problem, buying_signals, supporting_signals, partner_signal
        )
        
        return DetectionResult(
            classification=classification,
            icp_score=icp_score,
            buying_signals=buying_signals,
            supporting_signals=supporting_signals,
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
        
        INOWIX ICP: Technical/startup companies needing development services.
        """
        text = f"{event.title} {event.content}".lower()
        metadata = event.event_metadata or {}
        
        score = 0.0
        
        # Check ICP keywords
        for keyword in self.ICP_KEYWORDS:
            if keyword in text:
                score += 0.15
                break
        
        # Check for technical indicators
        technical_indicators = [
            "developer", "engineer", "technical", "software", "saas",
            "mvp", "web app", "mobile app", "ai", "automation",
            "startup", "founder", "bootstrapped", "funded",
        ]
        for indicator in technical_indicators:
            if indicator in text:
                score += 0.1
        
        # Check metadata for technical signals
        if metadata.get("industry"):
            industry = metadata["industry"].lower()
            if any(x in industry for x in ["technology", "software", "saas", "tech"]):
                score += 0.2
        
        # Check for company indicators
        company_indicators = [
            "company", "startup", "business", "venture", "studio",
            "agency", "consultancy", "firm",
        ]
        for indicator in company_indicators:
            if indicator in text:
                score += 0.05
        
        # Strong signal: technical pain (INOWIX's core use case)
        technical_pain_indicators = [
            "need developer", "looking for developer", "need engineer",
            "need mvp", "need mobile app", "need web app",
            "need software", "looking for team", "need technical",
            "funded", "seed", "series a", "raising",
        ]
        technical_pain_count = sum(1 for indicator in technical_pain_indicators if indicator in text)
        if technical_pain_count >= 2:
            score += 0.3  # Strong signal for INOWIX ICP
        
        # Strong signal: explicit technical need + company
        if any(x in text for x in ["startup", "founded", "company"]) and any(x in text for x in ["developer", "engineer", "technical", "software"]):
            score += 0.2
        
        return min(score, 1.0)
    
    def _detect_buying_signals(self, event: RawEvent) -> list[BuyingSignal]:
        """Detect explicit development requirements."""
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
    
    def _detect_supporting_signals(self, event: RawEvent) -> list[SupportingSignal]:
        """Detect supporting signals (funding, hiring, etc.).
        
        These increase priority but are NOT buying events.
        """
        text = f"{event.title} {event.content}".lower()
        signals = []
        
        for signal_type, patterns in self.SUPPORTING_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    signals.append(SupportingSignal(
                        signal_type=signal_type,
                        description=self._describe_supporting(signal_type),
                        evidence=[f"Pattern matched: {pattern}"],
                        confidence=0.7,
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
            client_icp=["startups", "saas", "tech", "growth"],
            evidence=[f"Matched services: {', '.join(matched_services)}"],
            confidence=0.7,
        )
    
    def _classify(
        self,
        icp_score: float,
        buying_signals: list[BuyingSignal],
        supporting_signals: list[SupportingSignal],
        partner_signal: PartnerSignal | None,
    ) -> str:
        """Classify into 6-level system.
        
        CRITICAL RULES:
        - Funding alone ≠ buying event
        - Hiring alone ≠ outsourcing
        - Company growth alone ≠ buying event
        """
        from app.models.buying_event import BuyingEventClassification
        
        # Rule 1: Must match ICP (score > 0.4)
        if icp_score < 0.4:
            return BuyingEventClassification.REJECT
        
        # Rule 2: Check for explicit buying intent
        if buying_signals:
            return BuyingEventClassification.ACTIVE_BUYING_EVENT
        
        # Rule 3: Check for partner opportunity
        if partner_signal:
            return BuyingEventClassification.PARTNER_OPPORTUNITY
        
        # Rule 4: Supporting signals only = ICP opportunity
        if supporting_signals:
            return BuyingEventClassification.ICP_OPPORTUNITY
        
        # Rule 5: Fits ICP but no signals
        if icp_score >= 0.5:
            return BuyingEventClassification.NURTURE
        
        # Rule 6: Insufficient evidence
        return BuyingEventClassification.REJECT
    
    def _build_problem_solution(
        self,
        classification: str,
        buying_signals: list[BuyingSignal],
        supporting_signals: list[SupportingSignal],
        partner_signal: PartnerSignal | None,
    ) -> tuple[str | None, str | None, str | None]:
        """Build problem, why_now, and solution_match based on classification."""
        from app.models.buying_event import BuyingEventClassification
        
        if classification == BuyingEventClassification.ACTIVE_BUYING_EVENT:
            if buying_signals:
                signal = buying_signals[0]
                return (
                    signal.description,
                    "Actively seeking a development partner",
                    "INOWIX -- SaaS + Custom Software Development",
                )
        
        elif classification == BuyingEventClassification.PARTNER_OPPORTUNITY:
            if partner_signal:
                return (
                    f"Agency providing {', '.join(partner_signal.services[:2])}",
                    "Agency needs additional development capacity",
                    "INOWIX -- White-label Development Partnership",
                )
        
        elif classification == BuyingEventClassification.ICP_OPPORTUNITY:
            # Supporting signals indicate potential need
            supporting = supporting_signals[0] if supporting_signals else None
            if supporting:
                return (
                    f"Company with {supporting.description}",
                    "Growing company that may need technical support",
                    "INOWIX -- SaaS + Custom Software Development",
                )
        
        return None, None, None
    
    def _build_outreach_reason(
        self,
        classification: str,
        company_name: str | None,
        problem: str | None,
        buying_signals: list[BuyingSignal],
        supporting_signals: list[SupportingSignal],
        partner_signal: PartnerSignal | None,
    ) -> str | None:
        """Build evidence-based outreach reason."""
        from app.models.buying_event import BuyingEventClassification
        
        name = company_name or "This company"
        
        if classification == BuyingEventClassification.ACTIVE_BUYING_EVENT:
            return f"{name} has an explicit development requirement. They are actively looking for a technical partner."
        
        elif classification == BuyingEventClassification.PARTNER_OPPORTUNITY:
            services = partner_signal.services[0] if partner_signal else "development"
            return f"{name} is an agency that could benefit from white-label development capacity."
        
        elif classification == BuyingEventClassification.ICP_OPPORTUNITY:
            if supporting_signals:
                supporting = supporting_signals[0].description
                return f"{name} has {supporting}. They may need additional technical capacity."
            return f"{name} is a technical company that fits our ICP."
        
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
        buying_signals: list[BuyingSignal],
        supporting_signals: list[SupportingSignal],
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
        
        # Add buying signal evidence
        for signal in buying_signals:
            evidence.append({
                "type": "buying_signal",
                "signal": signal.signal_type,
                "description": signal.description,
                "confidence": signal.confidence,
            })
        
        # Add supporting signal evidence
        for signal in supporting_signals:
            evidence.append({
                "type": "supporting_signal",
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
    
    def _describe_buying(self, signal_type: str) -> str:
        """Describe a buying signal."""
        descriptions = {
            "looking_for_developer": "Looking for a developer or development team",
            "need_mvp_built": "Needs MVP built",
            "need_saas_development": "Needs SaaS/platform development",
            "need_mobile_app": "Needs mobile app development",
            "need_web_application": "Needs web application development",
            "need_ai_development": "Needs AI/ML development",
            "need_automation": "Needs workflow automation",
            "need_technical_team": "Needs technical team",
            "project_delayed": "Project delayed due to technical limitations",
            "team_overloaded": "Existing team overloaded",
        }
        return descriptions.get(signal_type, "Unknown buying signal")
    
    def _describe_supporting(self, signal_type: str) -> str:
        """Describe a supporting signal."""
        descriptions = {
            "funding": "Recently raised funding",
            "hiring_engineers": "Hiring engineers",
            "new_product_launch": "Launching new product",
            "rapid_growth": "Rapid company growth",
            "technical_hiring": "Hiring technical leadership",
        }
        return descriptions.get(signal_type, "Unknown supporting signal")
