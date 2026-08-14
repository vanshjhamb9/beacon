"""Print discovery results in readable format."""

import json
import sys


def main():
    with open("exports/discovery_raw_results.json", "r", encoding="utf-8") as f:
        companies = json.load(f)

    print("=" * 80)
    print("SIGNAL-BASED DISCOVERY RESULTS - 30 COMPANIES")
    print("Date: 2026-08-08")
    print("Source: EXTERNAL SIGNALS (funding announcements, NOT seed lists)")
    print("=" * 80)
    print()

    for i, c in enumerate(companies, 1):
        name = c["company_name"]
        print("-" * 70)
        print(f"#{i:02d} | {name}")
        print("-" * 70)
        print(f"  Domain:         {c['domain']}")
        print(f"  Source:         {c['source']}")
        print(f"  WHY discovered: {c['discovery_reason']}")
        print(f"  Business stage: {c['business_stage']}")
        if c["founder_name"]:
            print(f"  Founder:        {c['founder_name']} ({c['founder_role']})")
        if c["growth_signals"]:
            print("  Growth signals:")
            for sig in c["growth_signals"][:3]:
                print(f"    - {sig}")
        if c["buying_signals"]:
            print("  Buying signals:")
            for sig in c["buying_signals"][:3]:
                print(f"    - {sig}")
        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    sources = {}
    for c in companies:
        s = c["source"]
        sources[s] = sources.get(s, 0) + 1
    print("By source:")
    for s, cnt in sorted(sources.items()):
        print(f"  {s}: {cnt}")

    stages = {}
    for c in companies:
        st = c["business_stage"]
        stages[st] = stages.get(st, 0) + 1
    print("\nBy stage:")
    for st, cnt in sorted(stages.items()):
        print(f"  {st}: {cnt}")

    with_founder = [c for c in companies if c["founder_name"]]
    print(f"\nCompanies with founder identified: {len(with_founder)}/{len(companies)}")
    for c in with_founder:
        print(f"  {c['company_name']}: {c['founder_name']} ({c['founder_role']})")

    famous = ["mamaearth", "sugar", "plum", "boat", "noise", "nykaa", "firstcry"]
    famous_found = [c for c in companies if any(f in c["company_name"].lower() for f in famous)]
    print(f"\nFamous/enterprise brands found: {len(famous_found)}/{len(companies)}")
    if famous_found:
        for c in famous_found:
            print(f"  WARNING: {c['company_name']}")
    else:
        print("  NONE - all companies are signal-discovered, not famous brands")


if __name__ == "__main__":
    main()
