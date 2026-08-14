# Sprint 17 Engineering Report — Founder Revenue OS

**Mission:** Founder Revenue OS  
**Date:** 2026-07-23  
**Package:** `packages/founder_os/`  
**Version:** `fos-v1`

## Verdict

Beacon Home is now a daily VP-of-Sales operating system. Founders open Beacon and see only actionable work: who to contact, why, what to sell, approvals, replies, meetings, proposals, and evidence-backed recommendations. No GPT dependency. No redesign of completed engines.

## Architecture

```text
Existing engines (unchanged)
  revenue_hunter · outcomes · campaigns · communication · sales_copilot(optional)
        │
        ▼
 founder_os pipeline (compose only)
  Brief → Assistant → Tasks → Timeline → KPIs → Recommendations
  → Proposals → Meeting Packs → Command Center → Analytics
        │
        ▼
 API /founder-os/*  →  Home dashboard  →  Celery refresh @300s
```

Constraints honored:
- Append-only timeline + analytics tables
- Deterministic reasoning only
- Reuses existing APIs/tables as source of truth
- Sales Copilot remains optional/external (GroundedProvider when used)

## Files Created

### Package
- `packages/founder_os/models/types.py`
- `packages/founder_os/brief/engine.py`
- `packages/founder_os/assistant/engine.py`
- `packages/founder_os/tasks/engine.py`
- `packages/founder_os/timeline/engine.py`
- `packages/founder_os/kpi/engine.py`
- `packages/founder_os/recommendations/engine.py`
- `packages/founder_os/proposals/queue.py`
- `packages/founder_os/meetings/intelligence.py`
- `packages/founder_os/command/center.py`
- `packages/founder_os/analytics/tracker.py`
- `packages/founder_os/pipelines/founder_os_pipeline.py`
- `packages/founder_os/services/engine.py`

### API
- `apps/api/app/models/founder_os.py`
- `apps/api/app/repositories/founder_os.py`
- `apps/api/app/services/founder_os.py`
- `apps/api/app/schemas/founder_os.py`
- `apps/api/app/api/routes/founder_os.py`
- `apps/api/alembic/versions/20260723_0018_create_founder_os_tables.py`

### Worker / Dashboard / Docs / Tests
- `apps/worker/worker/founder_os_tasks.py` (+ beat entry)
- `apps/dashboard/features/home/home-workspace.tsx` (replaced clutter)
- `apps/dashboard/lib/api/beacon.ts` (founder OS client)
- `docs/founder-os.md`
- `docs/sprint-17-engineering-report.md`
- `tests/founder_os/test_*.py` (8 modules)

## Migration

- **Revision:** `20260723_0018`
- **Revises:** `20260723_0017`
- **Tables:** `founder_daily_briefs`, `founder_revenue_tasks`, `founder_timeline_events`, `founder_analytics_events`

```bash
cd apps/api
python -m alembic -c alembic.ini upgrade head
```

## APIs

| Method | Path |
|---|---|
| GET | `/api/v1/founder-os/command-center` |
| POST | `/api/v1/founder-os/refresh` |
| GET | `/api/v1/founder-os/brief` |
| GET | `/api/v1/founder-os/assistant` |
| GET | `/api/v1/founder-os/tasks` |
| POST | `/api/v1/founder-os/tasks/{id}/complete` |
| GET | `/api/v1/founder-os/kpis` |
| GET | `/api/v1/founder-os/recommendations` |
| GET | `/api/v1/founder-os/proposals` |
| GET | `/api/v1/founder-os/meetings` |
| GET | `/api/v1/founder-os/timeline/{company_id}` |
| POST | `/api/v1/founder-os/analytics/track` |

## Dashboard

Home (`/`) now shows only:
- Good Morning + executive summary
- Revenue Today / Pipeline / Meetings / A+
- Today's Mission (who / why / sell / budget / probability / next action)
- Tasks, Recommendations
- Campaign Queue · Inbox · Meetings
- Top Companies

## Workers

| Task | Schedule |
|---|---|
| `founder_os.refresh_brief` | 300s |

Runs after revenue hunter so dossiers/work queue feed the morning pack.

## Tests

```text
17 passed
```

| Suite | Purpose |
|---|---|
| components | Brief, assistant, tasks, KPIs, recommendations, timeline |
| pipeline | Full OS pack composition |
| api | Route registration |
| migration | 0018 contract |
| performance | 50 packs < 2.0s |
| regression | Evidence rules, proposals, meetings, determinism |
| dashboard | Home pack shape contract |
| integration | Evaluate + analytics track |

## Coverage (modules)

All 12 sprint modules shipped:
1. Daily Brief Engine  
2. Revenue Command Center  
3. AI Founder Assistant (deterministic)  
4. Revenue Task Engine  
5. Revenue Timeline (immutable)  
6. Sales KPI Engine  
7. Founder Recommendations (evidence-gated)  
8. Proposal Queue  
9. Meeting Intelligence  
10. Founder Dashboard UX  
11. Analytics (append-only)  
12. Testing  

## Performance

- 50 full OS packs under **2.0s**
- Refresh worker is read-compose-write; no LLM calls

## Remaining Work

1. Wire inbox `pending_replies` from conversation items (direction=inbound) into task engine with richer thread metadata.
2. Optional Sales Copilot grounded snippets on assistant `next_action` when enabled in settings.
3. Campaign approval one-click from Home → existing campaign approve API.
4. Persist subject-line / CTA win stats from campaign execution logs into brief top performers.
5. DB-backed API integration tests with fixtures.

## Metric mapping

| Module output | Metrics lifted |
|---|---|
| Assistant + work queue | Qualified Opportunities, Meetings Booked |
| Reply / approve tasks | Reply Rate |
| Proposal queue | Proposal Conversion |
| KPIs + recommendations | Revenue Closed / forecast |
