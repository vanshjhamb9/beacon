"""Celery tasks for COMAI B2B Partner Discovery."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

from celery import shared_task

logger = logging.getLogger(__name__)

ROOT = Path("/home/ubuntu/beacon")


@shared_task(
    name="b2b_partners.discover_partners",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def discover_b2b_partners(self, limit: int = 50):
    """Run B2B partner discovery via subprocess.

    Extracts agencies, consultants, and service providers for COMAI partner program.
    Runs every 6 hours via Celery beat.
    """
    try:
        result = subprocess.run(
            [
                str(ROOT / ".venv/bin/python"),
                str(ROOT / "apps/api/app/scripts/comai_b2b_partner_extraction.py"),
            ],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(ROOT),
        )

        if result.returncode == 0:
            output = json.loads(result.stdout) if result.stdout else {}
            logger.info(f"B2B partner discovery completed: {output.get('imported', 0)} imported")
            return {
                "status": "completed",
                "imported": output.get("imported", 0),
                "tier_a": output.get("tier_a", 0),
                "tier_b": output.get("tier_b", 0),
                "tier_c": output.get("tier_c", 0),
            }
        else:
            logger.error(f"B2B partner discovery failed: {result.stderr[:500]}")
            return {"status": "error", "error": result.stderr[:500]}

    except subprocess.TimeoutExpired:
        logger.error("B2B partner discovery timed out")
        return {"status": "error", "error": "Timeout"}
    except Exception as e:
        logger.error(f"B2B partner discovery failed: {e}")
        return {"status": "error", "error": str(e)}
