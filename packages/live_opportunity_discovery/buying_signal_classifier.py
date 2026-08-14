"""Rule-based buying signal classification."""

from __future__ import annotations

from dataclasses import dataclass

from live_opportunity_discovery.discovery_router import LiveEvent


DISCOVERY_CATEGORIES: tuple[str, ...] = (
    "HIRING",
    "FUNDING",
    "EXPANSION",
    "TECHNOLOGY CHANGE",
    "SECURITY",
    "COMPLIANCE",
    "PROCUREMENT",
    "EXECUTIVE CHANGE",
    "MARKETING",
    "SALES",
    "OPERATIONS",
    "CUSTOMER SUPPORT",
    "DIGITAL TRANSFORMATION",
)

EVENT_RULES: dict[str, dict[str, tuple[str, ...]]] = {
    "HIRING": {
        "Hiring SDRs": ("sdr", "sales development representative", "business development"),
        "Hiring Recruiters": ("recruiter", "talent acquisition", "recruitment"),
        "Hiring Engineers": ("engineer", "developer", "software"),
        "Hiring Operations": ("operations manager", "operations lead", "ops"),
        "Hiring HR": ("hr manager", "people ops", "human resources"),
        "Hiring Sales": ("sales manager", "account executive", "sales rep"),
        "Hiring Support": ("support agent", "customer support", "customer success"),
    },
    "EXPANSION": {
        "New office": ("new office", "opened office", "office in"),
        "New country": ("new country", "entered", "launches in"),
        "New market": ("new market", "market expansion", "regional expansion"),
        "New product": ("new product", "product launch", "launched product"),
        "New team": ("new team", "builds team", "expands team"),
    },
    "TECHNOLOGY CHANGE": {
        "Migration": ("migration", "migrating", "modernization"),
        "Replacing CRM": ("replace crm", "new crm", "salesforce", "hubspot"),
        "Replacing ERP": ("replace erp", "new erp", "netsuite", "sap"),
        "Moving cloud": ("cloud migration", "moving to cloud", "aws", "azure", "gcp"),
        "New integrations": ("integration", "api", "connected apps"),
        "Hiring DevOps": ("devops", "platform engineer", "site reliability"),
    },
    "FUNDING": {
        "Series A": ("series a",),
        "Series B": ("series b",),
        "Series C": ("series c",),
        "Debt": ("debt financing", "credit facility", "venture debt"),
        "Strategic investment": ("strategic investment", "strategic investor"),
    },
    "EXECUTIVE CHANGE": {
        "New CEO": ("new ceo", "appointed ceo"),
        "New CTO": ("new cto", "appointed cto"),
        "New CRO": ("new cro", "appointed cro"),
        "VP Sales": ("vp sales", "vice president of sales"),
        "Head HR": ("head of hr", "chief people", "people leader"),
    },
    "SECURITY": {"Security program": ("security", "soc 2", "iso 27001", "breach")},
    "COMPLIANCE": {"Compliance program": ("compliance", "gdpr", "hipaa", "audit")},
    "PROCUREMENT": {"Procurement": ("tender", "rfp", "procurement", "contract notice")},
    "MARKETING": {"Marketing growth": ("marketing", "campaign", "demand generation")},
    "SALES": {"Sales growth": ("sales team", "pipeline", "go-to-market")},
    "OPERATIONS": {"Operations change": ("operations", "supply chain", "workflow")},
    "CUSTOMER SUPPORT": {"Support scale": ("support", "helpdesk", "customer service")},
    "DIGITAL TRANSFORMATION": {"Transformation": ("digital transformation", "automation", "modernize")},
}


@dataclass(frozen=True, slots=True)
class ClassifiedBuyingSignal:
    category: str
    event_type: str
    score: float
    reasons: tuple[str, ...]


class BuyingSignalClassifier:
    def classify(self, event: LiveEvent) -> ClassifiedBuyingSignal | None:
        text = f"{event.headline} {event.description}".lower()
        for category, event_rules in EVENT_RULES.items():
            for event_type, keywords in event_rules.items():
                matches = tuple(keyword for keyword in keywords if keyword in text)
                if matches:
                    return ClassifiedBuyingSignal(
                        category=category,
                        event_type=event_type,
                        score=min(70.0 + (len(matches) * 8.0), 100.0),
                        reasons=tuple(f"Matched keyword '{match}'" for match in matches),
                    )
        return None
