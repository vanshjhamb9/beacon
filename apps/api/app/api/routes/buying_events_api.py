"""Buying Events API routes - serves data from buying_events table to dashboard."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import DatabaseDep
from app.db.session import AsyncSessionLocal
from app.models.buying_event import (
    BuyingEvent,
    BuyingEventClassification,
    BuyingEventDepartment,
    BuyingEventStatus,
    ContactType,
    FreshnessStatus,
)

router = APIRouter(prefix="/buying-events", tags=["Buying Events"])


class SendEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str


class SendBulkEmailRequest(BaseModel):
    event_ids: list[str] | None = None  # None = send to all with email
    subject_template: str | None = None
    body_template: str | None = None
    custom_subject: str | None = None
    custom_body: str | None = None


class UpdateEventRequest(BaseModel):
    status: str | None = None
    classification: str | None = None


@router.get("")
async def list_buying_events(
    database: DatabaseDep,
    department: str | None = None,
    classification: str | None = None,
    status: str | None = None,
    freshness: str | None = None,
    contact_type: str | None = None,
    search: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List buying events from the buying_events table."""
    query = select(BuyingEvent)
    count_query = select(func.count(BuyingEvent.id))
    
    filters = []
    if department:
        filters.append(BuyingEvent.department == department)
    if classification:
        filters.append(BuyingEvent.classification == classification)
    if status:
        filters.append(BuyingEvent.status == status)
    if freshness:
        filters.append(BuyingEvent.freshness == freshness)
    if contact_type:
        filters.append(BuyingEvent.contact_type == contact_type)
    if search:
        filters.append(
            or_(
                BuyingEvent.company_name.ilike(f"%{search}%"),
                BuyingEvent.company_domain.ilike(f"%{search}%"),
            )
        )
    
    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
    
    # Get total count
    total_result = await database.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get items
    query = query.order_by(BuyingEvent.created_at.desc()).offset(offset).limit(limit)
    result = await database.execute(query)
    events = result.scalars().all()
    
    return {
        "items": [
            {
                "id": str(event.id),
                "company_name": event.company_name,
                "company_domain": event.company_domain,
                "department": event.department.value if event.department else None,
                "classification": event.classification.value if event.classification else None,
                "status": event.status.value if event.status else None,
                "freshness": event.freshness.value if event.freshness else None,
                "confidence": event.confidence,
                "score": event.confidence * 100,
                "contact_type": event.contact_type.value if event.contact_type else None,
                "problem": event.problem,
                "why_now": event.why_now,
                "solution_match": event.solution_match,
                "outreach_reason": event.outreach_reason,
                "industry": None,  # Will be enriched later
                "country": None,  # Will be enriched later
                "source": event.raw_event_id,
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "contact_info": event.contact_info or {},
                "evidence": event.evidence or [],
            }
            for event in events
        ],
        "total": total,
    }


@router.get("/stats")
async def buying_events_stats(database: DatabaseDep):
    """Get statistics about buying events."""
    # Total count
    total_result = await database.execute(select(func.count(BuyingEvent.id)))
    total = total_result.scalar() or 0
    
    # By department
    dept_result = await database.execute(
        select(BuyingEvent.department, func.count(BuyingEvent.id)).group_by(BuyingEvent.department)
    )
    by_department = {row[0].value: row[1] for row in dept_result.all()}
    
    # By classification
    class_result = await database.execute(
        select(BuyingEvent.classification, func.count(BuyingEvent.id)).group_by(BuyingEvent.classification)
    )
    by_classification = {row[0].value: row[1] for row in class_result.all()}
    
    # By status
    status_result = await database.execute(
        select(BuyingEvent.status, func.count(BuyingEvent.id)).group_by(BuyingEvent.status)
    )
    by_status = {row[0].value: row[1] for row in status_result.all()}
    
    # By freshness
    fresh_result = await database.execute(
        select(BuyingEvent.freshness, func.count(BuyingEvent.id)).group_by(BuyingEvent.freshness)
    )
    by_freshness = {row[0].value: row[1] for row in fresh_result.all()}
    
    # By contact type
    contact_result = await database.execute(
        select(BuyingEvent.contact_type, func.count(BuyingEvent.id)).group_by(BuyingEvent.contact_type)
    )
    by_contact_type = {row[0].value: row[1] for row in contact_result.all()}
    
    return {
        "total": total,
        "by_department": by_department,
        "by_classification": by_classification,
        "by_status": by_status,
        "by_freshness": by_freshness,
        "by_contact_type": by_contact_type,
    }


