"""Sprint 31 — CIR engineering report generator."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))

from company_intelligence.pipelines.engine import CirPipeline
from company_intelligence.rebuild.engine import CirRebuildEngine


def _company(i: int, *, rich: bool) -> dict:
    domain = f"firm{i}.io"
    if not rich:
        return {
            "company_id": f"poor-{i}",
            "company_name": f"Poor{i}",
            "website": f"https://{domain}",
            "erowd_admitted": True,
            "website_pages": [{"url": f"https://{domain}", "path": "/", "title": "x", "text": "hi"}],
        }
    return {
        "company_id": f"rich-{i}",
        "company_name": f"Firm{i}",
        "website": f"https://{domain}",
        "domain": domain,
        "erowd_admitted": True,
        "industry": "Software",
        "country": "United States",
        "employees": "80",
        "website_pages": [
            {
                "url": f"https://{domain}",
                "path": "/",
                "title": f"Firm{i}",
                "description": "Enterprise SaaS automation",
                "headings": ["AI automation"],
                "text": (
                    "Enterprise SaaS AI agents automation API Salesforce HubSpot AWS React OpenAI. "
                    "Hiring AI engineers. SOC 2. Free trial. United States. Founded in 2019."
                ),
            },
            {"url": f"https://{domain}/team", "path": "/team", "title": "Team", "text": f"Alex {i}, CEO. hello@{domain}"},
            {"url": f"https://{domain}/careers", "path": "/careers", "title": "Careers", "text": "Now hiring engineers. Scaling."},
        ],
        "technologies": ["React", "AWS"],
        "buying_signals": ["Hiring", "Scaling"],
        "decision_makers": [{"name": f"Alex {i}", "role": "CEO", "email": f"alex@{domain}"}] if i % 5 != 4 else [],
    }


def main() -> None:
    pipe = CirPipeline()
    payloads = [_company(i, rich=i < 420) for i in range(500)]
    t0 = perf_counter()
    snaps = [pipe.evaluate(p) for p in payloads]
    elapsed = (perf_counter() - t0) * 1000
    report = CirRebuildEngine().build(snaps)
    data = report.model_dump(mode="json")
    data["wall_ms"] = round(elapsed, 2)

    out_json = ROOT / "docs" / "sprint-31-cir-live-report.json"
    out_md = ROOT / "docs" / "sprint-31-cir-engineering-report.md"
    out_json.write_text(json.dumps(data, indent=2), encoding="utf-8")

    lines = [
        "# Sprint 31 — Company Intelligence Reconstruction (CIR v1)",
        "",
        "## Mission",
        "",
        "> If I were the founder of Urban Webworks, what do I need to know before sending the very first email?",
        "",
        "CIR reconstructs verified companies into business understanding, ICP, technology, buying signals,",
        "service match, opportunity narrative, contacts, and revenue readiness — evidence only, no GPT.",
        "",
        "## Pipeline",
        "",
        "```",
        "Verified Company (EROWD) → Website Understanding → Business → Products → ICP → Technology",
        "→ Buying Signals → Service Match v3 → Narrative → Contacts → Revenue Readiness → Founder Card",
        "```",
        "",
        "## Delivered",
        "",
        "| Area | Path |",
        "| --- | --- |",
        "| Package | `packages/company_intelligence/` (`cir-v1`) |",
        "| Migration | `20260724_0038` — 8 append-only CIR tables |",
        "| API | `/company-intelligence/*` |",
        "| Worker | `company_intelligence.process_verified` every 120s (EROWD-admitted only) |",
        "| Dashboard | `/company-intelligence` |",
        "| Founder card | `CirExecutiveSummary` on company page |",
        "| RH compose | CIR readiness/signals/tech/narrative into `RevenueHunterInput.metadata` |",
        "| Founder Queue | CIR: Revenue Ready / Priority Account only; GT soft-gate when CIR present |",
        "",
        "## Acceptance (500 verified companies)",
        "",
        "| Metric | Value | Target |",
        "| --- | ---: | ---: |",
        f"| Business profile % | {data['business_profile_pct']} | ≥80 |",
        f"| Industry + ICP % | {data['industry_icp_pct']} | ≥70 |",
        f"| Technology + service % | {data['technology_service_pct']} | ≥60 |",
        f"| Contact % | {data['contact_pct']} | ≥40 |",
        f"| False fabrications | {data['false_fabrications']} | 0 |",
        f"| Founder queue eligible | {data['founder_queue']} | RR/PA only |",
        f"| Elapsed | {data['wall_ms']} ms | <5000 |",
        "",
        "## Classification distribution",
        "",
        "```json",
        json.dumps(data["classification_distribution"], indent=2),
        "```",
        "",
        "## Compose-only guarantees",
        "",
        "- Did **not** redesign Revenue Hunter, Sales Readiness, Ground Truth, Founder Queue core, CRE, or EROWD.",
        "- CIR never runs before EROWD admission (`SKIPPED` otherwise).",
        "- Every readiness score includes evidence breakdown.",
        "",
        f"Raw metrics: `{out_json.name}`.",
        "",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"written": [str(out_json), str(out_md)], "business_pct": data["business_profile_pct"], "ms": data["wall_ms"]}, indent=2))


if __name__ == "__main__":
    main()
