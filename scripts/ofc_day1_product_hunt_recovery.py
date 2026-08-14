"""OFC Day 1 — Product Hunt official site + public contact recovery.

Mission: increase Revenue Ready companies via PH recovery only.
No new engines. Measures live funnel against OFC acceptance ladder.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for _p in (
    ROOT / "apps" / "api",
    ROOT / "apps" / "worker",
    ROOT / "packages",
    ROOT,
):
    sys.path.insert(0, str(_p))

REPORT_JSON = ROOT / "docs" / "ofc-day1-product-hunt-live-report.json"
REPORT_MD = ROOT / "docs" / "ofc-day1-product-hunt-engineering-report.md"


async def _collect_ph_sample(max_items: int = 40) -> dict[str, Any]:
    import httpx
    import os

    from collectors.sources.product_hunt import ProductHuntCollector

    feeds = ["https://www.producthunt.com/feed"]
    # Optional override from env (JSON list or comma-separated)
    raw = os.getenv("PRODUCT_HUNT_COLLECTOR__FEED_URLS") or ""
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list) and parsed:
                feeds = [str(x) for x in parsed]
        except json.JSONDecodeError:
            pass
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        collector = ProductHuntCollector(client, feed_urls=feeds, max_items=max_items)
        events = await collector.collect()

    recovered = 0
    with_email = 0
    with_dm = 0
    with_phone = 0
    with_linkedin = 0
    skipped = 0
    samples: list[dict[str, Any]] = []

    for event in events:
        meta = event.metadata or {}
        if meta.get("ofc_skip_company"):
            skipped += 1
            continue
        if not meta.get("ofc_product_hunt_recovered"):
            continue
        recovered += 1
        if meta.get("business_email") or (meta.get("emails") or []):
            with_email += 1
        if meta.get("decision_maker") or (meta.get("decision_makers") or []):
            with_dm += 1
        if meta.get("phone") or (meta.get("phones") or []):
            with_phone += 1
        if meta.get("linkedin") or meta.get("linkedin_company"):
            with_linkedin += 1
        if len(samples) < 12:
            samples.append(
                {
                    "title": event.title,
                    "official_website": meta.get("official_website"),
                    "domain": meta.get("domain"),
                    "business_email": meta.get("business_email"),
                    "decision_maker": meta.get("decision_maker"),
                    "phone": meta.get("phone"),
                    "linkedin": meta.get("linkedin") or meta.get("linkedin_company"),
                    "about": (meta.get("about") or "")[:160],
                }
            )

    return {
        "collected": len(events),
        "recovered_official_website": recovered,
        "skipped_no_website": skipped,
        "with_business_email": with_email,
        "with_decision_maker": with_dm,
        "with_phone": with_phone,
        "with_linkedin": with_linkedin,
        "samples": samples,
    }


def _live_db_kpis() -> dict[str, Any]:
    """Best-effort KPI read from DB + rev acceptance if available."""
    import os

    out: dict[str, Any] = {"db_available": False}
    try:
        from sqlalchemy import create_engine, text

        url = (
            os.getenv("DATABASE_URL")
            or os.getenv("BEACON_DATABASE_URL")
            or "postgresql://beacon:beacon@127.0.0.1:5432/beacon"
        ).replace("+asyncpg", "")
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            out["db_available"] = True
            out["companies_active"] = int(
                conn.execute(
                    text("SELECT COUNT(*) FROM companies WHERE deleted_at IS NULL")
                ).scalar()
                or 0
            )
            # Official website / domain presence
            out["with_primary_domain"] = int(
                conn.execute(
                    text(
                        "SELECT COUNT(*) FROM companies "
                        "WHERE deleted_at IS NULL AND primary_domain IS NOT NULL AND primary_domain <> ''"
                    )
                ).scalar()
                or 0
            )
            # Business emails from company_contacts if table exists
            try:
                out["business_emails"] = int(
                    conn.execute(
                        text(
                            "SELECT COUNT(DISTINCT company_id) FROM company_contacts "
                            "WHERE deleted_at IS NULL AND kind IN ('email','business_email') "
                            "AND value IS NOT NULL AND value <> ''"
                        )
                    ).scalar()
                    or 0
                )
            except Exception:
                out["business_emails"] = None
            try:
                out["ph_raw_events_7d"] = int(
                    conn.execute(
                        text(
                            "SELECT COUNT(*) FROM raw_events WHERE source = 'product_hunt' "
                            "AND created_at > NOW() - INTERVAL '7 days' AND deleted_at IS NULL"
                        )
                    ).scalar()
                    or 0
                )
            except Exception:
                out["ph_raw_events_7d"] = None
    except Exception as exc:  # noqa: BLE001
        out["db_error"] = str(exc)[:240]
    return out


def _rev_acceptance() -> dict[str, Any]:
    try:
        from revenue_execution_validation.acceptance.engine import AcceptanceGateEngine
        from revenue_execution_validation.rebuild.engine import RevenueExecutionRebuildEngine

        # Prefer reading existing dashboard snapshot if service layer exposes it lightly
        rebuild = RevenueExecutionRebuildEngine()
        # Some installs expose evaluate_acceptance on gate only — keep soft
        if hasattr(rebuild, "latest_acceptance"):
            return dict(rebuild.latest_acceptance() or {})
        gate = AcceptanceGateEngine()
        if hasattr(gate, "evaluate_empty"):
            return {"note": "acceptance engine present; run API /acceptance for live gates"}
        return {"note": "acceptance package importable"}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)[:240]}


def write_report(collect: dict[str, Any], db: dict[str, Any], acceptance: dict[str, Any]) -> dict[str, Any]:
    ladder = {
        "target_100_real_companies": 100,
        "target_50_verified_websites": 50,
        "target_40_business_emails": 40,
        "target_25_decision_makers": 25,
        "target_20_revenue_ready": 20,
        "target_10_founder_queue": 10,
        "target_5_emails_sent": 5,
        "target_1_meeting": 1,
        "day1_ph_recovered_websites": collect.get("recovered_official_website"),
        "day1_ph_emails_on_site": collect.get("with_business_email"),
        "day1_ph_decision_makers": collect.get("with_decision_maker"),
        "db_companies_active": db.get("companies_active"),
        "db_with_primary_domain": db.get("with_primary_domain"),
        "db_business_emails": db.get("business_emails"),
    }
    payload = {
        "mission": "OFC Day 1 — Product Hunt recovery",
        "generated_at": datetime.now(UTC).isoformat(),
        "collector_sample": collect,
        "live_db": db,
        "acceptance": acceptance,
        "ladder": ladder,
        "policy": {
            "enabled_collectors": ["product_hunt", "github_trending", "devto"],
            "disabled_collectors": ["rss", "hacker_news", "reddit", "indie_hackers", "sec_edgar"],
            "erowd_signal_only": ["reddit", "hacker_news", "rss", "indie_hackers", "sec_edgar"],
        },
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    c = collect
    md = f"""# OFC Day 1 — Product Hunt Recovery

