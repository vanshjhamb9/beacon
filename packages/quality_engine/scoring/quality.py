from quality_engine.models.types import QualityDecision, QualityGrade, QualityStage, StageResult
from quality_engine.rules.definitions import RuleCatalog


class QualityScoreCombiner:
    WEIGHTS: dict[QualityStage, float] = {
        QualityStage.SCHEMA: 0.12,
        QualityStage.SPAM: 0.16,
        QualityStage.SOURCE_TRUST: 0.16,
        QualityStage.FRESHNESS: 0.12,
        QualityStage.COMPLETENESS: 0.14,
        QualityStage.ENTITY_CONFIDENCE: 0.14,
        QualityStage.DUPLICATE: 0.16,
    }

    def combine(self, stage_results: list[StageResult], rules: RuleCatalog) -> StageResult:
        by_stage = {result.stage: result for result in stage_results}
        weighted = 0.0
        for stage, weight in self.WEIGHTS.items():
            result = by_stage.get(stage)
            if result is None:
                continue
            contribution = 100.0 - result.score if stage in {QualityStage.SPAM, QualityStage.DUPLICATE} else result.score
            weighted += contribution * weight

        score = round(max(0.0, min(100.0, weighted)), 4)
        decision, grade = self.decision(score, rules)
        if self._hard_reject(by_stage):
            decision, grade = QualityDecision.REJECT, QualityGrade.REJECT
        reasons = [
            code
            for result in stage_results
            for code in result.reason_codes
            if code
        ]
        return StageResult(
            stage=QualityStage.QUALITY_SCORE,
            score=score,
            passed=decision != QualityDecision.REJECT,
            reason_codes=reasons,
            details={"decision": decision.value, "grade": grade.value, "weights": self.WEIGHTS},
        )

    def _hard_reject(self, by_stage: dict[QualityStage, StageResult]) -> bool:
        schema = by_stage.get(QualityStage.SCHEMA)
        spam = by_stage.get(QualityStage.SPAM)
        duplicate = by_stage.get(QualityStage.DUPLICATE)
        freshness = by_stage.get(QualityStage.FRESHNESS)
        return bool(
            (schema is not None and not schema.passed)
            or (spam is not None and spam.score >= 75.0)
            or (duplicate is not None and duplicate.score >= 95.0)
            or (freshness is not None and not freshness.passed)
        )

    def decision(self, score: float, rules: RuleCatalog) -> tuple[QualityDecision, QualityGrade]:
        rule = rules.by_key("score.acceptance")
        threshold = rule.threshold if rule else 72.0
        review_threshold = float((rule.parameters if rule else {}).get("review_threshold", 55))
        reject_threshold = float((rule.parameters if rule else {}).get("reject_threshold", 45))
        if score >= 94:
            return QualityDecision.ACCEPT, QualityGrade.A_PLUS
        if score >= 86:
            return QualityDecision.ACCEPT, QualityGrade.A
        if score >= threshold:
            return QualityDecision.ACCEPT, QualityGrade.B
        if score >= review_threshold:
            return QualityDecision.REVIEW, QualityGrade.C
        if score >= reject_threshold:
            return QualityDecision.REJECT, QualityGrade.D
        return QualityDecision.REJECT, QualityGrade.REJECT
