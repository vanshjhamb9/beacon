# Sprint 35 — Beacon Operations Center (BOC v1)

## Mission

Beacon is now a **real-time operational intelligence platform**. The CTO homepage is `/operations`.

No AI. No GPT. No new intelligence engines. Only operational visibility.

## What shipped

### Package

`packages/operations_center/`

- `collector_monitor.py`
- `pipeline_monitor.py`
- `worker_monitor.py`
- `queue_monitor.py`
- `connector_monitor.py`
- `metrics_engine.py`
- `daily_snapshot.py`
- `health_engine.py`
- `dashboard_service.py`
- `router.py`

### Database

Migration: **`20260726_0048`**

> Sprint brief asked for `20260725_0043`, but that id was already used by ODU (`20260724_0043`). Following prior sprint convention, this append-only revision is `20260726_0048` after execution readiness `0047`.

Tables:

| Table | Purpose |
| --- | --- |
| `pipeline_stage_metrics` | Live stage counters (append-only) |
| `connector_health` | Per-connector health upsert |
| `worker_health` | Per-worker health upsert |
| `operation_snapshots` | Hourly snapshots |
| `ingestion_events` | Append-only collector/enrichment events |

### APIs

| Endpoint | Role |
| --- | --- |
| `GET /api/v1/operations/live` | Full BOC dashboard |
| `GET /api/v1/operations/connectors` | Connector health |
| `GET /api/v1/operations/workers` | Worker status |
| `GET /api/v1/operations/pipeline` | Funnel + conversions + source map |
| `GET /api/v1/operations/feed` | Real-time feed |
| `GET /api/v1/operations/queues` | Queue depths |
| `GET /api/v1/operations/health` | Health summary |
| `GET /api/v1/operations/daily` | Timeline + progress + revenue |

### Route collision resolution

Existing ODU endpoints under `/operations/{connectors,health,dashboard,...}` collided with BOC.

ODU moved to:

- `/api/v1/operations/odu/connectors`
- `/api/v1/operations/odu/health`
- `/api/v1/operations/odu/dashboard`
- `/api/v1/operations/odu/recovery`
- `/api/v1/operations/odu/report`
- `/api/v1/operations/odu/unlock`

Runtime infra dashboard kept at `/operations/runtime`.

### Background workers

Celery beat:

- `operations_center.refresh_metrics` every **60s**
- `operations_center.hourly_snapshot` every **3600s**

Every collector run now emits an `ingestion_events` row (success + failure).

### UI

`/operations` is now the CTO Operations Center:

1. Live Pipeline funnel
2. Connector Health
3. Pipeline Conversion
4. Daily Timeline
5. Worker Status
6. Queues
7. Top Failures
8. Real-time Feed
9. Today's Progress
10. Revenue Engine
11. Live Source Map

Dark mode. Auto-refresh every **5 seconds**. Top-row KPI cards included.

Sidebar: **Operations** is the second nav item (after Dashboard).

## Future integrations (no redesign required)

`KNOWN_CONNECTORS` already reserves rows for:

Hunter.io · LinkedIn · Apollo · People Data Labs · Crunchbase · Clearbit · BuiltWith · Wappalyzer · Google Maps · YC · App Store · Google Play

They appear automatically in Connector Health as disabled / not configured until keys are wired.

## Acceptance checklist

| Question | Answered from `/operations` |
| --- | --- |
| Is Beacon collecting data? | Health banner + Signals Today |
| Which connector is failing? | Connector Health |
| Which worker is stuck? | Worker Status |
| How many signals today? | Top cards + Live Pipeline |
| How many became companies? | Live Pipeline |
| How many emails recovered? | Emails card |
| How many decision makers? | Decision Makers card |
| Revenue Ready gained today? | Today's Progress |
| Biggest bottleneck? | Health banner + Conversion |
| Queue sizes? | Queues |
| Pipeline / connector / revenue health? | Sections 1–3, 10 |

## Next recommendation

Stop building internal engines for a while. Integrate external enrichment providers into this observable pipeline. BOC will immediately show which integrations move Revenue Ready — not just raw lead counts.
