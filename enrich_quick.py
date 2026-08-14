"""Quick enrichment — adds websearch-sourced intent signals to discovery data.

Run this after manual websearch to inject enriched text into the pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import date

PROJECT_ROOT = Path(__file__).parent

# Manually enriched data from websearch results
ENRICHMENTS = {
    "HyugaLife": {
        "discovery_text": (
            "Raised Rs 100 Cr Series A (Apr 2026). Mumbai-based nutrition marketplace. "
            "Has software engineer on team (React Native, Fullstack). Founded 2022. "
            "Active jobs on Jobaaj (Marketing Communications Manager). "
            "1.5M+ registered users, 450+ brands, 10K+ products. "
            "Hiring for marketing roles. Expanding into offline retail and dark store network. "
            "Building AI personalisation engine. 60+ salary records on AmbitionBox."
        ),
        "evidence_additions": [
            {"claim": "Has software engineer (React Native/Fullstack)", "value": "Mohak Muskan, Software Engineer since Sep 2024", "source": "linkedin", "source_url": "https://linkedin.com/in/mohak-muskan-0a7a7b16a", "confidence": "VERIFIED"},
            {"claim": "Active marketing hiring", "value": "Marketing Communications Manager role posted", "source": "jobaaj.com", "source_url": "https://www.jobaaj.com/company/hyugalife-careers", "confidence": "VERIFIED"},
            {"claim": "Building AI personalisation engine", "value": "Growth signal from discovery", "source": "funding_announcement", "source_url": "", "confidence": "MEDIUM"},
            {"claim": "1.5M+ registered users", "value": "Significant user base", "source": "funding_announcement", "source_url": "", "confidence": "HIGH"},
        ],
    },
    "BeastLife": {
        "discovery_text": (
            "Raised Rs 20 Cr Pre-Series A (Mar 2026). Sports nutrition brand. "
            "Self-funded (bootstrapped) company without external investments per Uplers. "
            "Founded 2024 by Gaurav Taneja (The Flying Beast). "
            "Hiring for Copy Content Writer. New Product Development intern positions. "
            "Food Technology roles. No explicit tech/software hiring signals. "
            "Revenue grew from Rs 36 Cr (FY25) to Rs 100 Cr (FY26)."
        ),
        "evidence_additions": [
            {"claim": "Bootstrapped / self-funded", "value": "No external investments per Uplers profile", "source": "uplers.com", "source_url": "https://www.uplers.com/company/beastlife-8936", "confidence": "HIGH"},
            {"claim": "Hiring content and product roles", "value": "Copy Content Writer, New Product Development intern", "source": "indeed.com", "source_url": "https://in.indeed.com/q-beastlife-jobs.html", "confidence": "VERIFIED"},
            {"claim": "No tech/software hiring signals", "value": "No developer or engineer roles found", "source": "websearch", "source_url": "", "confidence": "MEDIUM"},
        ],
    },
    "MyDesignation": {
        "discovery_text": (
            "Raised Rs 40 Cr Series A (Feb 2026) led by RPSG Capital Ventures. "
            "Kerala-based D2C fashion brand, 1M+ customers, high repeat purchase rates. "
            "Founded 2017 by Gopika Menon (CEO). 11-50 employees. "
            "Uses 20 technologies for website per BuiltWith (DNSSEC, Amazon, etc). "
            "Self-funded historically, now Series A. "
            "Fast-growing unisex fashion brand. Monthly web visits 400K+."
        ),
        "evidence_additions": [
            {"claim": "20 technologies on website", "value": "DNSSEC, Mobile Non Scaleable Content, Amazon per BuiltWith", "source": "crunchbase.com", "source_url": "https://www.crunchbase.com/organization/mydesignation", "confidence": "HIGH"},
            {"claim": "RPSG Capital Ventures led Series A", "value": "4 investors including RPSG Capital Ventures and Veltis Capital", "source": "crunchbase.com", "source_url": "https://www.crunchbase.com/organization/mydesignation", "confidence": "VERIFIED"},
            {"claim": "400K+ monthly web visits", "value": "-35.68% in past month per SemRush", "source": "crunchbase.com", "source_url": "https://www.crunchbase.com/organization/mydesignation", "confidence": "HIGH"},
        ],
    },
    "Open Secret": {
        "discovery_text": (
            "Raised Rs 50 Cr (2026) led by Desai Brothers Group. "
            "Mumbai-based D2C healthy snacking brand expanding offline retail and product portfolio. "
            "No explicit tech hiring or technology need signals found. "
            "Expanding into offline retail channels."
        ),
        "evidence_additions": [
            {"claim": "Expanding offline retail", "value": "Growing offline presence alongside D2C", "source": "funding_announcement", "source_url": "", "confidence": "MEDIUM"},
            {"claim": "No tech/software hiring signals", "value": "No developer or engineer roles found", "source": "websearch", "source_url": "", "confidence": "MEDIUM"},
        ],
    },
    "Nester": {
        "discovery_text": (
            "Raised Rs 19 Cr Pre-Series A (Feb 2026) led by Fireside Ventures. "
            "Design-led home appliance brand, stainless steel kitchen products. "
            "Founded Jan 2025. Very early stage. "
            "No explicit technology hiring or need signals found."
        ),
        "evidence_additions": [
            {"claim": "Very early stage", "value": "Founded Jan 2025", "source": "funding_announcement", "source_url": "", "confidence": "HIGH"},
            {"claim": "No tech/software hiring signals", "value": "No developer or engineer roles found", "source": "websearch", "source_url": "", "confidence": "MEDIUM"},
        ],
    },
}


def main():
    input_file = PROJECT_ROOT / "exports" / "discovery_raw_results.json"
    output_file = PROJECT_ROOT / "exports" / "enriched_companies.json"

    with open(input_file, "r", encoding="utf-8") as f:
        companies = json.load(f)

    enriched = []
    for company in companies:
        name = company.get("company_name", "")
        if name in ENRICHMENTS:
            enrich = ENRICHMENTS[name]
            company["discovery_text"] = enrich["discovery_text"]
            existing_evidence = company.get("evidence", [])
            for e in enrich.get("evidence_additions", []):
                e["observed_at"] = date.today().isoformat()
                existing_evidence.append(e)
            company["evidence"] = existing_evidence
            print(f"  [ENRICHED] {name}")
        else:
            # Use discovery_reason as fallback
            company["discovery_text"] = company.get("discovery_reason", "")
            print(f"  [FALLBACK] {name}")
        enriched.append(company)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(enriched)} enriched companies to {output_file}")


if __name__ == "__main__":
    main()
