from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import DatabaseDep
from app.models.improvement import (
    CollectorPerformance,
    ExperimentRun,
    OpportunityAccuracy,
    QualityRulePerformance,
    WeightAdjustment,
)
from app.repositories.improvement import ImprovementRepository
from app.schemas.improvement import (
    CollectorPerformanceListResponse,
    CollectorPerformanceResponse,
    ExperimentListResponse,
    ExperimentRunResponse,
    ImprovementOverviewResponse,
    OpportunityAccuracyListResponse,
    OpportunityAccuracyResponse,
    OptimizationRecommendationListResponse,
    OptimizationRecommendationResponse,
    RulePerformanceListResponse,
    RulePerformanceResponse,
)
from app.services.improvement import ImprovementService

router = APIRouter(prefix="/improvement", tags=["improvement"])


def get_improvement_service(database: DatabaseDep) -> ImprovementService:
    return ImprovementService(ImprovementRepository(database))


ImprovementServiceDep = Annotated[ImprovementService, Depends(get_improvement_service)]


@router.get("/overview", response_model=ImprovementOverviewResponse)
async def improvement_overview(service: ImprovementServiceDep) -> ImprovementOverviewResponse:
    return ImprovementOverviewResponse(overview=await service.overview())


@router.get("/collectors", response_model=CollectorPerformanceListResponse)
async def improvement_collectors(service: ImprovementServiceDep) -> CollectorPerformanceListResponse:
    return CollectorPerformanceListResponse(
        collectors=[_collector_response(item) for item in await service.collectors()]
    )


@router.get("/rules", response_model=RulePerformanceListResponse)
async def improvement_rules(service: ImprovementServiceDep) -> RulePerformanceListResponse:
    return RulePerformanceListResponse(rules=[_rule_response(item) for item in await service.rules()])


@router.get("/opportunities", response_model=OpportunityAccuracyListResponse)
async def improvement_opportunities(service: ImprovementServiceDep) -> OpportunityAccuracyListResponse:
    return OpportunityAccuracyListResponse(
        opportunities=[_opportunity_response(item) for item in await service.opportunities()]
    )


@router.get("/experiments", response_model=ExperimentListResponse)
async def improvement_experiments(service: ImprovementServiceDep) -> ExperimentListResponse:
    return ExperimentListResponse(experiments=[_experiment_response(item) for item in await service.experiments()])


@router.get("/recommendations", response_model=OptimizationRecommendationListResponse)
async def improvement_recommendations(service: ImprovementServiceDep) -> OptimizationRecommendationListResponse:
    return OptimizationRecommendationListResponse(
        recommendations=[_recommendation_response(item) for item in await service.recommendations()]
    )


def _collector_response(item: CollectorPerformance) -> CollectorPerformanceResponse:
    return CollectorPerformanceResponse(
        id=item.id,
        collector=item.collector,
        precision=item.precision,
        recall=item.recall,
        spam_rate=item.spam_rate,
        duplicate_rate=item.duplicate_rate,
        conversion_rate=item.conversion_rate,
        average_quality=item.average_quality,
        average_confidence=item.average_confidence,
        latency_ms=item.latency_ms,
        ranking=item.ranking,
        details=item.details,
        created_at=item.created_at,
    )


def _rule_response(item: QualityRulePerformance) -> RulePerformanceResponse:
    return RulePerformanceResponse(
        id=item.id,
        rule_key=item.rule_key,
        times_fired=item.times_fired,
        correct_decisions=item.correct_decisions,
        incorrect_decisions=item.incorrect_decisions,
        override_rate=item.override_rate,
        confidence=item.confidence,
        historical_trend=item.historical_trend,
        created_at=item.created_at,
    )


def _opportunity_response(item: OpportunityAccuracy) -> OpportunityAccuracyResponse:
    return OpportunityAccuracyResponse(
        id=item.id,
        opportunity_id=item.opportunity_id,
        predicted_score=item.predicted_score,
        actual_outcome_score=item.actual_outcome_score,
        prediction_error=item.prediction_error,
        outcome_label=item.outcome_label,
        created_at=item.created_at,
    )


def _experiment_response(item: ExperimentRun) -> ExperimentRunResponse:
    return ExperimentRunResponse(
        id=item.id,
        experiment_key=item.experiment_key,
        name=item.name,
        area=item.area,
        variant_a=item.variant_a,
        variant_b=item.variant_b,
        hypothesis=item.hypothesis,
        status=item.status,
        created_at=item.created_at,
    )


def _recommendation_response(item: WeightAdjustment) -> OptimizationRecommendationResponse:
    return OptimizationRecommendationResponse(
        id=item.id,
        target_type=item.target_type,
        target_key=item.target_key,
        current_weight=item.current_weight,
        recommended_weight=item.recommended_weight,
        recommendation=item.recommendation,
        reason=item.reason,
        confidence=item.confidence,
        requires_approval=item.requires_approval,
        created_at=item.created_at,
    )
