from urllib.parse import urlparse

from quality_engine.models.types import NormalizedQualityEvent, QualityStage, SourceQualityProfile, StageResult
from quality_engine.rules.definitions import RuleCatalog

OFFICIAL_DOMAIN_HINTS = (".gov", ".edu", "sec.gov", "newsroom", "press", "investor")
ANONYMOUS_SOURCES = {"reddit"}
COMMUNITY_SOURCES = {"reddit", "hacker_news", "product_hunt"}


class SourceTrustScorer:
    def score(
        self,
        event: NormalizedQualityEvent,
        rules: RuleCatalog,
        profile: SourceQualityProfile,
    ) -> StageResult:
        baseline_rule = rules.by_key("source.community_default")
        baselines = baseline_rule.parameters if baseline_rule else {}
        trust = float(baselines.get(event.source, 60.0))
        reasons: list[str] = []

        trust += min(12.0, profile.average_quality / 10.0)
        trust -= profile.spam_rate * 25.0
        trust -= profile.duplicate_rate * 15.0

        domain = urlparse(event.url).netloc.lower()
        if any(hint in domain for hint in OFFICIAL_DOMAIN_HINTS):
            trust += 12.0
            reasons.append("official_source")
        elif event.source in COMMUNITY_SOURCES:
            reasons.append("community_source")
        if event.source in ANONYMOUS_SOURCES:
            trust -= 8.0
            reasons.append("anonymous_source")

        if profile.collector_health == "down":
            trust -= 20.0
            reasons.append("collector_down")
        elif profile.collector_health == "degraded":
            trust -= 10.0
            reasons.append("collector_degraded")

        trust = max(0.0, min(100.0, trust))
        return StageResult(
            stage=QualityStage.SOURCE_TRUST,
            score=round(trust, 4),
            passed=trust >= 40.0,
            reason_codes=reasons,
            details={
                "source": event.source,
                "domain": domain,
                "historical_spam_rate": profile.spam_rate,
                "historical_duplicate_rate": profile.duplicate_rate,
                "collector_health": profile.collector_health,
            },
        )
