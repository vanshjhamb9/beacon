#!/usr/bin/env python3
"""Beacon Lane C — one-shot cybersecurity buyer discovery.

Writes exports/cybersecurity_discovery/ then STOPS.
Does not send outreach. Does not scan targets. Does not guess emails.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.cybersecurity_discovery.exporters import write_exports
from packages.cybersecurity_discovery.pipeline import run_cybersecurity_discovery

OUTPUT_DIR = ROOT / "exports" / "cybersecurity_discovery"


async def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print("=" * 70)
    print("BEACON — CYBERSECURITY HIGH-INTENT BUYER DISCOVERY")
    print("CTO LANE. PUBLIC BUYING EVENTS WITH A REACHABLE PATH BECOME SALES READY.")
    print("=" * 70)

    result = await run_cybersecurity_discovery(limit=150, enrich=True)
    written = write_exports(result, OUTPUT_DIR)
    try:
        from packages.cybersecurity_discovery.workspace_sync import sync_to_workspace
        synced = sync_to_workspace(result)
        print(f"\nWORKSPACE SYNC  leads={synced.get('workspace_leads', 0)} pool_added={synced.get('pool_added', 0)}")
    except Exception as exc:  # noqa: BLE001
        print(f"\nWORKSPACE SYNC SKIPPED: {exc}")

    print("\nCOUNTERS")
    for key in (
        "TOTAL_DISCOVERED",
        "BUYING_EVENTS",
        "VERIFIED_REQUIREMENTS",
        "HOT",
        "HIGH_INTENT",
        "CONTACTABLE",
        "SALES_READY",
        "PARTNER_OPPORTUNITIES",
        "NEEDS_RESEARCH",
        "REJECTED",
    ):
        print(f"  {key}: {result.counters.get(key, 0)}")

    print("\nFUNNEL")
    for stage, count in result.funnel.items():
        print(f"  {stage}: {count}")

    print("\nCTO — STRONGEST / GATE FAILURES")
    ranked = (result.sales_ready + result.needs_research)[:8]
    if not ranked:
        ranked = [o for o in result.rejected if o.buying_event_verified][:8]
    if not ranked:
        print("  No opportunities close enough for a 15-minute contact.")
    for opp in ranked:
        print(f"  - {opp.company or opp.title}")
        print(f"      verdict={opp.final_verdict} type={opp.opportunity_type}")
        print(f"      CTO={opp.cto_15_minute_test} ({opp.cto_decision_reason})")
        if opp.failed_gates:
            print(f"      failed_gates={', '.join(opp.failed_gates)}")
        print(f"      source={opp.source_url}")

    print("\nWROTE")
    for name, path in written.items():
        print(f"  {name}: {path}")

    print("\nSTOP. DO NOT SEND OUTREACH.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
