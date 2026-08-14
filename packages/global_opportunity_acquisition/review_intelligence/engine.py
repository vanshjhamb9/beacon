from __future__ import annotations

from global_opportunity_acquisition.models.types import ReviewSignal


class ReviewIntelligenceEngine:
    def analyze(self, texts: list[str]) -> ReviewSignal:
        blob = " ".join(texts).lower()
        complaints = []
        missing = []
        pains = []
        competitors = []
        migrations = []
        for phrase in ("slow support", "buggy", "expensive", "poor ux", "downtime"):
            if phrase in blob:
                complaints.append(phrase)
        for phrase in ("missing reporting", "no api", "no sso", "no mobile", "limited integrations"):
            if phrase in blob:
                missing.append(phrase)
        for phrase in ("manual process", "too complex", "hard to use", "steep learning"):
            if phrase in blob:
                pains.append(phrase)
        for phrase in ("salesforce", "hubspot", "zendesk", "intercom", "shopify"):
            if phrase in blob:
                competitors.append(phrase)
        for phrase in ("switching from", "migrating to", "looking for alternative", "alternative to"):
            if phrase in blob:
                migrations.append(phrase)
        return ReviewSignal(
            complaints=complaints,
            missing_features=missing,
            pain_points=pains,
            competitor_mentions=list(dict.fromkeys(competitors)),
            migration_opportunities=migrations,
            evidence=[f"complaints:{len(complaints)}", f"migrations:{len(migrations)}"],
        )
