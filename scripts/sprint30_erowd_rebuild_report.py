"""Sprint 30 — EROWD live rebuild report (offline-safe + optional DB)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT / "apps" / "api"))

from entity_resolution.pipelines.engine import ErowdPipeline
from entity_resolution.rebuild.engine import ErowdRebuildEngine


def _synthetic_corpus():
    signals = []
    for i in range(500):
        with_site = i < 120
        domain = f"product{i}.io"
        p = {
            "signal_id": f"ph-{i}",
            "title": f"Product{i} — AI ops",
            "body": f"Product{i} automates enterprise workflows.",
            "url": f"https://www.producthunt.com/posts/product{i}",
            "source": "product_hunt",
            "metadata": {"company_hints": [f"Product{i}"]},
            "industry": "Software",
        }
        if with_site:
            p["official_website"] = f"https://{domain}"
            p["metadata"]["official_website"] = f"https://{domain}"
            p["website_verified"] = True
            p["website_title"] = f"Product{i}"
        signals.append(p)
    for i in range(500):
        with_site = i < 80
        p = {
            "signal_id": f"gh-{i}",
            "title": f"GitHub: org{i}/repo{i}",
            "body": f"Org{i} toolkit",
            "url": f"https://github.com/org{i}/repo{i}",
            "source": "github_trending",
            "metadata": {"company_hints": [f"Org{i}"]},
            "industry": "Software",
        }
        if with_site:
            p["github_homepage"] = f"https://org{i}.dev"
            p["metadata"]["repo_homepage"] = f"https://org{i}.dev"
            p["website_verified"] = True
            p["website_title"] = f"Org{i}"
        signals.append(p)
    for i in range(200):
        signals.append(
            {
                "signal_id": f"rss-{i}",
                "title": f"Article {i}",
                "body": "news",
                "url": f"https://example.com/a/{i}",
                "source": "rss",
                "metadata": {"article_only": True},
            }
        )
    for i in range(200):
        signals.append(
            {
                "signal_id": f"rd-{i}",
                "title": f"thread {i}",
                "body": "x",
                "url": f"https://reddit.com/r/x/{i}",
                "source": "reddit",
            }
        )
    for i in range(200):
        signals.append(
            {
                "signal_id": f"hn-{i}",
                "title": f"Ask HN {i}",
                "body": "x",
                "url": f"https://news.ycombinator.com/item?id={i}",
                "source": "hacker_news",
            }
        )
    for i in range(200):
        signals.append(
            {
                "signal_id": f"dv-{i}",
                "title": f"post {i}",
                "body": "x",
                "url": f"https://dev.to/u/{i}",
                "source": "devto",
            }
        )
    return signals


def main() -> None:
    pipe = ErowdPipeline()
    snaps = [pipe.evaluate(s) for s in _synthetic_corpus()]
    report = ErowdRebuildEngine().build(snaps)
    data = report.model_dump(mode="json")

    out_json = ROOT / "docs" / "sprint-30-erowd-live-report.json"
    out_md = ROOT / "docs" / "sprint-30-erowd-engineering-report.md"
    out_json.write_text(json.dumps(data, indent=2), encoding="utf-8")

    lines = [
        "# Sprint 30 — Entity Resolution & Official Website Discovery (EROWD v1)",
        "",
        "## Mission",
        "",
        "Rebuild Beacon's identity layer so a company is never created without a verified official website.",
        "",
        "> KPI: How many real companies with verified official websites become genuinely Sales Ready each day?",
        "",
        "## Flow",
        "",
        "```",
        "Signal → Entity Resolution → Official Website Discovery → Identity Verification → Company Creation",
        "```",
        "",
        "## Absolute rules",
        "",
        "1. No official website → remains a signal (not a company).",
        "2. Never guess / fabricate / autocomplete / infer domains.",
        "3. Every website stores attribution (source, confidence, verified_at, collector).",
        "4. One canonical website per company — platforms are evidence, not identity.",
        "",
        "## Delivered",
        "",
        "| Area | Path |",
        "| --- | --- |",
        "| Package | `packages/entity_resolution/` (`erowd-v1`) |",
        "| Migration | `20260724_0037` — 8 append-only EROWD tables |",
        "| API | `/entity-resolution/*` |",
        "| Dashboard | `/entity-resolution` |",
        "| Founder view | Official Website / Verified / Confidence / Evidence first on company page |",
        "| Collectors | Product Hunt official homepage; GitHub repo homepage; RSS org website only |",
        "| Gate | `IntelligenceService` → EROWD admit required (`erowd_rejected` otherwise) |",
        "",
        "## Benchmark (synthetic corpus)",
        "",
        "| Metric | Value | Target |",
        "| --- | ---: | ---: |",
        f"| Signals | {data['total_signals']} | 1000+ |",
        f"| Entity candidates | {data['entity_candidates']} | 150 |",
        f"| Official websites | {data['official_websites']} | 120 |",
        f"| Verified companies | {data['verified_companies']} | 100 |",
        f"| Sales-ready | {data['sales_ready']} | 40 (downstream) |",
        f"| Discovery rate | {data['discovery_rate']}% | — |",
        f"| Verification rate | {data['verification_rate']}% | — |",
        f"| False positives | {data['false_positives']} | 0 |",
        f"| Admitted | {data['admitted']} | — |",
        f"| Rejected / signal-only | {data['rejected']} | — |",
        "",
        "## Identity confidence distribution",
        "",
        "```json",
        json.dumps(data["identity_confidence_distribution"], indent=2),
        "```",
        "",
        "## Source precision",
        "",
        "```json",
        json.dumps(data["source_precision"], indent=2),
        "```",
        "",
        "## Notes",
        "",
        "- Reddit and Hacker News are **signal-only** — never companies.",
        "- Product Hunt listing URLs (`producthunt.com/posts/...`) are never identity; official homepage must come from evidence.",
        "- GitHub repo URLs are never identity; only repository homepage / org website when present.",
        "- RSS articles without an organization website remain article-only signals.",
        "- Sales Readiness remains a downstream consumer — EROWD only admits verified-website companies.",
        "- Dual gate: EROWD is primary; CRE soft-bypass after EROWD admit (documented intentional).",
        "",
        "## Raw metrics",
        "",
        f"See `{out_json.name}`.",
        "",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"written": [str(out_json), str(out_md)], "admitted": data["admitted"], "verified": data["verified_companies"]}, indent=2))


if __name__ == "__main__":
    main()
