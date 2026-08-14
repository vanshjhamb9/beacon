"""Pre-launch simulation: freshness gate + Lead Quality Score before live outreach.

Runs synthetic fixtures + optional live HN/Reddit/PH RSS pulls.
Writes JSON report to docs/lead-quality-simulation-report.json
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(ROOT / "apps" / "api"),
    str(ROOT / "apps" / "worker"),
    str(ROOT / "packages"),
    str(ROOT),
]


def _fixtures() -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    return [
        {
            "id": "perfect_ph_launch",
            "company_name": "Nova Health",
            "source": "product_hunt",
            "website": "https://novahealth.io",
            "official_website": "https://novahealth.io",
            "primary_domain": "novahealth.io",
            "industry": "Healthcare SaaS",
            "description": "AI patient intake for clinics",
            "business_email": "founders@novahealth.io",
            "decision_maker": "James Lee (Founder)",
            "why_now": "Recent product launch signal",
            "buying_signals": ["Product Hunt launch signal: Nova Health"],
            "evidence": ["PH launch today"],
            "website_verified": True,
            "published_at": now - timedelta(hours=5),
            "attributes": {"source": "product_hunt", "source_kind": "event", "lead_eligible": True},
            "expect_perfect": True,
            "expect_outbound": True,
        },
        {
            "id": "good_hn_hiring",
            "company_name": "CircuitOps",
            "source": "hacker_news",
            "website": "https://circuitops.com",
            "official_website": "https://circuitops.com",
            "industry": "DevTools",
            "description": "Ops automation for SaaS",
            "business_email": "hello@circuitops.com",
            "decision_maker": "Priya Shah",
            "why_now": "Hiring / growth signal",
            "buying_signals": ["HN: We're hiring ops engineers"],
            "website_verified": True,
            "published_at": now - timedelta(hours=18),
            "attributes": {"source": "hacker_news", "source_kind": "event"},
            "expect_perfect": False,
            "expect_outbound": True,
        },
        {
            "id": "stale_ok_company",
            "company_name": "OldCo",
            "source": "product_hunt",
            "website": "https://oldco.com",
            "business_email": "hi@oldco.com",
            "decision_maker": "Alex",
            "why_now": "Recent product launch signal",
            "buying_signals": ["Product Hunt launch"],
            "published_at": now - timedelta(hours=72),
            "attributes": {"source": "product_hunt", "source_kind": "event"},
            "expect_perfect": False,
            "expect_outbound": False,
        },
        {
            "id": "yc_directory_fake_fresh",
            "company_name": "LegacyYC",
            "source": "yc",
            "website": "https://legacyyc.com",
            "business_email": "team@legacyyc.com",
            "decision_maker": "Founder",
            "why_now": "YC portfolio company (Summer 2015) — expansion / growth context",
            "buying_signals": ["YC company directory: Summer 2015"],
            "published_at": now,
            "attributes": {"source": "yc", "source_kind": "directory", "lead_eligible": False},
            "expect_perfect": False,
            "expect_outbound": False,
        },
        {
            "id": "article_only_news",
            "company_name": "TechCrunch Blurb",
            "source": "rss",
            "why_now": "Funding / capital event",
            "buying_signals": ["Series A mentioned in article"],
            "published_at": now - timedelta(hours=3),
            "article_only": True,
            "attributes": {"source": "rss", "source_kind": "event"},
            "expect_perfect": False,
            "expect_outbound": False,
        },
        {
            "id": "fresh_weak_contacts",
            "company_name": "SparkAI",
            "source": "product_hunt",
            "website": "https://sparkai.dev",
            "official_website": "https://sparkai.dev",
            "why_now": "Recent product launch signal",
            "buying_signals": ["Product Hunt launch signal: SparkAI"],
            "website_verified": True,
            "published_at": now - timedelta(hours=8),
            "attributes": {"source": "product_hunt", "source_kind": "event"},
            "expect_perfect": False,  # no email/DM → not perfect
            "expect_outbound": False,  # needs contacts for outbound bar
        },
    ]


def _score_fixture(row: dict[str, Any]) -> dict[str, Any]:
    from lead_quality import LeadQualityScorer

    result = LeadQualityScorer().score(row)
    ok_outbound = result.outbound_ready == bool(row["expect_outbound"])
    ok_perfect = result.perfect == bool(row["expect_perfect"])
    return {
        "id": row["id"],
        "company": row.get("company_name"),
        "lqs": result.as_dict(),
        "expect_outbound": row["expect_outbound"],
        "expect_perfect": row["expect_perfect"],
        "pass_outbound_assert": ok_outbound,
        "pass_perfect_assert": ok_perfect,
        "pass": ok_outbound and ok_perfect,
    }


async def _resolve_website(client: Any, meta: dict[str, Any], title: str, url: str) -> str | None:
    from urllib.parse import urlparse

    from intelligence.entity_resolution.platform_domains import is_platform_domain

    candidates = [
        meta.get("official_website"),
        meta.get("homepage"),
        meta.get("organization_website"),
        meta.get("ph_redirect_url"),
    ]
    # Show HN / GitHub links sometimes embed project URL in content metadata
    for key in ("canonical_url", "url"):
        candidates.append(meta.get(key))

    for cand in candidates:
        if not cand:
            continue
        try:
            resp = await client.head(str(cand), follow_redirects=True)
            final = str(resp.url)
            host = urlparse(final).netloc.lower().removeprefix("www.")
            if host and not is_platform_domain(host) and "producthunt.com" not in host:
                return f"https://{host}"
        except Exception:  # noqa: BLE001
            continue
    return None


async def _live_collect() -> dict[str, Any]:
    import httpx

    from collectors.freshness import FRESH_HOURS, filter_fresh_events
    from collectors.sources.hacker_news import HackerNewsCollector
    from collectors.sources.product_hunt import ProductHuntCollector
    from collectors.sources.reddit import RedditCollector
    from lead_quality import LeadQualityScorer

    report: dict[str, Any] = {"sources": {}, "candidates": []}
    scorer = LeadQualityScorer()

    async with httpx.AsyncClient(timeout=40.0, follow_redirects=True) as client:
        collectors = [
            (
                "hacker_news",
                HackerNewsCollector(
                    client,
                    feed_urls=[
                        "https://hnrss.org/newest?q=hiring+OR+funding+OR+launch+OR+SaaS",
                        "https://hnrss.org/frontpage",
                    ],
                    max_items=20,
                ),
            ),
            (
                "product_hunt",
                ProductHuntCollector(
                    client,
                    feed_urls=["https://www.producthunt.com/feed"],
                    max_items=15,
                ),
            ),
            (
                "reddit",
                RedditCollector(
                    client,
                    subreddits=["startups", "SaaS"],
                    max_items=10,
                ),
            ),
        ]
        for name, collector in collectors:
            try:
                events = list(await collector.collect())
                fresh = filter_fresh_events(events, max_age_hours=FRESH_HOURS)
                scored = []
                for ev in fresh[:12]:
                    meta = dict(ev.metadata or {})
                    website = await _resolve_website(client, meta, ev.title, ev.url)
                    payload = {
                        "company_name": ev.title,
                        "source": ev.source,
                        "website": website,
                        "official_website": website,
                        "why_now": (
                            "Recent product launch signal"
                            if ev.source == "product_hunt"
                            else (
                                "Hiring / growth signal"
                                if "hir" in (ev.title + ev.content).lower()
                                else f"Recent {ev.source} signal"
                            )
                        ),
                        "buying_signals": meta.get("buying_signals")
                        or [f"{ev.source}: {ev.title[:120]}"],
                        "published_at": ev.published_at,
                        "article_only": meta.get("article_only") if not website else False,
                        "website_verified": bool(website),
                        "attributes": {
                            **meta,
                            "source": ev.source,
                            "source_kind": "event",
                            "lead_eligible": True,
                            "official_website": website,
                            "domain": (website or "").replace("https://", "").split("/")[0] if website else None,
                        },
                        "content": ev.content[:400],
                        "title": ev.title,
                    }
                    result = scorer.score(payload)
                    scored.append(
                        {
                            "title": ev.title[:120],
                            "source": ev.source,
                            "published_at": ev.published_at.isoformat(),
                            "website": website,
                            "lqs": result.total,
                            "grade": result.grade,
                            "outbound_ready": result.outbound_ready,
                            "perfect": result.perfect,
                            "pipeline_worthy": result.pipeline_worthy,
                            "blockers": result.blockers,
                            "age_hours": result.age_hours,
                        }
                    )
                scored.sort(key=lambda r: r["lqs"], reverse=True)
                report["sources"][name] = {
                    "collected": len(events),
                    "fresh_48h": len(fresh),
                    "outbound": sum(1 for r in scored if r["outbound_ready"]),
                    "perfect": sum(1 for r in scored if r["perfect"]),
                    "pipeline_worthy": sum(1 for r in scored if r["pipeline_worthy"]),
                    "with_website": sum(1 for r in scored if r["website"]),
                    "top": scored[:5],
                }
                report["candidates"].extend(scored)
            except Exception as exc:  # noqa: BLE001
                report["sources"][name] = {"error": str(exc)}

    report["candidates"].sort(key=lambda r: r["lqs"], reverse=True)
    report["summary"] = {
        "live_candidates": len(report["candidates"]),
        "live_outbound": sum(1 for r in report["candidates"] if r["outbound_ready"]),
        "live_perfect": sum(1 for r in report["candidates"] if r["perfect"]),
        "live_pipeline_worthy": sum(1 for r in report["candidates"] if r["pipeline_worthy"]),
        "live_with_website": sum(1 for r in report["candidates"] if r["website"]),
        "top_5": report["candidates"][:5],
    }
    return report


async def main() -> None:
    from collectors.freshness import FRESH_HOURS
    from lead_quality import OUTBOUND_THRESHOLD, PERFECT_THRESHOLD, SCORING_VERSION

    print("=== Lead Quality Pre-Launch Simulation ===")
    print(f"scoring={SCORING_VERSION} fresh<={FRESH_HOURS}h outbound>={OUTBOUND_THRESHOLD} perfect>={PERFECT_THRESHOLD}")

    fixture_rows = [_score_fixture(row) for row in _fixtures()]
    fixture_pass = all(r["pass"] for r in fixture_rows)
    print("\n--- Synthetic fixtures ---")
    for row in fixture_rows:
        status = "PASS" if row["pass"] else "FAIL"
        lqs = row["lqs"]
        print(
            f"  [{status}] {row['id']}: LQS={lqs['total']} grade={lqs['grade']} "
            f"outbound={lqs['outbound_ready']} perfect={lqs['perfect']} blockers={lqs['blockers']}"
        )

    print("\n--- Live collector pull (HN / PH / Reddit) ---")
    live = await _live_collect()
    for source, info in live.get("sources", {}).items():
        if "error" in info:
            print(f"  {source}: ERROR {info['error']}")
        else:
            print(
                f"  {source}: collected={info['collected']} fresh={info['fresh_48h']} "
                f"pipeline={info.get('pipeline_worthy')} websites={info.get('with_website')} "
                f"outbound={info['outbound']} perfect={info['perfect']}"
            )
            for top in info.get("top") or []:
                print(
                    f"    · {top['lqs']:.1f} {top['grade']} | {top['title'][:70]} "
                    f"| age={round(top.get('age_hours') or 0, 1)}h | site={top.get('website') or '-'} "
                    f"| blockers={top['blockers']}"
                )

    summary = live.get("summary") or {}
    print("\n--- Verdict ---")
    print(f"  fixtures_pass={fixture_pass}")
    print(
        f"  live_pipeline_worthy={summary.get('live_pipeline_worthy')} "
        f"live_with_website={summary.get('live_with_website')} "
        f"live_outbound={summary.get('live_outbound')} live_perfect={summary.get('live_perfect')} "
        f"of {summary.get('live_candidates')} scored"
    )

    # Launch bar: fixtures green + enough fresh pipeline fuel (websites recover next)
    launch_ready = fixture_pass and int(summary.get("live_pipeline_worthy") or 0) >= 3
    print(f"  launch_ready_quality_bar={launch_ready}")

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scoring_version": SCORING_VERSION,
        "fresh_hours": FRESH_HOURS,
        "outbound_threshold": OUTBOUND_THRESHOLD,
        "perfect_threshold": PERFECT_THRESHOLD,
        "fixtures": fixture_rows,
        "fixtures_pass": fixture_pass,
        "live": live,
        "launch_ready_quality_bar": launch_ready,
        "cto_notes": [
            "Directory/YC leads must fail",
            "Only <=48h event triggers can outbound",
            "Perfect leads need website + contact + strong trigger + high freshness",
            "pipeline_worthy = fresh trigger fuel for website/email enrichment",
            "Set PRODUCT_HUNT_DEVELOPER_TOKEN for GraphQL website resolution lift",
        ],
    }
    out = ROOT / "docs" / "lead-quality-simulation-report.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nReport: {out}")
    if not fixture_pass:
        raise SystemExit(2)
    if not launch_ready:
        print("WARN: fixtures OK but live pipeline fuel low — check feeds / network")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
