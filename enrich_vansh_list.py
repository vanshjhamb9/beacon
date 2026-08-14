#!/usr/bin/env python3
"""Batch enrich Vansh Jhamb Apollo list — founder+company → domain → crawl → profiles.

Usage:
  python enrich_vansh_list.py
  python enrich_vansh_list.py --limit 5
  python enrich_vansh_list.py --seed data/vansh_jhamb_list_seed.json
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "packages" / "sales_intelligence_platform"))
sys.path.insert(0, str(ROOT / "packages"))

from engines.founder_company_enricher import FounderCompanyEnricher  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("enrich_vansh_list")

CSV_FIELDS = [
    "founder_name",
    "company_name",
    "location",
    "job_title",
    "industry",
    "company_size",
    "enrichment_status",
    "domain",
    "website",
    "pages_scraped",
    "founder_email",
    "general_email",
    "support_email",
    "business_phone",
    "emails",
    "phones",
    "linkedin_person_url",
    "linkedin_company_url",
    "linkedin_urls",
    "decision_makers",
    "errors",
]


def _flatten(row: dict) -> dict:
    flat = {k: row.get(k, "") for k in CSV_FIELDS}
    for key in ("emails", "phones", "linkedin_urls", "decision_makers", "errors"):
        val = row.get(key) or []
        if isinstance(val, list):
            if key in ("emails", "phones") and val and isinstance(val[0], dict):
                flat[key] = "; ".join(
                    f"{i.get('value','')}@{i.get('confidence', '')}" for i in val
                )
            elif key == "decision_makers" and val and isinstance(val[0], dict):
                flat[key] = "; ".join(
                    f"{i.get('name','')}|{i.get('role','')}" for i in val
                )
            else:
                flat[key] = "; ".join(str(x) for x in val)
        else:
            flat[key] = val
    return flat


async def run(seed_path: Path, out_json: Path, out_csv: Path, limit: int | None) -> dict:
    leads = json.loads(seed_path.read_text(encoding="utf-8"))
    if limit is not None:
        leads = leads[:limit]

    enricher = FounderCompanyEnricher(timeout=8.0, delay=0.8, max_concurrent=2, max_pages=8)
    results: list[dict] = []
    checkpoint = out_json.with_suffix(".checkpoint.json")
    t0 = time.time()

    # Resume from checkpoint if present and same seed size intent
    start_idx = 0
    if checkpoint.exists() and limit is None:
        try:
            prev = json.loads(checkpoint.read_text(encoding="utf-8"))
            if isinstance(prev, list) and prev:
                results = prev
                start_idx = len(prev)
                logger.info("Resuming from checkpoint at %d", start_idx)
        except Exception:
            results = []
            start_idx = 0

    for i, lead in enumerate(leads[start_idx:], start_idx + 1):
        name = lead.get("founder_name", "")
        company = lead.get("company_name", "")
        logger.info("[%d/%d] Enriching %s @ %s", i, len(leads), name, company)
        try:
            result = await enricher.enrich(
                founder_name=name,
                company_name=company,
                location=lead.get("location", ""),
                industry=lead.get("industry", ""),
                job_title=lead.get("job_title", ""),
                company_size=lead.get("company_size"),
            )
            results.append(result.to_dict())
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed %s / %s", name, company)
            results.append(
                {
                    "founder_name": name,
                    "company_name": company,
                    "location": lead.get("location", ""),
                    "job_title": lead.get("job_title", ""),
                    "industry": lead.get("industry", ""),
                    "company_size": lead.get("company_size"),
                    "enrichment_status": "error",
                    "domain": None,
                    "website": None,
                    "pages_scraped": 0,
                    "emails": [],
                    "phones": [],
                    "errors": [str(exc)],
                }
            )
        # Checkpoint every lead
        checkpoint.write_text(json.dumps(results, ensure_ascii=False), encoding="utf-8")
        await asyncio.sleep(0.3)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "seed": str(seed_path),
        "total": len(results),
        "elapsed_seconds": round(time.time() - t0, 1),
        "leads": results,
    }
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow(_flatten(row))

    summary = _summarize(results)
    summary["elapsed_seconds"] = payload["elapsed_seconds"]
    summary_path = out_json.with_name("vansh_list_enriched_summary.json")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("Summary: %s", json.dumps(summary))
    logger.info("Wrote %s", out_json)
    logger.info("Wrote %s", out_csv)
    if checkpoint.exists():
        checkpoint.unlink(missing_ok=True)
    return summary


def _summarize(results: list[dict]) -> dict:
    n = len(results) or 1
    domain_found = sum(1 for r in results if r.get("domain"))
    email = sum(1 for r in results if r.get("emails") or r.get("founder_email") or r.get("general_email"))
    phone = sum(1 for r in results if r.get("phones") or r.get("business_phone"))
    li_person = sum(1 for r in results if r.get("linkedin_person_url"))
    li_company = sum(1 for r in results if r.get("linkedin_company_url"))
    status_counts: dict[str, int] = {}
    for r in results:
        st = r.get("enrichment_status") or "unknown"
        status_counts[st] = status_counts.get(st, 0) + 1
    return {
        "total": len(results),
        "domain_found": domain_found,
        "domain_found_pct": round(100 * domain_found / n, 1),
        "with_email": email,
        "with_email_pct": round(100 * email / n, 1),
        "with_phone": phone,
        "with_phone_pct": round(100 * phone / n, 1),
        "linkedin_person": li_person,
        "linkedin_person_pct": round(100 * li_person / n, 1),
        "linkedin_company": li_company,
        "linkedin_company_pct": round(100 * li_company / n, 1),
        "status_counts": status_counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich Vansh Jhamb Apollo list")
    parser.add_argument(
        "--seed",
        type=Path,
        default=ROOT / "data" / "vansh_jhamb_list_seed.json",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=ROOT / "exports" / "vansh_list_enriched.json",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "exports" / "vansh_list_enriched.csv",
    )
    parser.add_argument("--limit", type=int, default=None, help="Only enrich first N leads")
    args = parser.parse_args()
    asyncio.run(run(args.seed, args.out_json, args.out_csv, args.limit))


if __name__ == "__main__":
    main()
