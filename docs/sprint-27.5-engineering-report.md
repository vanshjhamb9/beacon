# Sprint 27.5 Engineering Report — Operational Hardening (Runtime Recovery)

**Date:** 2026-07-23  
**Objective:** Transform Beacon from feature-complete modules into a continuously running Revenue Intelligence System — **no new business features**.

## Verdict

Sprint 27.5 restores Redis Streams (7.x), completes Alembic to `20260724_0029`, adds fail-fast startup validation, Celery Beat heartbeat, System Operations dashboard/API, production gate, and 150+ operational tests.

## Compliance

| Rule | Status |
|---|---|
| No redesign of completed engines | ✅ |
| No new intelligence modules | ✅ |
| No GPT additions | ✅ |
| No breaking schema changes | ✅ (forward migrations only) |
| Compose-only | ✅ (`packages/runtime_ops`) |
| Deterministic / evidence-driven | ✅ |
| Automated tests for every fix | ✅ `tests/runtime_ops/` |

## Phase Status

| Phase | Status | Evidence |
|---|---|---|
| 1 Infrastructure Recovery | ✅ | Redis 7.4.9 Streams validated; startup gate; worker/beat scripts |
| 2 Migration Recovery | ✅ | Alembic upgraded `0016 → 0029`; required tables present |
| 3 Pipeline Recovery | ✅ | Stage auditor in `/api/v1/operations` |
| 4 Collector Recovery | ✅ | Source health + ops alerts; start scripts restore Beat |
| 5 Enrichment Recovery | ✅ | Coverage metrics + low_coverage alert |
| 6 Operations Dashboard | ✅ | `/operations` + `/api/v1/operations` |
| 7 Production Gate | ✅ | Blocks production when Redis/migrations/worker/beat fail |
| 8 E2E Validation | 🟡 | Live probes + gate; full pipeline requires worker continuous run |
| 9 Recovery Tests | ✅ | 150+ tests in `tests/runtime_ops` |
| 10 Operational Reports | ✅ | Generated via `/operations/reports` + docs below |

## Runtime Changes

- `packages/runtime_ops/` — Redis validator, migration validator, pipeline auditor, Celery probe, production gate, reports
- `apps/api/app/services/runtime_ops.py` + `/api/v1/operations*`
- `apps/api/app/main.py` — fail-fast Redis Streams check (hard fail in production)
- `worker.runtime_ops_tasks` + Beat heartbeat every 60s
- `scripts/start-redis.bat`, `start-worker.bat`, `start-beacon.bat` (API script updated)
- Dashboard `/operations` (System Operations)

## Redis

| Item | Value |
|---|---|
| Required | Redis **7.x** with Streams |
| Local runtime | `C:\temp\redis74` (Redis 7.4.9 msys2 build + DLLs) |
| Validated | XADD, XREADGROUP, consumer groups, Pub/Sub |
| Fail-fast | `RedisStreamsValidator` on API startup |

## Migrations

| Item | Value |
|---|---|
| Before | `20260720_0016` |
| After | `20260724_0029` (head) |
| Tables restored | `revenue_hunter_dossiers`, `sales_intelligence_snapshots`, `founder_daily_briefs`, `roip_email_metrics`, `account_journeys`, `aip_account_profiles`, … |

## How to run continuously

```bat
scripts\start-redis.bat
scripts\start-api.bat
scripts\start-worker.bat
```

**Windows note:** Celery does not support `worker --beat` on Windows. `start-worker.bat` starts **Beat** and **Worker** as separate processes (`--pool=solo`).

Dashboard: `npm run dashboard:dev` → **System Operations** (`/operations`)

## Follow-ups

1. Keep worker+beat running as always-on terminals (or Windows services)
2. Revisit Indie Hackers connector bot-protection / alternate feed
3. Raise enrichment coverage from ~3% toward 100% of qualified opportunities once collectors are continuous
4. Optional: Docker Compose path remains Redis 7-alpine (already correct)
5. Production readiness score ≥95% requires worker+beat continuously online (gate currently enforces this)