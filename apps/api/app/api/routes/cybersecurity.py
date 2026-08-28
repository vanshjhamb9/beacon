"""Cybersecurity Buyer Discovery Engine — API routes."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FileResponse, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cybersecurity", tags=["cybersecurity"])

EXPORT_DIR = Path("/home/ubuntu/beacon/exports/cybersecurity_discovery")


class DiscoveryRunResponse(BaseModel):
    status: str
    total_signals: int
    total_opportunities: int
    sales_ready: int
    marketing_ready: int
    not_ready: int
    p0_count: int
    p1_count: int
    p2_count: int
    elapsed_seconds: float
    output_files: list[str] = Field(default_factory=list)


class LeadSummary(BaseModel):
    opportunity_id: str
    company_name: str
    company_url: str
    country: str
    industry: str
    priority: str
    final_verdict: str
    buying_event: str
    services_needed: list[str]
    decision_maker: str
    email: str
    email_status: str
    contactability: str
    evidence_count: int
    evidence_confidence: str


_discovery_lock = asyncio.Lock()


@router.get("/run", response_model=DiscoveryRunResponse)
async def run_discovery() -> DiscoveryRunResponse:
    """Trigger a full cybersecurity discovery run using System A pipeline."""
    if _discovery_lock.locked():
        raise HTTPException(status_code=409, detail="Discovery already in progress")
    async with _discovery_lock:
        import sys
        import time
        sys.path.insert(0, "/home/ubuntu/beacon/packages")

        try:
            from cybersecurity_discovery.pipeline import run_cybersecurity_discovery
            from cybersecurity_discovery.exporters import write_exports
        except ImportError as exc:
            raise HTTPException(status_code=500, detail=f"Cybersecurity pipeline unavailable: {exc}") from exc

        start = time.time()
        try:
            result = await run_cybersecurity_discovery(limit=80, enrich=True)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Discovery failed: {exc}") from exc
        elapsed = time.time() - start

        # Write exports
        try:
            output_files = write_exports(result, EXPORT_DIR)
        except Exception as exc:
            output_files = []
            logger.warning("Failed to write exports: %s", exc)

        # Count P0/P1/P2 from sales_ready leads
        p0_count = sum(1 for o in result.sales_ready if o.intent_level in {"HOT", "HIGH"})
        p1_count = sum(1 for o in result.sales_ready if o.intent_level == "MEDIUM")
        p2_count = sum(1 for o in result.sales_ready if o.intent_level == "LOW")

        return DiscoveryRunResponse(
            status="completed",
            total_signals=result.counters.get("TOTAL_DISCOVERED", 0),
            total_opportunities=len(result.all_opportunities),
            sales_ready=len(result.sales_ready),
            marketing_ready=0,
            not_ready=len(result.needs_research) + len(result.rejected),
            p0_count=p0_count,
            p1_count=p1_count,
            p2_count=p2_count,
            elapsed_seconds=round(elapsed, 1),
            output_files=output_files,
        )


@router.get("/leads", response_model=list[LeadSummary])
async def list_leads() -> list[LeadSummary]:
    """List all SALES_READY leads from the latest export."""
    filepath = EXPORT_DIR / "cyber_sales_ready.json"
    if not filepath.exists():
        return []

    data = json.loads(filepath.read_text())
    return [
        LeadSummary(
            opportunity_id=o.get("opportunity_id", ""),
            company_name=o.get("company") or "",
            company_url=o.get("company_url") or "",
            country=o.get("country") or "",
            industry=o.get("industry") or "",
            priority=o.get("intent_level") or "",
            final_verdict=o.get("final_verdict") or "",
            buying_event=o.get("buying_event_category") or "",
            services_needed=o.get("services_needed") or [],
            decision_maker=o.get("buyer_name") or "",
            email=o.get("email") or "",
            email_status=o.get("email_status") or "",
            contactability=o.get("contactability") or "",
            evidence_count=len(o.get("evidence") or []),
            evidence_confidence=o.get("evidence_confidence") or "",
        )
        for o in data
    ]


@router.get("/export/{format_name}")
async def export_file(format_name: str):
    """Download an export file."""
    allowed = {
        "json": ("cyber_sales_ready.json", "application/json"),
        "rejected": ("cyber_rejected.json", "application/json"),
        "audit": ("cyber_evidence_audit.json", "application/json"),
        "all": ("cyber_all_opportunities.json", "application/json"),
    }

    if format_name not in allowed:
        raise HTTPException(status_code=400, detail=f"Unknown format: {format_name}. Allowed: {list(allowed.keys())}")

    filename, media_type = allowed[format_name]
    filepath = EXPORT_DIR / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Export not found: {filename}. Run discovery first.")

    return FileResponse(path=str(filepath), filename=filename, media_type=media_type)


@router.get("/summary")
async def get_summary() -> dict[str, Any]:
    """Get summary statistics from the latest run."""
    sales_path = EXPORT_DIR / "cyber_sales_ready.json"
    rejected_path = EXPORT_DIR / "cyber_rejected.json"

    result: dict[str, Any] = {
        "has_data": sales_path.exists(),
        "sales_ready_count": 0,
        "rejected_count": 0,
    }

    if sales_path.exists():
        data = json.loads(sales_path.read_text())
        result["sales_ready_count"] = len(data)

    if rejected_path.exists():
        data = json.loads(rejected_path.read_text())
        result["rejected_count"] = len(data)

    return result
