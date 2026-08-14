from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import DatabaseDep
from app.models.intelligence import ClassifiedSignal, Company
from app.repositories.intelligence import IntelligenceRepository
from app.schemas.intelligence import (
    ClassifiedSignalResponse,
    ClassifiedSignalsResponse,
    CompaniesResponse,
    CompanyResponse,
    CompanyTimelineResponse,
    KnowledgeGraphEdgeResponse,
    KnowledgeGraphNodeResponse,
    KnowledgeGraphResponse,
    TimelineItemResponse,
)
from app.services.intelligence import IntelligenceService

router = APIRouter(tags=["intelligence"])


def get_intelligence_service(database: DatabaseDep) -> IntelligenceService:
    return IntelligenceService(IntelligenceRepository(database))


IntelligenceServiceDep = Annotated[IntelligenceService, Depends(get_intelligence_service)]


@router.get("/companies", response_model=CompaniesResponse)
async def list_companies(
    service: IntelligenceServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> CompaniesResponse:
    companies = await service.list_companies(limit=limit, offset=offset)
    return CompaniesResponse(companies=[_company_response(company) for company in companies])


@router.get("/companies/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: UUID, service: IntelligenceServiceDep) -> CompanyResponse:
    company = await service.get_company(company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found.")
    return _company_response(company)


@router.get("/companies/{company_id}/timeline", response_model=CompanyTimelineResponse)
async def get_company_timeline(
    company_id: UUID,
    service: IntelligenceServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
) -> CompanyTimelineResponse:
    timeline = await service.company_timeline(company_id, limit=limit)
    return CompanyTimelineResponse(
        timeline=[
            TimelineItemResponse(
                id=item.id,
                timestamp=item.timestamp,
                event_id=item.event_id,
                source=item.source,
                signal_type=item.signal_type,
                summary=item.summary,
                confidence=item.confidence,
                evidence=item.evidence,
            )
            for item in timeline
        ]
    )


@router.get("/companies/{company_id}/signals", response_model=ClassifiedSignalsResponse)
async def get_company_signals(
    company_id: UUID,
    service: IntelligenceServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
) -> ClassifiedSignalsResponse:
    signals = await service.company_signals(company_id, limit=limit)
    return ClassifiedSignalsResponse(signals=[_signal_response(signal) for signal in signals])


@router.get("/signals", response_model=ClassifiedSignalsResponse)
async def list_signals(
    service: IntelligenceServiceDep,
    category: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> ClassifiedSignalsResponse:
    signals = await service.list_signals(category=category, limit=limit, offset=offset)
    return ClassifiedSignalsResponse(signals=[_signal_response(signal) for signal in signals])


@router.get("/knowledge/{node_id}", response_model=KnowledgeGraphResponse)
async def get_knowledge(node_id: UUID, service: IntelligenceServiceDep) -> KnowledgeGraphResponse:
    node, edges = await service.knowledge(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Knowledge graph node not found.")
    return KnowledgeGraphResponse(
        node=KnowledgeGraphNodeResponse(
            id=node.id,
            node_type=node.node_type,
            external_id=node.external_id,
            label=node.label,
            properties=node.properties,
        ),
        edges=[
            KnowledgeGraphEdgeResponse(
                id=edge.id,
                from_node_id=edge.from_node_id,
                to_node_id=edge.to_node_id,
                edge_type=edge.edge_type,
                confidence=edge.confidence,
                evidence_event_id=edge.evidence_event_id,
                properties=edge.properties,
            )
            for edge in edges
        ],
    )


def _company_response(company: Company) -> CompanyResponse:
    return CompanyResponse(
        id=company.id,
        name=company.name,
        normalized_name=company.normalized_name,
        primary_domain=company.primary_domain,
        industry=company.industry,
        last_seen_at=company.last_seen_at,
        signal_frequency=company.signal_frequency,
        memory_summary=company.memory_summary,
        attributes=company.attributes,
    )


def _signal_response(signal: ClassifiedSignal) -> ClassifiedSignalResponse:
    return ClassifiedSignalResponse(
        id=signal.id,
        event_id=signal.event_id,
        company_id=signal.company_id,
        category=signal.category,
        subcategory=signal.subcategory,
        confidence=signal.confidence,
        business_function=signal.business_function,
        urgency=signal.urgency,
        positive_or_negative=signal.positive_or_negative,
        source_confidence=signal.source_confidence,
        entity_confidence=signal.entity_confidence,
        classification_confidence=signal.classification_confidence,
        freshness_score=signal.freshness_score,
        reliability_score=signal.reliability_score,
        overall_confidence=signal.overall_confidence,
        confidence_explanation=signal.confidence_explanation,
        evidence=signal.evidence,
    )
