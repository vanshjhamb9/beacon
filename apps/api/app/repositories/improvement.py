from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.context import ContextFeedback
from app.models.improvement import (
    ClassifierPerformance,
    CollectorPerformance,
    FeedbackEvent,
    ExperimentRun,
    LearningEvent,
    OpportunityAccuracy,
    QualityRulePerformance,
    WeightAdjustment,
)
from app.models.opportunity import Opportunity, OpportunityFeedback, OpportunityMetric
from app.models.outcomes import OpportunityOutcome
from app.models.quality import QualityFeedback, QualityReport
from intelligence_improvement.models import (
    FeedbackSignal,
    FeedbackSource,
    ImprovementArea,
    ImprovementReport,
    PredictionEvaluation,
)
from outcome_intelligence.metrics.lifecycle import outcome_score


class ImprovementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def feedback_signals(self, *, limit: int = 1000) -> list[FeedbackSignal]:
        signals: list[FeedbackSignal] = []
        signals.extend(await self._quality_feedback(limit=limit))
        signals.extend(await self._context_feedback(limit=limit))
        signals.extend(await self._opportunity_feedback(limit=limit))
        signals.extend(await self._outcome_lifecycle_feedback(limit=limit))
        signals.extend(await self._collector_feedback(limit=limit))
        return signals

    async def quality_rule_feedback(self, *, limit: int = 1000) -> list[FeedbackSignal]:
        result = await self.session.execute(
            select(QualityFeedback, QualityReport)
            .join(QualityReport, QualityReport.id == QualityFeedback.quality_report_id)
            .order_by(QualityFeedback.created_at.desc())
            .limit(limit)
        )
        signals: list[FeedbackSignal] = []
        for feedback, report in result.all():
            reason_codes = feedback.corrected_reason_codes or report.reason_codes or ["quality.default"]
            for reason in reason_codes:
                signals.append(
                    FeedbackSignal(
                        source=FeedbackSource.HUMAN_REVIEW,
                        area=ImprovementArea.QUALITY_RULE,
                        entity_id=feedback.quality_report_id,
                        entity_key=str(reason),
                        outcome=feedback.review_outcome,
                        score=report.overall_quality_score,
                        occurred_at=feedback.created_at,
                        details={"decision": report.decision, "corrected_decision": feedback.corrected_decision},
                    )
                )
        return signals

    async def classifier_feedback(self, *, limit: int = 1000) -> list[FeedbackSignal]:
        result = await self.session.execute(
            select(ContextFeedback)
            .order_by(ContextFeedback.created_at.desc())
            .limit(limit)
        )
        return [
            FeedbackSignal(
                source=FeedbackSource.MANUAL_CORRECTION,
                area=ImprovementArea.CLASSIFIER,
                entity_id=item.business_context_id,
                entity_key=str(item.corrected_fields.get("category", "context.classifier")),
                outcome=item.review_outcome,
                score=100.0 if item.review_outcome in {"accepted", "correct"} else 0.0,
                occurred_at=item.created_at,
                details={"corrected_fields": item.corrected_fields, "ground_truth": item.ground_truth},
            )
            for item in result.scalars().all()
        ]

    async def prediction_evaluations(self, *, limit: int = 1000) -> list[PredictionEvaluation]:
        evaluations: list[PredictionEvaluation] = []
        result = await self.session.execute(
            select(OpportunityFeedback, Opportunity)
            .join(Opportunity, Opportunity.id == OpportunityFeedback.opportunity_id)
            .order_by(OpportunityFeedback.created_at.desc())
            .limit(limit)
        )
        for feedback, opportunity in result.all():
            actual = self._outcome_score(feedback.outcome_label or feedback.review_outcome)
            evaluations.append(
                PredictionEvaluation(
                    opportunity_id=opportunity.id,
                    predicted_score=opportunity.opportunity_score,
                    actual_outcome_score=actual,
                    prediction_error=opportunity.opportunity_score - actual,
                    outcome_label=feedback.outcome_label or feedback.review_outcome,
                )
            )

        outcome_result = await self.session.execute(
            select(OpportunityOutcome).order_by(OpportunityOutcome.updated_at.desc()).limit(limit)
        )
        for outcome in outcome_result.scalars().all():
            actual = outcome_score(outcome.lifecycle_stage)
            evaluations.append(
                PredictionEvaluation(
                    opportunity_id=outcome.opportunity_id,
                    predicted_score=outcome.opportunity_score,
                    actual_outcome_score=actual,
                    prediction_error=outcome.opportunity_score - actual,
                    outcome_label=outcome.lifecycle_stage,
                )
            )
        return evaluations

    async def store_report(self, report: ImprovementReport) -> None:
        for metric in report.collector_rankings:
            self.session.add(
                CollectorPerformance(
                    collector=metric.entity_key,
                    precision=metric.precision,
                    recall=metric.recall,
                    spam_rate=0.0,
                    duplicate_rate=0.0,
                    conversion_rate=metric.conversion_rate,
                    average_quality=metric.average_confidence,
                    average_confidence=metric.average_confidence,
                    latency_ms=metric.average_latency_ms,
                    ranking=report.collector_rankings.index(metric) + 1,
                    details={"trend": metric.trend, "sample_size": metric.sample_size},
                )
            )
        for metric in report.rule_rankings:
            if metric.rule_type == "quality":
                self.session.add(
                    QualityRulePerformance(
                        rule_key=metric.rule_key,
                        times_fired=metric.times_fired,
                        correct_decisions=metric.correct_decisions,
                        incorrect_decisions=metric.incorrect_decisions,
                        override_rate=metric.override_rate,
                        confidence=metric.confidence,
                        historical_trend=metric.historical_trend,
                    )
                )
            else:
                self.session.add(
                    ClassifierPerformance(
                        rule_key=metric.rule_key,
                        category=metric.rule_key,
                        times_fired=metric.times_fired,
                        correct_decisions=metric.correct_decisions,
                        incorrect_decisions=metric.incorrect_decisions,
                        confidence=metric.confidence,
                        historical_trend=metric.historical_trend,
                    )
                )
        for recommendation in report.recommendations:
            self.session.add(
                WeightAdjustment(
                    target_type=recommendation.area.value,
                    target_key=recommendation.target_key,
                    current_weight=None,
                    recommended_weight=None,
                    recommendation=recommendation.recommendation,
                    reason=recommendation.reason,
                    confidence=recommendation.confidence,
                    requires_approval=str(recommendation.requires_approval).lower(),
                )
            )
        for key, value in report.opportunity_accuracy.items():
            if isinstance(value, int | float):
                self.session.add(
                    LearningEvent(
                        event_type="opportunity_accuracy_metric",
                        area=ImprovementArea.OPPORTUNITY.value,
                        entity_key=str(key),
                        entity_id=None,
                        outcome="measured",
                        score=float(value),
                        details=report.opportunity_accuracy,
                    )
                )
        await self.session.flush()

    async def store_prediction_evaluations(self, predictions: list[PredictionEvaluation]) -> None:
        for prediction in predictions:
            self.session.add(
                OpportunityAccuracy(
                    opportunity_id=prediction.opportunity_id,
                    predicted_score=prediction.predicted_score,
                    actual_outcome_score=prediction.actual_outcome_score,
                    prediction_error=prediction.prediction_error,
                    outcome_label=prediction.outcome_label,
                )
            )
        await self.session.flush()

    async def overview(self) -> dict[str, float | int | str]:
        since = datetime.now(UTC) - timedelta(days=1)
        feedback_count = await self._count(FeedbackEvent)
        recommendation_count = await self._count(WeightAdjustment)
        learning_count = await self._count(LearningEvent)
        latency_result = await self.session.execute(
            select(func.avg(OpportunityMetric.metric_value)).where(
                OpportunityMetric.metric_name == "scoring_latency_ms",
                OpportunityMetric.created_at >= since,
            )
        )
        return {
            "window": "24h",
            "learning_events": learning_count,
            "feedback_events": feedback_count,
            "optimization_recommendations": recommendation_count,
            "average_scoring_latency_ms": round(float(latency_result.scalar_one() or 0.0), 4),
        }

    async def collectors(self) -> Sequence[CollectorPerformance]:
        result = await self.session.execute(
            select(CollectorPerformance).order_by(CollectorPerformance.ranking, CollectorPerformance.created_at.desc())
        )
        return result.scalars().all()

    async def rules(self) -> Sequence[QualityRulePerformance]:
        result = await self.session.execute(
            select(QualityRulePerformance).order_by(QualityRulePerformance.confidence.desc())
        )
        return result.scalars().all()

    async def opportunities(self) -> Sequence[OpportunityAccuracy]:
        result = await self.session.execute(
            select(OpportunityAccuracy).order_by(OpportunityAccuracy.created_at.desc())
        )
        return result.scalars().all()

    async def recommendations(self) -> Sequence[WeightAdjustment]:
        result = await self.session.execute(
            select(WeightAdjustment).order_by(WeightAdjustment.created_at.desc())
        )
        return result.scalars().all()

    async def experiments(self) -> Sequence[ExperimentRun]:
        result = await self.session.execute(
            select(ExperimentRun).order_by(ExperimentRun.created_at.desc())
        )
        return result.scalars().all()

    async def _quality_feedback(self, *, limit: int) -> list[FeedbackSignal]:
        result = await self.session.execute(
            select(QualityFeedback, QualityReport)
            .join(QualityReport, QualityReport.id == QualityFeedback.quality_report_id)
            .order_by(QualityFeedback.created_at.desc())
            .limit(limit)
        )
        return [
            FeedbackSignal(
                source=FeedbackSource.HUMAN_REVIEW,
                area=ImprovementArea.QUALITY_RULE,
                entity_id=feedback.quality_report_id,
                entity_key=report.source,
                outcome=feedback.review_outcome,
                score=report.overall_quality_score,
                occurred_at=feedback.created_at,
                details={"source": report.source, "latency_ms": report.processing_time_ms},
            )
            for feedback, report in result.all()
        ]

    async def _context_feedback(self, *, limit: int) -> list[FeedbackSignal]:
        result = await self.session.execute(
            select(ContextFeedback).order_by(ContextFeedback.created_at.desc()).limit(limit)
        )
        return [
            FeedbackSignal(
                source=FeedbackSource.MANUAL_CORRECTION,
                area=ImprovementArea.CONTEXT,
                entity_id=item.business_context_id,
                entity_key="context_accuracy",
                outcome=item.review_outcome,
                score=100.0 if item.review_outcome in {"accepted", "correct"} else 0.0,
                occurred_at=item.created_at,
                details={"corrected_fields": item.corrected_fields, "ground_truth": item.ground_truth},
            )
            for item in result.scalars().all()
        ]

    async def _opportunity_feedback(self, *, limit: int) -> list[FeedbackSignal]:
        result = await self.session.execute(
            select(OpportunityFeedback, Opportunity)
            .join(Opportunity, Opportunity.id == OpportunityFeedback.opportunity_id)
            .order_by(OpportunityFeedback.created_at.desc())
            .limit(limit)
        )
        return [
            FeedbackSignal(
                source=self._feedback_source(feedback.outcome_label or feedback.review_outcome),
                area=ImprovementArea.OPPORTUNITY,
                entity_id=feedback.opportunity_id,
                entity_key=opportunity.recommendation,
                outcome=feedback.outcome_label or feedback.review_outcome,
                score=opportunity.opportunity_score,
                occurred_at=feedback.created_at,
                details={"status": opportunity.status, "recommendation": opportunity.recommendation},
            )
            for feedback, opportunity in result.all()
        ]

    async def _outcome_lifecycle_feedback(self, *, limit: int) -> list[FeedbackSignal]:
        result = await self.session.execute(
            select(OpportunityOutcome).order_by(OpportunityOutcome.updated_at.desc()).limit(limit)
        )
        signals: list[FeedbackSignal] = []
        for outcome in result.scalars().all():
            area = ImprovementArea.OPPORTUNITY
            entity_key = outcome.recommended_service or outcome.collector or "outcome"
            if outcome.recommended_service:
                area = ImprovementArea.RECOMMENDATION
                entity_key = outcome.recommended_service
            elif outcome.collector:
                area = ImprovementArea.COLLECTOR
                entity_key = outcome.collector
            signals.append(
                FeedbackSignal(
                    source=self._feedback_source(outcome.lifecycle_stage),
                    area=area,
                    entity_id=outcome.opportunity_id,
                    entity_key=entity_key,
                    outcome=outcome.lifecycle_stage,
                    score=outcome_score(outcome.lifecycle_stage),
                    occurred_at=outcome.updated_at,
                    details={
                        "opportunity_score": outcome.opportunity_score,
                        "revenue": outcome.revenue,
                        "industry": outcome.industry,
                        "buyer_persona": outcome.buyer_persona,
                        "collector": outcome.collector,
                        "technology": outcome.technology,
                    },
                )
            )
        return signals

    async def _collector_feedback(self, *, limit: int) -> list[FeedbackSignal]:
        result = await self.session.execute(
            select(QualityReport)
            .order_by(QualityReport.created_at.desc())
            .limit(limit)
        )
        return [
            FeedbackSignal(
                source=FeedbackSource.HUMAN_REVIEW,
                area=ImprovementArea.COLLECTOR,
                entity_id=report.raw_event_id,
                entity_key=report.source,
                outcome="accepted" if report.decision == "accept" else "rejected",
                score=report.overall_quality_score,
                occurred_at=report.created_at,
                details={"latency_ms": report.processing_time_ms, "spam_score": report.spam_score},
            )
            for report in result.scalars().all()
        ]

    async def _count(self, model: type[Any]) -> int:
        result = await self.session.execute(select(func.count(model.id)))
        return int(result.scalar_one() or 0)

    def _outcome_score(self, outcome: str) -> float:
        mapped = {
            "won": 100.0,
            "proposal_sent": 80.0,
            "meeting_booked": 75.0,
            "meeting_scheduled": 60.0,
            "accepted": 70.0,
            "correct": 70.0,
            "lost": 0.0,
            "rejected": 0.0,
            "false_positive": 0.0,
            "archived": 0.0,
        }
        if outcome in mapped:
            return mapped[outcome]
        return outcome_score(outcome)

    def _feedback_source(self, outcome: str) -> FeedbackSource:
        return {
            "won": FeedbackSource.WON,
            "lost": FeedbackSource.LOST,
            "meeting_booked": FeedbackSource.MEETING_BOOKED,
            "meeting_scheduled": FeedbackSource.MEETING_BOOKED,
            "proposal_sent": FeedbackSource.PROPOSAL_SENT,
            "false_positive": FeedbackSource.FALSE_POSITIVE,
            "false_negative": FeedbackSource.FALSE_NEGATIVE,
            "accepted": FeedbackSource.OPPORTUNITY_ACCEPTED,
            "rejected": FeedbackSource.OPPORTUNITY_REJECTED,
        }.get(outcome, FeedbackSource.HUMAN_REVIEW)
