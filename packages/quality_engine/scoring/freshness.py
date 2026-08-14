from datetime import UTC, datetime

from collectors.freshness import FRESH_HOURS, DIRECTORY_SOURCES
from quality_engine.models.types import NormalizedQualityEvent, QualityStage, StageResult
from quality_engine.rules.definitions import RuleCatalog


class FreshnessScorer:
    def score(self, event: NormalizedQualityEvent, rules: RuleCatalog) -> StageResult:
        rule = rules.by_key("freshness.signal_age")
        params = rule.parameters if rule else {}
        fresh_hours = float(params.get("fresh_hours", FRESH_HOURS))
        fresh_days = float(params.get("fresh_days", fresh_hours / 24.0))
        stale_days = float(params.get("stale_days", 2))
        expired_days = float(params.get("expired_days", 2))
        published = event.published_at.astimezone(UTC)
        age_hours = max(0.0, (datetime.now(UTC) - published).total_seconds() / 3600.0)
        age_days = age_hours / 24.0
        source = str(getattr(event, "source", "") or "").lower()
        meta = getattr(event, "metadata", None) or {}
        if isinstance(meta, dict) and meta.get("source_kind") == "directory":
            directory = True
        else:
            directory = source in DIRECTORY_SOURCES

        if directory:
            return StageResult(
                stage=QualityStage.FRESHNESS,
                score=0.0,
                passed=False,
                reason_codes=["directory_source_not_lead"],
                details={
                    "age_days": round(age_days, 4),
                    "age_hours": round(age_hours, 4),
                    "published_at": published.isoformat(),
                    "source": source,
                },
            )

        if age_hours <= fresh_hours and age_days <= fresh_days:
            score = 100.0
        elif age_days <= stale_days:
            score = 85.0 - ((age_days - fresh_days) / max(0.01, stale_days - fresh_days) * 35.0)
        elif age_days <= expired_days:
            score = 40.0
        else:
            score = 10.0

        expired = age_hours > fresh_hours or age_days > expired_days
        reasons = ["signal_expired"] if expired else []
        return StageResult(
            stage=QualityStage.FRESHNESS,
            score=round(max(0.0, min(100.0, score)), 4),
            passed=not expired,
            reason_codes=reasons,
            details={
                "age_days": round(age_days, 4),
                "age_hours": round(age_hours, 4),
                "fresh_hours": fresh_hours,
                "published_at": published.isoformat(),
            },
        )
