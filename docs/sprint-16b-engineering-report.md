# Sprint 16B Engineering Report — Revenue Hunter Mode

**Mission:** Operation First Client  
**Date:** 2026-07-23  
**Package:** `packages/revenue_hunter/`  
**Scoring version:** `rh-v1`

## Verdict

Beacon now behaves as an AI Business Development Manager for the agency. Every morning recommendation is deterministic, explainable, evidence-backed, and actionable — A+ / A only enter campaigns and the founder work queue by default.

## What shipped

| Step | Deliverable | Status |
|---|---|---|
| 1 | Target Account Filter (country / size / industry / funding / revenue) | Done |
| 2 | Service Match Engine (11 Beacon services + confidence) | Done |
| 3 | Pain Point Engine (evidence-required top problems) | Done |
| 4 | Website Intelligence (CWV / SEO / a11y / stack / opportunities) | Done |
| 5 | Why Now Engine V2 (why company / today / us / budget / timeline / probability / evidence) | Done |
| 6 | Revenue Dossier (full BD pack in one object) | Done |
| 7 | Automatic Prioritization (A+→D, campaign gate) | Done |
| 8 | Founder Dashboard (targets, top 25, pipeline, queues) | Done |
| 9 | Work Queue (Approve / Send / Reply / Book Meeting) | Done |
| 10 | Tests (unit / pipeline / API / migration / performance / regression / integration) | Done |

## Files

### Package
- `packages/revenue_hunter/__init__.py`
- `packages/revenue_hunter/models/types.py`
- `packages/revenue_hunter/filters/{taxonomy,engine}.py`
- `packages/revenue_hunter/matching/service_match.py`
- `packages/revenue_hunter/pain/engine.py`
- `packages/revenue_hunter/website/intelligence.py`
- `packages/revenue_hunter/why_now/engine_v2.py`
- `packages/revenue_hunter/dossier/builder.py`
- `packages/revenue_hunter/prioritization/engine.py`
- `packages/revenue_hunter/queue/work_queue.py`
- `packages/revenue_hunter/dashboard/founder.py`
- `packages/revenue_hunter/pipelines/revenue_hunter_pipeline.py`
- `packages/revenue_hunter/services/engine.py`
- `packages/revenue_hunter/repository/protocols.py`

### API / persistence
- `apps/api/app/models/revenue_hunter.py`
- `apps/api/app/repositories/revenue_hunter.py`
- `apps/api/app/services/revenue_hunter.py`
- `apps/api/app/schemas/revenue_hunter.py`
- `apps/api/app/api/routes/revenue_hunter.py`
- `apps/api/alembic/versions/20260723_0017_create_revenue_hunter_tables.py`
- Config gates in `apps/api/app/core/config.py`

### Worker
- `apps/worker/worker/revenue_hunter_tasks.py`
- Beat entry `process-revenue-hunter` @ 132s in `celery_app.py`

### Dashboard
- `apps/dashboard/features/revenue-hunter/revenue-hunter-workspace.tsx`
- `apps/dashboard/app/(workspace)/revenue-hunter/page.tsx`
- Sidebar + `beacon.ts` client methods

### Docs / tests
- `docs/revenue-hunter.md`
- `docs/sprint-16b-engineering-report.md`
- `tests/revenue_hunter/test_*.py` (7 modules)

## Tests

```text
17 passed in ~2.7s
```

| Suite | Coverage |
|---|---|
| `test_components` | Filter taxonomy, service match, pain, website, why-now v2, prioritization |
| `test_pipeline` | Full dossier + campaign gate + work queue + dashboard |
| `test_api` | OpenAPI route registration |
| `test_migration` | Model tablenames + migration 0017 contract |
| `test_performance` | 100 companies < 2.5s |
| `test_regression_e2e` | Determinism, multi-service reachability, A-grade gate |
| `test_integration` | Service facade + founder dashboard composition |

## Coverage (engine)

Weighted score components (`rh-v1`):

| Component | Weight |
|---|---|
| Filter | 15% |
| Service match | 20% |
| Pain | 15% |
| Website opportunity | 10% |
| Why-now probability | 20% |
| Upstream opportunity | 10% |
| Access (DM + verification) | 10% |

## Migration

- **Revision:** `20260723_0017`
- **Revises:** `20260720_0016`
- **Tables:** `revenue_hunter_dossiers`, `revenue_hunter_work_queue`, `revenue_hunter_daily_briefs`

```bash
cd apps/api
python -m alembic -c alembic.ini upgrade head
```

## Dashboard

Route: `/revenue-hunter`

Surfaces:
- Today's Top Opportunities (work queue)
- Expected revenue / pipeline
- Meetings / campaign / reply / follow-up / hot counts
- Top 25 ranked companies
- Inline revenue dossier (proposal + pain + why-now)

## Performance

- Pure pipeline: **100 evaluations < 2.5s** (local unit budget)
- Worker batch default: 40 opportunities / tick
- Deterministic: identical inputs → identical scores / grades / services

## Remaining work

1. **Live CWV fetch** — website engine currently consumes `website_metrics` / enrichment payload; wire real Lighthouse / CrUX connector.
2. **Campaign gate handoff** — optionally require `proceed_to_campaign` from Revenue Hunter (not only TAI top tier) before `campaign_intelligence` creates campaigns.
3. **Reply / meeting sync** — map communication_gateway replies and calendar bookings into work-queue status automatically.
4. **Portfolio case-study CMS** — replace static `CASE_STUDIES` map with curated agency wins.
5. **Founder notification** — morning Slack/email brief from `revenue_hunter_daily_briefs`.
6. **DB-backed integration tests** — current API tests assert route registration only (matches TAI pattern).

## Success criteria

| Criterion | Met |
|---|---|
| Morning “who to contact” work queue | Yes |
| No random leads — filter + A+/A gate | Yes |
| Service pitch with confidence | Yes |
| Pain points with evidence | Yes |
| Website improvement opportunities | Yes |
| Why Now V2 structured + evidence chain | Yes |
| Full revenue dossier | Yes |
| Deterministic / explainable / actionable | Yes |
