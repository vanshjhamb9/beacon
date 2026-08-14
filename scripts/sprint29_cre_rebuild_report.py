"""Sprint 29 — rebuild companies from raw signals via CRE (offline report).

Does not trust existing company identities. Evaluates raw_events through CRE v1
and writes the acceptance deliverable report.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "apps" / "api"), str(ROOT / "packages"), str(ROOT)]

REPORT_JSON = ROOT / "docs" / "sprint-29-cre-live-report.json"
REPORT_MD = ROOT / "docs" / "sprint-29-company-resolution-report.md"


async def main() -> None:
    import asyncpg

    from company_resolution.pipelines.engine import CompanyResolutionPipeline
    from company_resolution.rebuild.engine import CreRebuildEngine

    conn = await asyncpg.connect(
        host="127.0.0.1",
        database="beacon",
        user="beacon",
        password="beacon_password",
        timeout=5,
        command_timeout=120,
    )
    try:
        total_signals = await conn.fetchval("SELECT COUNT(*) FROM raw_events WHERE deleted_at IS NULL")
        rows = await conn.fetch(
            """
            SELECT id::text, source, url, title, content, published_at, metadata
            FROM raw_events
            WHERE deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT 1000
            """
        )
        pipe = CompanyResolutionPipeline()
        snaps = []
        ph_fetch_budget = 0
        for r in rows:
            meta = r["metadata"] or {}
            if isinstance(meta, str):
                meta = json.loads(meta)
            domains = []
            if meta.get("domain") and "producthunt" not in str(meta.get("domain")).lower():
                domains = [meta["domain"]]
            fetch_ph = False
            if r["source"] == "product_hunt" and ph_fetch_budget < 25:
                fetch_ph = True
                ph_fetch_budget += 1
            snap = pipe.evaluate(
                {
                    "signal_id": r["id"],
                    "title": r["title"] or "",
                    "body": r["content"] or "",
                    "url": r["url"],
                    "source": r["source"],
                    "timestamp": r["published_at"],
                    "metadata": {**meta, "fetch_product_hunt": fetch_ph},
                    "domains": domains,
                    "mentions": list(meta.get("company_hints") or []),
                    "website_alive": True if domains else None,
                    "fetch_product_hunt": fetch_ph,
                },
                website_payload={"fetch_product_hunt": fetch_ph},
            )
            snaps.append(snap)

        report = CreRebuildEngine().build(snaps)
        payload = report.model_dump(mode="json")
        payload["db_total_raw_signals"] = int(total_signals or 0)
        payload["evaluated"] = len(rows)
        payload["generated_at"] = datetime.now(UTC).isoformat()
        payload["note"] = (
            "Offline CRE evaluation of up to 1000 latest raw signals. "
            "Companies are not written unless /company-resolution/rebuild is run after alembic 0036."
        )
        REPORT_JSON.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

        lines = [
            "# Sprint 29 — Company Resolution Engine (CRE v1)",
            "",
            f"**Generated:** {payload['generated_at']}",
            "",
            "## Mission",
            "",
            "Replace `Signal → Company` with `Signal → Evidence → Identity Resolution → Verification → Company`.",
            "",
            "## Live rebuild metrics (from raw signals)",
            "",
            f"- Total raw signals in DB: **{payload['db_total_raw_signals']}**",
            f"- Evaluated this run: **{payload['evaluated']}**",
            f"- Companies that would be created: **{report.companies_created}**",
            f"- Companies rejected: **{report.companies_rejected}**",
            f"- Verified companies: **{report.verified_companies}**",
            f"- Resolution success rate: **{report.resolution_success_rate}%**",
            "",
            "## Resolution failure reasons",
            "",
        ]
        for k, v in list(report.rejection_reasons.items())[:20]:
            lines.append(f"- **{k}**: {v}")
        lines += ["", "## Identity confidence distribution", ""]
        for k, v in report.identity_confidence_distribution.items():
            lines.append(f"- **{k}**: {v}")
        lines += ["", "## Source-wise precision", ""]
        for src, stats in sorted(report.source_precision.items(), key=lambda x: -float(x[1].get("precision_pct") or 0)):
            lines.append(
                f"- **{src}**: {stats.get('admitted')}/{stats.get('signals')} admitted "
                f"({stats.get('precision_pct')}%)"
            )
        lines += ["", "## Top verified companies (with attribution)", ""]
        for i, c in enumerate(report.top_verified[:50], 1):
            lines.append(
                f"{i}. **{c.get('company')}** — {c.get('domain')} | source={c.get('source')} | "
                f"confidence={c.get('identity_confidence')} | url={c.get('attribution_url')}"
            )
        lines += ["", "## Rejected false-positive examples", ""]
        for ex in report.rejected_examples[:20]:
            lines.append(
                f"- `{ex.get('title')}` ({ex.get('source')}) → **{ex.get('reason')}** "
                f"(identity={ex.get('identity_score')}, domain={ex.get('domain')})"
            )
        lines += [
            "",
            "## Engineering",
            "",
            "| Piece | Path |",
            "|---|---|",
            "| Package | `packages/company_resolution/` (`cre-v1`) |",
            "| Intercept | `IntelligenceService.process_raw_event` — CRE before upsert |",
            "| Migration | `20260724_0036` — `cre_snapshots`, `cre_admission_decisions`, `cre_rebuild_reports` |",
            "| API | `/company-resolution/*` |",
            "| Worker | `company_resolution.rebuild` |",
            "",
            "## Acceptance target vs actual",
            "",
            "| Funnel | Target | Actual (this eval) |",
            "|---|---:|---:|",
            f"| Signals | 1000 | {payload['evaluated']} |",
            f"| Real companies | 150 | {report.resolved_companies} |",
            f"| Verified | 100 | {report.verified_companies} |",
            f"| Sales Ready | 40 | {report.sales_ready} (requires downstream SRE; CRE only admits identity) |",
            "",
            "CRE stops fake company creation. Sales Ready still requires contact/intent enrichment after admit.",
            "",
        ]
        REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"signals={payload['evaluated']} created={report.companies_created} rejected={report.companies_rejected}")
        print(f"Wrote {REPORT_MD}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