## Mission

Increase **Revenue Ready Companies** by recovering official websites + public contacts from Product Hunt.
No new engines. Feature-complete Beacon; revenue machine mode.

## Collector sample (live feed)

| Metric | Count |
| --- | ---: |
| PH events collected | {c.get("collected")} |
| Official website recovered | {c.get("recovered_official_website")} |
| Skipped (no official website) | {c.get("skipped_no_website")} |
| Business email on site | {c.get("with_business_email")} |
| Named decision maker on site | {c.get("with_decision_maker")} |
| Phone on site | {c.get("with_phone")} |
| LinkedIn on site | {c.get("with_linkedin")} |

## Live DB snapshot

| Metric | Value |
| --- | ---: |
| Active companies | {db.get("companies_active")} |
| With primary domain | {db.get("with_primary_domain")} |
| Distinct business emails | {db.get("business_emails")} |
| PH raw events (7d) | {db.get("ph_raw_events_7d")} |

## Engineering shipped (Day 1)

- Product Hunt collector: official site via EROWD discovery + public contact crawl
- `ofc_skip_company` honored in `ErowdPipeline.evaluate` (no company without official site)
- Weak sources signal-only: RSS / HN / Reddit / Indie Hackers / SEC
- Collectors disabled in `.env` for those sources; PH / GitHub / Dev.to enabled
- CTO Console `/cto`, OFC company one-pager, Founder Queue Top 10 (send LOCKED)

## OFC ladder (honest)

Day 1 measures **PH recovery capacity**. Full ladder (100→50→40→25→20→10→5→1) requires Days 2–N (DM discovery, email verify, send).

Raw: `ofc-day1-product-hunt-live-report.json`
"""
    REPORT_MD.write_text(md, encoding="utf-8")
    return payload


async def main() -> None:
    print("OFC Day 1: collecting Product Hunt sample…", flush=True)
    collect = await _collect_ph_sample(40)
    print(json.dumps({k: v for k, v in collect.items() if k != "samples"}, indent=2), flush=True)
    db = _live_db_kpis()
    acceptance = _rev_acceptance()
    payload = write_report(collect, db, acceptance)
    print(f"Wrote {REPORT_JSON}", flush=True)
    print(f"Wrote {REPORT_MD}", flush=True)
    print(
        f"Day1 PH recovered websites={collect.get('recovered_official_website')} "
        f"emails={collect.get('with_business_email')} dms={collect.get('with_decision_maker')}",
        flush=True,
    )
    _ = payload


if __name__ == "__main__":
    asyncio.run(main())
