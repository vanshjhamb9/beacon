"""
Automated Mega Lead Extraction Task
Runs every 20 minutes to extract new leads with founder enrichment.
Uses subprocess to avoid complex import dependencies.
"""

import json
import logging
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from celery import shared_task

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
EXPORT_ROOT = ROOT / "exports"
SEEN_PATH = EXPORT_ROOT / "lead_engine_runs" / "_mega_seen_domains.json"


@shared_task(
    name="lead_engine.mega_extract_with_enrichment",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def mega_extract_with_enrichment(self, limit=40, enrich_founders=True):
    """Extract mega leads with founder enrichment via subprocess."""
    logger.info(f"Starting mega extraction: limit={limit}, enrich_founders={enrich_founders}")

    script_path = ROOT / "apps" / "api" / "app" / "scripts" / "mega_extract_and_store.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--limit", str(limit),
            "--enrich-founders" if enrich_founders else "--no-enrich-founders",
        ],
        capture_output=True,
        text=True,
        timeout=300,
        cwd=str(ROOT),
    )

    if result.returncode != 0:
        logger.error(f"Mega extraction failed: {result.stderr}")
        raise RuntimeError(f"Extraction failed: {result.stderr[:500]}")

    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        output = {"status": "completed", "raw_output": result.stdout[:500]}

    logger.info(f"Mega extraction completed: {output}")
    return output
