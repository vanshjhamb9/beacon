"""Enrich discovery results with intent signals via websearch.

Runs targeted websearch queries per company to find:
- Job postings (hiring for tech roles)
- Vendor/partner searches
- Technology needs
- Operational problems
- Project requests

Adds discovery_text field with enriched intent content.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import date

PROJECT_ROOT = Path(__file__).parent


def websearch(query: str, num_results: int = 5) -> str:
    """Run websearch via opencode websearch tool (simulated via subprocess).

    Returns concatenated search result text.
    """
    # We'll use a Python script that calls the websearch API
    # For now, use a simple approach with subprocess
    try:
        cmd = [
            sys.executable, "-c",
            f"import urllib.request, urllib.parse, json; "
            f"q = urllib.parse.quote('{query}'); "
            f"url = 'https://api.duckduckgo.com/?q=' + q + '&format=json&no_html=1'; "
            f"r = urllib.request.urlopen(url, timeout=10); "
            f"data = json.loads(r.read()); "
            f"results = data.get('AbstractText', '') + ' ' + ' '.join([x.get('Text', '') for x in data.get('RelatedTopics', [])[:5]]); "
            f"print(results[:2000])"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace")
        return result.stdout.strip()
    except Exception as e:
        return f"Search error: {e}"


def build_search_queries(company_name: str, industry: str, domain: str) -> list[str]:
    """Build targeted search queries for intent detection."""
    name = company_name.replace(" ", "+")
    queries = [
        f"{name}+India+hiring+engineer+developer+2025+2026",
        f"{name}+India+looking+for+software+development",
        f"{name}+India+technology+need+automation",
        f"{name}+India+customer+support+chatbot+whatsapp",
        f"{name}+site:linkedin.com+jobs+{name}",
    ]
    if "ecommerce" in industry.lower() or "d2c" in industry.lower() or "fashion" in industry.lower():
        queries.append(f"{name}+ecommerce+technology+stack+shopify")
        queries.append(f"{name}+D2C+brand+tech+need+automation")
    if "saas" in industry.lower() or "tech" in industry.lower():
        queries.append(f"{name}+SaaS+product+development+team")
    return queries


def enrich_company(company: dict) -> dict:
    """Enrich a single company with intent signals."""
    name = company.get("company_name", "Unknown")
    industry = company.get("industry", "")
    domain = company.get("domain", "")

    print(f"  Enriching: {name}...", end=" ", flush=True)

    queries = build_search_queries(name, industry, domain)
    all_results = []

    for q in queries:
        result = websearch(q)
        if result and "Search error" not in result:
            all_results.append(result)
        time.sleep(0.5)

    enriched_text = " ".join(all_results)
    company["discovery_text"] = (
        company.get("discovery_reason", "") + " " + enriched_text
    ).strip()

    # Add websearch results as evidence
    existing_evidence = company.get("evidence", [])
    if enriched_text:
        existing_evidence.append({
            "claim": "Websearch enrichment for intent signals",
            "value": enriched_text[:500],
            "source": "websearch",
            "source_url": "",
            "confidence": "MEDIUM",
            "observed_at": date.today().isoformat(),
        })
    company["evidence"] = existing_evidence

    print(f"({len(enriched_text)} chars)")
    return company


def main():
    """Enrich all discovered companies with intent signals."""
    input_file = PROJECT_ROOT / "exports" / "discovery_raw_results.json"
    output_file = PROJECT_ROOT / "exports" / "enriched_companies.json"

    with open(input_file, "r", encoding="utf-8") as f:
        companies = json.load(f)

    print(f"Loaded {len(companies)} companies")
    print("=" * 60)

    enriched = []
    for i, company in enumerate(companies, 1):
        print(f"\n[{i}/{len(companies)}]", end="")
        result = enrich_company(company)
        enriched.append(result)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"\n\nSaved enriched data to {output_file}")
    return enriched


if __name__ == "__main__":
    main()
