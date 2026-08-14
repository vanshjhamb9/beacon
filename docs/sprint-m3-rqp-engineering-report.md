# Sprint M3 Engineering Report — Revenue Quality Recovery (RQP v1)

**Date:** 2026-07-24  
**Objective:** Stop measuring software. Start measuring revenue. Every company is **REJECTED** or **SALES READY** — no middle state on founder/revenue surfaces.

## Verdict

RQP v1 (`rqp-v1`) enforces a binary revenue gate with contact waterfall enrichment, website crawl extraction, identity validation before admit, attributed evidence panels, duplicate merge keys, one-page company profiles, daily KPIs, a 500-company Beacon Gold Dataset, and a production-send acceptance lock.

## North star

> After M3, stop building infrastructure. Next is real sales — Gmail, WhatsApp, outreach on 20–50 verified accounts, measure replies.

## Rules implemented

| Rule | Engine |
|---|---|
| 1 Binary sales-ready requirements | `SalesReadyGateEngine` |
| 2 Contact waterfall | `ContactWaterfallEngine` |
| 3 Website crawler | `WebsiteCrawlerEngine` |
| 4 Identity before create | `IdentityValidatorEngine` |
| 5 Contact confidence attribution | `ContactConfidenceEngine` |
| 6 Evidence panel | `EvidencePanelEngine` |
| 7 Duplicate recovery | `DuplicateRecoveryEngine` |
| 8 Company profile | `CompanyProfileBuilder` |
| 9 Surface readiness (hide rest) | `SurfaceReadinessEngine` |
| 10 Daily KPI | `DailyKpiEngine` |
| 11 Golden dataset (500) | `GoldenDatasetEngine` |
| 12 Acceptance / production unlock | `AcceptanceEngine` |

## Package

`packages/revenue_quality_recovery/`

Pipeline: `RevenueQualityPipeline.evaluate(payload) → RqpSnapshot` with verdict `REJECTED | SALES_READY`.

## Migration

`20260724_0033` → `rqp_snapshots`, `rqp_daily_kpis`, `rqp_acceptance_gates`, `rqp_golden_dataset`

## API

`/api/v1/revenue-quality/*`

- company get/evaluate
- founder-queue (Sales Ready only)
- kpi / acceptance / dashboard
- golden-dataset/seed
- process-pending

## Worker

- `revenue_quality.process_pending` @ 127s
- `revenue_quality.daily_kpi` @ 86400s

## UI

`/revenue-quality` — internal QA (KPI + acceptance lock + founder preview)

## Production lock

`PRODUCTION_SEND_ENABLED = False` until acceptance criteria pass (≥95% identity, ≥90% websites, ≥70% emails, ≥50% phone/alt, dup &lt;10%, fake &lt;1%, evidence attribution, founder queue sales-ready only, ≥50 outreach-ready, 100-lead manual review ≥95%).

## Tests

`tests/revenue_quality_recovery/` — 500+ cases (unit matrix + contracts).

## Follow-ups

1. Apply Alembic `20260724_0033`
2. `POST /revenue-quality/golden-dataset/seed`
3. `POST /revenue-quality/process-pending?limit=200`
4. Manual review sample of 100 leads → feed accuracy into `/acceptance`
5. Only then unlock Gmail / WhatsApp production send
