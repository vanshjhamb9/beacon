"""CSV founder/company enrichment jobs — upload → enrich → download."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enrichment", tags=["enrichment-csv"])

# In-memory job store (single-process API). Fine for operator dashboard use.
_JOBS: dict[str, dict[str, Any]] = {}
_MAX_ROWS = 100


class CSVEnrichStartRequest(BaseModel):
    csv_data: str = Field(..., min_length=10, description="Raw CSV text")
    limit: int | None = Field(default=None, ge=1, le=_MAX_ROWS)


class CSVEnrichStartResponse(BaseModel):
    job_id: str
    total: int
    warnings: list[str] = Field(default_factory=list)
    status: str = "queued"


class CSVEnrichStatusResponse(BaseModel):
    job_id: str
    status: str
    total: int
    processed: int
    summary: dict[str, Any] | None = None
    error: str | None = None
    current_company: str | None = None
    elapsed_seconds: float | None = None


def _get_helpers():
    try:
        from packages.sales_intelligence_platform.engines.csv_batch_enrichment import (
            enrich_leads_batch,
            parse_leads_csv,
            results_to_csv,
            summarize,
        )
    except ImportError:
        from sales_intelligence_platform.engines.csv_batch_enrichment import (  # type: ignore
            enrich_leads_batch,
            parse_leads_csv,
            results_to_csv,
            summarize,
        )
    return parse_leads_csv, enrich_leads_batch, results_to_csv, summarize


async def _run_job(job_id: str, leads: list[dict[str, Any]]) -> None:
    _parse, enrich_leads_batch, results_to_csv, summarize = _get_helpers()
    job = _JOBS[job_id]
    job["status"] = "running"
    job["started_at"] = time.time()

    def on_progress(i: int, total: int, last: dict[str, Any]) -> None:
        job["processed"] = i
        job["current_company"] = str(last.get("company_name") or "")

    try:
        results = await enrich_leads_batch(leads, on_progress=on_progress)
        job["results"] = results
        job["csv_data"] = results_to_csv(results)
        job["summary"] = summarize(results)
        job["processed"] = len(results)
        job["status"] = "completed"
        job["finished_at"] = time.time()
    except Exception as exc:  # noqa: BLE001
        logger.exception("CSV enrichment job %s failed", job_id)
        job["status"] = "failed"
        job["error"] = str(exc)
        job["finished_at"] = time.time()


@router.post("/csv/start", response_model=CSVEnrichStartResponse)
async def start_csv_enrichment(request: CSVEnrichStartRequest) -> CSVEnrichStartResponse:
    parse_leads_csv, *_rest = _get_helpers()
    try:
        leads, warnings = parse_leads_csv(request.csv_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if request.limit is not None:
        leads = leads[: request.limit]
    if len(leads) > _MAX_ROWS:
        leads = leads[:_MAX_ROWS]
        warnings.append(f"Truncated to {_MAX_ROWS} rows (max per job).")

    job_id = str(uuid.uuid4())
    _JOBS[job_id] = {
        "status": "queued",
        "total": len(leads),
        "processed": 0,
        "warnings": warnings,
        "results": [],
        "csv_data": None,
        "summary": None,
        "error": None,
        "current_company": None,
        "created_at": time.time(),
    }
    # Fire-and-forget background task
    asyncio.create_task(_run_job(job_id, leads))
    return CSVEnrichStartResponse(
        job_id=job_id, total=len(leads), warnings=warnings, status="queued"
    )


@router.get("/csv/status/{job_id}", response_model=CSVEnrichStatusResponse)
async def csv_enrichment_status(job_id: str) -> CSVEnrichStatusResponse:
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Enrichment job not found.")
    started = job.get("started_at") or job.get("created_at")
    elapsed = round(time.time() - started, 1) if started else None
    return CSVEnrichStatusResponse(
        job_id=job_id,
        status=str(job["status"]),
        total=int(job["total"]),
        processed=int(job["processed"]),
        summary=job.get("summary"),
        error=job.get("error"),
        current_company=job.get("current_company"),
        elapsed_seconds=elapsed,
    )


@router.get("/csv/download/{job_id}")
async def csv_enrichment_download(job_id: str) -> Response:
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Enrichment job not found.")
    if job["status"] != "completed" or not job.get("csv_data"):
        raise HTTPException(status_code=409, detail="Enrichment job is not ready for download.")
    return Response(
        content=job["csv_data"],
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="enriched_leads_{job_id[:8]}.csv"'
        },
    )


@router.post("/csv")
async def enrich_csv_sync(request: CSVEnrichStartRequest) -> dict[str, Any]:
    """Synchronous enrich for small CSVs (≤10 rows). Prefer /csv/start for larger files."""
    parse_leads_csv, enrich_leads_batch, results_to_csv, summarize = _get_helpers()
    try:
        leads, warnings = parse_leads_csv(request.csv_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    limit = request.limit or 10
    leads = leads[: min(limit, 10)]
    results = await enrich_leads_batch(leads)
    return {
        "total": len(results),
        "warnings": warnings,
        "summary": summarize(results),
        "csv_data": results_to_csv(results),
        "leads": results,
    }
