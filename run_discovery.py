"""Run signal-based discovery engine. Output raw companies for founder review.

NO enrichment. NO scoring. Just discovery.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import date

from packages.discovery_engine.engine import DiscoveryEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def main() -> None:
    engine = DiscoveryEngine()

    print("=" * 80)
    print("SIGNAL-BASED DISCOVERY ENGINE")
    print("Date:", date.today().isoformat())
    print("Target: 30 companies from EXTERNAL SIGNALS")
    print("=" * 80)
    print()

    companies = await engine.discover(limit=30, min_per_source=5)

    print()
    print("=" * 80)
    print(f"DISCOVERY RESULTS: {len(companies)} companies found")
    print("=" * 80)
    print()

    # Print each company with WHY it was discovered
    for i, company in enumerate(companies, 1):
        print(f"{'─' * 70}")
        print(f"#{i:02d} | {company.company_name}")
        print(f"{'─' * 70}")
        print(f"  Domain:         {company.domain}")
        print(f"  Source:         {company.source}")
        print(f"  WHY discovered: {company.discovery_reason}")
        print(f"  Business stage: {company.business_stage}")

        if company.founder_name:
            print(f"  Founder:        {company.founder_name} ({company.founder_role})")
            print(f"  Founder source: {company.founder_source}")

        if company.growth_signals:
            print(f"  Growth signals:")
            for sig, src in zip(company.growth_signals, company.growth_signal_sources):
                print(f"    • {sig}")
                print(f"      Source: {src}")

        if company.buying_signals:
            print(f"  Buying signals:")
            for sig, src in zip(company.buying_signals, company.buying_signal_sources):
                print(f"    • {sig}")
                print(f"      Source: {src}")

        print()

    # Summary by source
    print("=" * 80)
    print("SUMMARY BY SOURCE")
    print("=" * 80)
    source_counts: dict[str, int] = {}
    for c in companies:
        source_counts[c.source] = source_counts.get(c.source, 0) + 1
    for source, count in sorted(source_counts.items()):
        print(f"  {source}: {count}")

    # Summary by stage
    print()
    print("SUMMARY BY STAGE")
    stage_counts: dict[str, int] = {}
    for c in companies:
        stage_counts[c.business_stage] = stage_counts.get(c.business_stage, 0) + 1
    for stage, count in sorted(stage_counts.items()):
        print(f"  {stage}: {count}")

    # Save to JSON
    output_path = "exports/discovery_raw_results.json"
    output_data = []
    for c in companies:
        output_data.append({
            "company_name": c.company_name,
            "domain": c.domain,
            "source": c.source,
            "discovery_reason": c.discovery_reason,
            "discovery_date": c.discovery_date.isoformat(),
            "business_stage": c.business_stage,
            "employee_count": c.employee_count,
            "employee_source": c.employee_source,
            "employee_confidence": c.employee_confidence,
            "founder_name": c.founder_name,
            "founder_role": c.founder_role,
            "founder_source": c.founder_source,
            "founder_confidence": c.founder_confidence,
            "growth_signals": c.growth_signals,
            "growth_signal_sources": c.growth_signal_sources,
            "buying_signals": c.buying_signals,
            "buying_signal_sources": c.buying_signal_sources,
            "technology_signals": c.technology_signals,
            "industry": c.industry,
            "city": c.city,
            "country": c.country,
            "metadata": c.metadata,
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print()
    print(f"Results saved to: {output_path}")
    print()
    print("NEXT STEP: Founder reviews these 30 companies.")
    print("Only after approval: Discovery → Enrichment → Qualification → Buyability → Sales Intelligence")


if __name__ == "__main__":
    asyncio.run(main())
