"""One-shot M1 Revenue Readiness Validation against live DB."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "apps" / "api"), str(ROOT / "apps" / "worker"), str(ROOT / "packages"), str(ROOT)]

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services.revenue_readiness_validation import RevenueReadinessValidationService


async def main() -> None:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        report = await RevenueReadinessValidationService(session, settings).full_report()
    out = ROOT / "docs" / "m1-revenue-readiness-live-report.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "overall_status": report["overall_status"],
        "estimated_qualified_per_100": report["estimated_qualified_per_100"],
        "production_allowed": report["production_allowed"],
        "success_metrics": report["success_metrics"],
        "phase_summaries": [
            {"phase": p["phase"], "title": p["title"], "status": p["status"], "summary": p["summary"]}
            for p in report["phases"]
        ],
        "wrote": str(out),
    }, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
