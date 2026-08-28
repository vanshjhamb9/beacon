"""Cybersecurity Buyer Discovery Engine — API routes."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

router = APIRouter(prefix="/cybersecurity", tags=["cybersecurity"])

EXPORT_DIR = Path("/home/ubuntu/beacon/exports/cybersecurity")


class DiscoveryRunResponse(BaseModel):
    status: str
    total_signals: int = 0
    total_opportunities: int = 0
    sales_ready: int = 0
    marketing_ready: int = 0
    not_ready: int = 0
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    elapsed_seconds: float = 0
    output_files: dict[str, str] = {}


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
    """Trigger a full cybersecurity discovery run."""
    if _discovery_lock.locked():
        raise HTTPException(status_code=409, detail="Discovery already in progress")
    async with _discovery_lock:
        import sys
        sys.path.insert(0, "/home/ubuntu/beacon/packages")

        try:
            from cybersecurity_engine.engine import CybersecurityDiscoveryEngine
        except ImportError as exc:
            raise HTTPException(status_code=500, detail=f"Cybersecurity engine unavailable: {exc}") from exc

        engine = CybersecurityDiscoveryEngine(
            output_dir=str(EXPORT_DIR),
            sender_name="Beacon Security Team",
            max_items_per_source=20,
        )

        try:
            summary = await engine.run(limit=30)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Discovery failed: {exc}") from exc

        return DiscoveryRunResponse(
            status="completed",
            total_signals=summary["total_signals"],
            total_opportunities=summary["total_opportunities"],
            sales_ready=summary["sales_ready"],
            marketing_ready=summary["marketing_ready"],
            not_ready=summary["not_ready"],
            p0_count=summary["p0_count"],
            p1_count=summary["p1_count"],
            p2_count=summary["p2_count"],
            elapsed_seconds=summary["elapsed_seconds"],
            output_files=summary["output_files"],
        )


@router.get("/leads", response_model=list[LeadSummary])
async def list_leads() -> list[LeadSummary]:
    """List all SALES_READY leads from the latest export."""
    filepath = EXPORT_DIR / "cybersecurity_sales_ready.json"
    if not filepath.exists():
        return []

    data = json.loads(filepath.read_text())
    return [
        LeadSummary(
            opportunity_id=o.get("opportunity_id", ""),
            company_name=o.get("company", {}).get("name", ""),
            company_url=o.get("company", {}).get("url", ""),
            country=o.get("company", {}).get("country", ""),
            industry=o.get("company", {}).get("industry", ""),
            priority=o.get("priority", ""),
            final_verdict=o.get("final_verdict", ""),
            buying_event=o.get("buying_event", {}).get("description", ""),
            services_needed=o.get("buying_event", {}).get("services_needed", []),
            decision_maker=o.get("contact", {}).get("name", ""),
            email=o.get("contact", {}).get("email", ""),
            email_status=o.get("contact", {}).get("email_status", ""),
            contactability=o.get("contactability", ""),
            evidence_count=o.get("evidence_chain", {}).__len__() if isinstance(o.get("evidence_chain"), list) else 0,
            evidence_confidence=o.get("evidence_confidence", ""),
        )
        for o in data
    ]


@router.get("/export/{format_name}")
async def export_file(format_name: str):
    """Download an export file."""
    allowed = {
        "json": ("cybersecurity_sales_ready.json", "application/json"),
        "xlsx": ("cybersecurity_sales_ready.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        "report": ("cybersecurity_report.txt", "text/plain"),
        "outreach": ("cybersecurity_outreach_queue.json", "application/json"),
        "rejected": ("cybersecurity_rejected.json", "application/json"),
        "audit": ("cybersecurity_evidence_audit.json", "application/json"),
    }

    if format_name not in allowed:
        raise HTTPException(status_code=400, detail=f"Unknown format: {format_name}. Allowed: {list(allowed.keys())}")

    filename, media_type = allowed[format_name]
    filepath = EXPORT_DIR / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Export not found: {filename}. Run discovery first.")

    return FileResponse(path=str(filepath), filename=filename, media_type=media_type)


@router.get("/report")
async def get_report():
    """Get the human-readable report."""
    filepath = EXPORT_DIR / "cybersecurity_report.txt"
    if not filepath.exists():
        return PlainTextResponse("No report available. Run discovery first.")
    return PlainTextResponse(content=filepath.read_text())


@router.get("/summary")
async def get_summary() -> dict[str, Any]:
    """Get summary statistics from the latest run."""
    report_path = EXPORT_DIR / "cybersecurity_report.txt"
    sales_path = EXPORT_DIR / "cybersecurity_sales_ready.json"
    audit_path = EXPORT_DIR / "cybersecurity_evidence_audit.json"

    result: dict[str, Any] = {
        "has_data": sales_path.exists(),
        "sales_ready_count": 0,
        "total_evidence_items": 0,
    }

    if sales_path.exists():
        data = json.loads(sales_path.read_text())
        result["sales_ready_count"] = len(data)

    if audit_path.exists():
        audit = json.loads(audit_path.read_text())
        result["total_evidence_items"] = sum(a.get("evidence_count", 0) for a in audit)

    return result
