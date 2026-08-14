# Sprint 30 — Entity Resolution & Official Website Discovery (EROWD v1)

## Mission

Rebuild Beacon's identity layer so a company is never created without a verified official website.

> KPI: How many real companies with verified official websites become genuinely Sales Ready each day?

## Flow

```
Signal → Entity Resolution → Official Website Discovery → Identity Verification → Company Creation
```

## Absolute rules

1. No official website → remains a signal (not a company).
2. Never guess / fabricate / autocomplete / infer domains.
3. Every website stores attribution (source, confidence, verified_at, collector).
4. One canonical website per company — platforms are evidence, not identity.

## Delivered

| Area | Path |
| --- | --- |
| Package | `packages/entity_resolution/` (`erowd-v1`) |
| Migration | `20260724_0037` — 8 append-only EROWD tables |
| API | `/entity-resolution/*` |
| Dashboard | `/entity-resolution` |
| Founder view | Official Website / Verified / Confidence / Evidence first on company page |
| Collectors | Product Hunt official homepage; GitHub repo homepage; RSS org website only |
| Gate | `IntelligenceService` → EROWD admit required (`erowd_rejected` otherwise) |

## Benchmark (synthetic corpus)

| Metric | Value | Target |
| --- | ---: | ---: |
| Signals | 1800 | 1000+ |
| Entity candidates | 1000 | 150 |
| Official websites | 200 | 120 |
| Verified companies | 200 | 100 |
| Sales-ready | 0 | 40 (downstream) |
| Discovery rate | 11.11% | — |
| Verification rate | 100.0% | — |
| False positives | 0 | 0 |
| Admitted | 200 | — |
| Rejected / signal-only | 1600 | — |

## Identity confidence distribution

```json
{
  "0-49": 1600,
  "50-69": 0,
  "70-89": 0,
  "90-100": 200
}
```

## Source precision

```json
{
  "product_hunt": {
    "signals": 500,
    "admitted": 120,
    "websites_found": 120,
    "precision_pct": 24.0
  },
  "github_trending": {
    "signals": 500,
    "admitted": 80,
    "websites_found": 80,
    "precision_pct": 16.0
  },
  "rss": {
    "signals": 200,
    "admitted": 0,
    "websites_found": 0,
    "precision_pct": 0.0
  },
  "reddit": {
    "signals": 200,
    "admitted": 0,
    "websites_found": 0,
    "precision_pct": 0.0
  },
  "hacker_news": {
    "signals": 200,
    "admitted": 0,
    "websites_found": 0,
    "precision_pct": 0.0
  },
  "devto": {
    "signals": 200,
    "admitted": 0,
    "websites_found": 0,
    "precision_pct": 0.0
  }
}
```

## Notes

- Reddit and Hacker News are **signal-only** — never companies.
- Product Hunt listing URLs (`producthunt.com/posts/...`) are never identity; official homepage must come from evidence.
- GitHub repo URLs are never identity; only repository homepage / org website when present.
- RSS articles without an organization website remain article-only signals.
- Sales Readiness remains a downstream consumer — EROWD only admits verified-website companies.
- Dual gate: EROWD is primary; CRE soft-bypass after EROWD admit (documented intentional).

## Raw metrics

See `sprint-30-erowd-live-report.json`.
