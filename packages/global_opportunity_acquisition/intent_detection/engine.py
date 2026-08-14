from __future__ import annotations

from global_opportunity_acquisition.models.types import DetectedIntent, OpportunityIntent

INTENT_PATTERNS: list[tuple[OpportunityIntent, tuple[str, ...], float]] = [
    (OpportunityIntent.HIRING, ("hiring", "we're hiring", "job opening", "open role"), 80.0),
    (OpportunityIntent.FUNDING, ("raised", "series a", "series b", "seed round", "funding"), 85.0),
    (OpportunityIntent.EXPANSION, ("expanding", "new office", "opening office"), 78.0),
    (OpportunityIntent.AI_ADOPTION, ("adopting ai", "openai", "llm", "generative ai"), 82.0),
    (OpportunityIntent.DIGITAL_TRANSFORMATION, ("digital transformation", "digitize", "modernize ops"), 80.0),
    (OpportunityIntent.WEBSITE_REBUILD, ("redesign website", "rebuild site", "new website"), 84.0),
    (OpportunityIntent.CRM_MIGRATION, ("migrate crm", "salesforce migration", "hubspot migration"), 86.0),
    (OpportunityIntent.ERP_MIGRATION, ("erp migration", "sap migration", "netsuite"), 86.0),
    (OpportunityIntent.CLOUD_MIGRATION, ("cloud migration", "move to aws", "azure migration"), 85.0),
    (OpportunityIntent.AUTOMATION, ("automate", "automation", "workflow automation"), 80.0),
    (OpportunityIntent.CUSTOMER_SUPPORT_SCALING, ("scale support", "support team", "zendesk"), 78.0),
    (OpportunityIntent.MARKETING_SCALING, ("scale marketing", "demand gen", "growth marketing"), 78.0),
    (OpportunityIntent.STARTUP_LAUNCH, ("launched", "just launched", "startup launch"), 75.0),
    (OpportunityIntent.ACQUISITION, ("acquired", "acquisition", "acquires"), 88.0),
    (OpportunityIntent.IPO, ("ipo", "public listing", "s-1"), 90.0),
    (OpportunityIntent.PRODUCT_LAUNCH, ("product launch", "announcing", "new product"), 76.0),
    (OpportunityIntent.TECHNOLOGY_MIGRATION, ("tech migration", "platform migration", "rewrite"), 80.0),
    (OpportunityIntent.INFRASTRUCTURE_UPGRADES, ("infra upgrade", "infrastructure", "kubernetes"), 77.0),
    (OpportunityIntent.INTERNATIONAL_EXPANSION, ("international expansion", "global expansion", "enter market"), 81.0),
    (OpportunityIntent.COMPLIANCE_CHANGES, ("compliance", "gdpr", "soc2", "hipaa"), 79.0),
    (OpportunityIntent.SECURITY_INVESTMENT, ("security investment", "zero trust", "penetration test"), 80.0),
    (OpportunityIntent.PLATFORM_MODERNIZATION, ("platform modernization", "legacy modernization", "rewrite monolith"), 83.0),
]


class IntentDetectionEngine:
    def detect(self, texts: list[str]) -> list[DetectedIntent]:
        blob = " ".join(texts).lower()
        out: list[DetectedIntent] = []
        for intent, patterns, base in INTENT_PATTERNS:
            hits = [p for p in patterns if p in blob]
            if hits:
                out.append(
                    DetectedIntent(
                        intent=intent,
                        confidence=min(95.0, base + len(hits) * 2.0),
                        evidence=[f"hits:{','.join(hits[:3])}"],
                    )
                )
        out.sort(key=lambda d: (-d.confidence, d.intent.value))
        return out
