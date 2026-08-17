"""BEACON — Cybersecurity Buyer Discovery Engine.

Run discovery for cybersecurity buying opportunities.

Usage:
    python run_cybersecurity_discovery.py
    python run_cybersecurity_discovery.py --limit 100
    python run_cybersecurity_discovery.py --output ./results
"""

import asyncio
import sys
from pathlib import Path

# Add the project root and packages to the path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "packages"))

from cybersecurity_engine.engine import CybersecurityDiscoveryEngine


async def main():
    """Run the cybersecurity discovery engine."""
    import argparse

    parser = argparse.ArgumentParser(
        description="BEACON — Cybersecurity Buyer Discovery Engine"
    )
    parser.add_argument(
        "--limit", type=int, default=50,
        help="Maximum opportunities to discover"
    )
    parser.add_argument(
        "--output", type=str, default=".",
        help="Output directory"
    )
    parser.add_argument(
        "--sender-name", type=str, default="Security Team",
        help="Sender name for outreach"
    )
    parser.add_argument(
        "--sender-company", type=str, default="",
        help="Sender company for outreach"
    )
    parser.add_argument(
        "--max-per-source", type=int, default=30,
        help="Max signals per source"
    )

    args = parser.parse_args()

    engine = CybersecurityDiscoveryEngine(
        output_dir=args.output,
        sender_name=args.sender_name,
        sender_company=args.sender_company,
        max_items_per_source=args.max_per_source,
    )

    summary = await engine.run(limit=args.limit)

    # Print final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Total Opportunities: {summary['total_opportunities']}")
    print(f"SALES_READY: {summary['sales_ready']}")
    print(f"MARKETING_READY: {summary['marketing_ready']}")
    print(f"P0 (Active Buyers): {summary['p0_count']}")
    print(f"P1 (Verified Pain): {summary['p1_count']}")
    print(f"P2 (Outbound Prospects): {summary['p2_count']}")
    print(f"\nOutput files:")
    for name, path in summary['output_files'].items():
        print(f"  {name}: {path}")

    return 0 if summary['sales_ready'] > 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
