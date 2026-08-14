from __future__ import annotations

from global_opportunity_acquisition.models.types import CommunitySignal

NEED_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("need developer", ("need a developer", "looking for developer", "hire developer")),
    ("need agency", ("need an agency", "looking for agency", "agency recommendation")),
    ("need AI", ("need ai", "looking for ai", "ai solution")),
    ("need SaaS", ("need saas", "looking for saas")),
    ("need automation", ("need automation", "automate this", "workflow automation")),
    ("need website", ("need a website", "redesign website", "build website")),
    ("need mobile app", ("need a mobile app", "build an app", "ios android")),
    ("need chatbot", ("need a chatbot", "chatbot for")),
    ("need CRM", ("need a crm", "crm recommendation")),
    ("need ERP", ("need erp", "erp system")),
    ("need integration", ("need integration", "integrate with")),
    ("need migration", ("need migration", "migrate from")),
    ("need DevOps", ("need devops", "looking for devops")),
    ("need cloud", ("need cloud", "move to cloud")),
]


class CommunityIntelligenceEngine:
    def detect(self, texts: list[str]) -> CommunitySignal:
        blob = " ".join(texts).lower()
        needs: list[str] = []
        evidence: list[str] = []
        for label, patterns in NEED_PATTERNS:
            hits = [p for p in patterns if p in blob]
            if hits:
                needs.append(label)
                evidence.append(f"{label}:{hits[0]}")
        conf = min(95.0, 40.0 + len(needs) * 8.0) if needs else 0.0
        return CommunitySignal(needs=needs, confidence=round(conf, 2), evidence=evidence)
