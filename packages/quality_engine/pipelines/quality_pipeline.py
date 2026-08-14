import time
from datetime import UTC, datetime

from quality_engine.metrics.timing import PipelineTimer
from quality_engine.models.types import (
    QualityDecision,
    QualityEvent,
    QualityGrade,
    QualityReportResult,
    SourceQualityProfile,
)
from quality_engine.rules.definitions import RuleCatalog
from quality_engine.rules.defaults import default_rule_catalog
from quality_engine.scoring.completeness import CompletenessScorer
from quality_engine.scoring.duplicate import DuplicateScorer
from quality_engine.scoring.entity_confidence import EntityConfidenceScorer
from quality_engine.scoring.freshness import FreshnessScorer
from quality_engine.scoring.quality import QualityScoreCombiner
from quality_engine.scoring.spam import SpamScorer
from quality_engine.scoring.trust import SourceTrustScorer
from quality_engine.services.normalization import EventNormalizer
from quality_engine.validators.schema import SchemaValidator


class QualityPipeline:
    def __init__(
        self,
        *,
        rules: RuleCatalog | None = None,
        schema_validator: SchemaValidator | None = None,
        normalizer: EventNormalizer | None = None,
        spam_scorer: SpamScorer | None = None,
        trust_scorer: SourceTrustScorer | None = None,
        freshness_scorer: FreshnessScorer | None = None,
        completeness_scorer: CompletenessScorer | None = None,
        entity_scorer: EntityConfidenceScorer | None = None,
        duplicate_scorer: DuplicateScorer | None = None,
        quality_scorer: QualityScoreCombiner | None = None,
        timer: PipelineTimer | None = None,
    ) -> None:
        self.rules = rules or default_rule_catalog()
        self.schema_validator = schema_validator or SchemaValidator()
        self.normalizer = normalizer or EventNormalizer()
        self.spam_scorer = spam_scorer or SpamScorer()
        self.trust_scorer = trust_scorer or SourceTrustScorer()
        self.freshness_scorer = freshness_scorer or FreshnessScorer()
        self.completeness_scorer = completeness_scorer or CompletenessScorer()
        self.entity_scorer = entity_scorer or EntityConfidenceScorer()
        self.duplicate_scorer = duplicate_scorer or DuplicateScorer()
        self.quality_scorer = quality_scorer or QualityScoreCombiner()
        self.timer = timer or PipelineTimer()

    def process(
        self,
        event: QualityEvent,
        *,
        source_profile: SourceQualityProfile,
        recent_hashes: set[str] | None = None,
        recent_fingerprints: list[str] | None = None,
        processed_urls: set[str] | None = None,
    ) -> QualityReportResult:
        started = time.perf_counter()
        queue_time_ms = self._queue_time_ms(event)

        schema = self.timer.time_stage(lambda: self.schema_validator.validate(event))
        normalized, normalization = self.timer.time_value(lambda: self.normalizer.normalize(event))

        spam = self.timer.time_stage(
            lambda: self.spam_scorer.score(
                normalized,
                self.rules,
                recent_fingerprints=recent_fingerprints,
            )
        )
        trust = self.timer.time_stage(lambda: self.trust_scorer.score(normalized, self.rules, source_profile))
        freshness = self.timer.time_stage(lambda: self.freshness_scorer.score(normalized, self.rules))
        completeness = self.timer.time_stage(
            lambda: self.completeness_scorer.score(normalized, self.rules)
        )
        entity = self.timer.time_stage(lambda: self.entity_scorer.score(normalized))
        duplicate = self.timer.time_stage(
            lambda: self.duplicate_scorer.score(
                normalized,
                known_hashes=recent_hashes,
                known_fingerprints=recent_fingerprints,
                processed_urls=processed_urls,
            )
        )

        stage_results = [
            schema,
            normalization,
            spam,
            trust,
            freshness,
            completeness,
            entity,
            duplicate,
        ]
        quality = self.timer.time_stage(lambda: self.quality_scorer.combine(stage_results, self.rules))
        decision = QualityDecision(str(quality.details["decision"]))
        grade = QualityGrade(str(quality.details["grade"]))
        all_results = [*stage_results, quality]
        reason_codes = sorted({code for result in all_results for code in result.reason_codes})

        return QualityReportResult(
            event_id=event.id,
            source=normalized.source,
            decision=decision,
            grade=grade,
            schema_score=schema.score,
            spam_score=spam.score,
            trust_score=trust.score,
            freshness_score=freshness.score,
            completeness_score=completeness.score,
            entity_confidence_score=entity.score,
            duplicate_probability=duplicate.score,
            overall_quality_score=quality.score,
            processing_time_ms=round((time.perf_counter() - started) * 1000, 4),
            queue_time_ms=queue_time_ms,
            reason_codes=reason_codes,
            stage_results=all_results,
            normalized_event=normalized,
            explanation={
                "pipeline": "quality_pipeline_v1",
                "rules": [rule.model_dump(mode="json") for rule in self.rules.enabled()],
                "stage_count": len(all_results),
            },
        )

    def _queue_time_ms(self, event: QualityEvent) -> float | None:
        if event.collected_at is None:
            return None
        collected = event.collected_at if event.collected_at.tzinfo else event.collected_at.replace(tzinfo=UTC)
        return round(max(0.0, (datetime.now(UTC) - collected.astimezone(UTC)).total_seconds() * 1000), 4)