@router.get("/{event_id}")
async def get_buying_event(event_id: UUID, database: DatabaseDep):
    """Get a single buying event by ID."""
    result = await database.execute(
        select(BuyingEvent).where(BuyingEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Buying event not found")
    
    return {
        "id": str(event.id),
        "company_name": event.company_name,
        "company_domain": event.company_domain,
        "department": event.department.value if event.department else None,
        "classification": event.classification.value if event.classification else None,
        "status": event.status.value if event.status else None,
        "freshness": event.freshness.value if event.freshness else None,
        "confidence": event.confidence,
        "score": event.confidence * 100,
        "contact_type": event.contact_type.value if event.contact_type else None,
        "problem": event.problem,
        "why_now": event.why_now,
        "solution_match": event.solution_match,
        "outreach_reason": event.outreach_reason,
        "industry": None,
        "country": None,
        "source": event.raw_event_id,
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "contact_info": event.contact_info or {},
        "evidence": event.evidence or [],
        "pain_signals": event.pain_signals or [],
        "buying_signals": event.buying_signals or [],
        "partner_signals": event.partner_signals or [],
        "outreach_preparation": event.outreach_preparation or {},
        "cto_test_result": event.cto_test_result,
    }


@router.get("/intent")
async def buying_intent(database: DatabaseDep):
    """Get buying intent signals summary."""
    # Recent high-confidence events
    result = await database.execute(
        select(BuyingEvent)
        .where(BuyingEvent.confidence >= 0.7)
        .order_by(BuyingEvent.created_at.desc())
        .limit(20)
    )
    events = result.scalars().all()
    
    # Group by industry (using solution_match as proxy)
    by_service = {}
    for event in events:
        service = event.solution_match or "Unknown"
        if service not in by_service:
            by_service[service] = []
        by_service[service].append({
            "company_name": event.company_name,
            "confidence": event.confidence,
            "problem": event.problem,
        })
    
    return {
        "total_high_intent": len(events),
        "by_service": by_service,
        "top_signals": [
            {
                "type": event.classification.value if event.classification else "unknown",
                "company": event.company_name,
                "confidence": event.confidence,
                "problem": event.problem,
            }
            for event in events[:10]
        ],
    }


@router.get("/pipeline")
async def opportunities_pipeline(database: DatabaseDep):
    """Get opportunities pipeline data."""
    # Group by classification
    result = await database.execute(
        select(BuyingEvent.classification, func.count(BuyingEvent.id))
        .where(BuyingEvent.status == BuyingEventStatus.VERIFIED)
        .group_by(BuyingEvent.classification)
    )
    pipeline = {row[0].value: row[1] for row in result.all()}
    
    # Total pipeline value (using confidence as proxy)
    total_result = await database.execute(
        select(func.sum(BuyingEvent.confidence * 10000))
        .where(BuyingEvent.status == BuyingEventStatus.VERIFIED)
    )
    total_value = total_result.scalar() or 0
    
    return {
        "pipeline": pipeline,
        "total_value": total_value,
        "total_opportunities": sum(pipeline.values()),
    }


@router.post("/{event_id}/send-email")
async def send_email_to_lead(event_id: UUID, database: DatabaseDep, request: SendEmailRequest):
    """Send a single email to a lead."""
    from email_service import send_email
    
    result = await database.execute(
        select(BuyingEvent).where(BuyingEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Buying event not found")
    
    email_result = send_email(
        to_email=request.to_email,
        subject=request.subject,
        body_html=request.body,
    )
    
    return email_result


@router.post("/send-bulk")
async def send_bulk_emails(database: DatabaseDep, request: SendBulkEmailRequest):
    """Send emails to multiple leads (one click)."""
    from email_service import send_bulk_emails, generate_outreach_email
    
    # Build query
    query = select(BuyingEvent)
    
    if request.event_ids:
        # Send to specific events
        uuid_ids = [UUID(eid) for eid in request.event_ids]
        query = query.where(BuyingEvent.id.in_(uuid_ids))
    else:
        # Send to all events with email contact
        query = query.where(
            BuyingEvent.contact_info["email"].isnot(None),
            BuyingEvent.contact_info["email"] != "",
        )
    
    result = await database.execute(query)
    events = result.scalars().all()
    
    if not events:
        return {"total": 0, "success": 0, "failed": 0, "message": "No events with email found"}
    
    # Build recipients list
    recipients = []
    for event in events:
        contact_info = event.contact_info or {}
        email = contact_info.get("email")
        
        if not email:
            continue
        
        # Generate personalized email
        if request.custom_subject and request.custom_body:
            subject = request.custom_subject
            body = request.custom_body
            # Personalize
            for placeholder, value in [
                ("{company_name}", event.company_name),
                ("{problem}", event.problem or "your current challenges"),
                ("{solution_match}", event.solution_match or "our solutions"),
            ]:
                subject = subject.replace(placeholder, str(value))
                body = body.replace(placeholder, str(value))
        else:
            email_content = generate_outreach_email(
                company_name=event.company_name,
                problem=event.problem,
                solution_match=event.solution_match,
                evidence=event.evidence if isinstance(event.evidence, list) else [],
            )
            subject = email_content["subject"]
            body = email_content["body"]
        
        recipients.append({
            "email": email,
            "company_name": event.company_name,
            "subject": subject,
            "body": body,
        })
    
    if not recipients:
        return {"total": 0, "success": 0, "failed": 0, "message": "No valid email addresses found"}
    
    # Send bulk emails
    email_results = send_bulk_emails(
        recipients=recipients,
        subject_template=recipients[0]["subject"],
        body_template=recipients[0]["body"],
    )
    
    return email_results


@router.post("/{event_id}/update")
async def update_buying_event(event_id: UUID, database: DatabaseDep, request: UpdateEventRequest):
    """Update a buying event's status or classification."""
    result = await database.execute(
        select(BuyingEvent).where(BuyingEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Buying event not found")
    
    if request.status:
        event.status = BuyingEventStatus(request.status)
    if request.classification:
        event.classification = BuyingEventClassification(request.classification)
    
    await database.commit()
    
    return {
        "id": str(event.id),
        "status": event.status.value,
        "classification": event.classification.value,
    }


@router.post("/{event_id}/delete")
async def delete_buying_event(event_id: UUID, database: DatabaseDep):
    """Delete a buying event."""
    result = await database.execute(
        select(BuyingEvent).where(BuyingEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Buying event not found")
    
    await database.delete(event)
    await database.commit()
    
    return {"deleted": True, "id": str(event_id)}


# --- Contact Enrichment Endpoints ---

class EnrichAllResponse(BaseModel):
    total: int
    enriched: int
    failed: int
    skipped: int
    results: list[dict] | None = None


@router.post("/enrich-all")
async def enrich_all_buying_events(database: DatabaseDep):
    """Trigger enrichment for all buying events missing contact info."""
    from celery import Celery
    from app.core.config import get_settings

    settings = get_settings()
    celery = Celery("beacon_worker", broker=settings.celery_broker_url)
    task = celery.send_task("buying_events.enrich_contacts")
    return {
        "task_id": task.id,
        "status": "enrichment_started",
        "message": "Enrichment task queued. Check /buying-events/enrichment-status/{task_id} for progress.",
    }


@router.get("/enrichment-status/{task_id}")
async def get_enrichment_status(task_id: str):
    """Check status of an enrichment task. Returns enrichment stats from DB."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import func

        total_result = await session.execute(
            select(func.count(BuyingEvent.id))
        )
        total_events = total_result.scalar()

        enriched_result = await session.execute(
            select(func.count(BuyingEvent.id)).where(
                BuyingEvent.contact_info["email"].isnot(None),
                BuyingEvent.contact_info["email"].astext != "",
                BuyingEvent.contact_info["email"].astext != "null",
            )
        )
        enriched_count = enriched_result.scalar()

        return {
            "task_id": task_id,
            "status": "completed",
            "total_events": total_events,
            "enriched_events": enriched_count,
            "pending_events": total_events - enriched_count,
            "enrichment_rate": round(enriched_count / total_events * 100, 1) if total_events > 0 else 0,
        }


@router.post("/{event_id}/enrich")
async def enrich_single_buying_event(event_id: UUID, database: DatabaseDep):
    """Enrich a single buying event with contact information."""
    result = await database.execute(
        select(BuyingEvent).where(BuyingEvent.id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Buying event not found")

    if not event.company_domain:
        raise HTTPException(status_code=400, detail="No company domain available for enrichment")

    from celery import Celery
    from app.core.config import get_settings

    settings = get_settings()
    celery = Celery("beacon_worker", broker=settings.celery_broker_url)
    task = celery.send_task("buying_events.enrich_single", args=[str(event_id)])
    return {
        "task_id": task.id,
        "status": "enrichment_started",
        "company": event.company_name,
        "domain": event.company_domain,
    }


@router.get("/{event_id}/enrichment-status")
async def get_event_enrichment_status(event_id: UUID, database: DatabaseDep):
    """Get enrichment status for a specific buying event."""
    result = await database.execute(
        select(BuyingEvent).where(BuyingEvent.id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Buying event not found")

    contact_info = event.contact_info or {}
    has_email = bool(contact_info.get("email") and contact_info["email"] != "null")
    has_phone = bool(contact_info.get("phone"))
    has_linkedin = bool(contact_info.get("linkedin"))
    has_founder = bool(contact_info.get("founder_name"))

    return {
        "event_id": str(event.id),
        "company": event.company_name,
        "domain": event.company_domain,
        "enrichment_status": "enriched" if has_email else "pending",
        "has_email": has_email,
        "has_phone": has_phone,
        "has_linkedin": has_linkedin,
        "has_founder": has_founder,
        "contact_info": contact_info,
        "contact_type": event.contact_type.value if event.contact_type else None,
    }
