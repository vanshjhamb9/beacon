# Sprint 36 — Beacon Intelligence Center (BIC v1)

## Mission

Transform Beacon from an operational dashboard into a **living intelligence platform**.

Zero new intelligence engines. No GPT. No AI. Everything deterministic and append-only.

## What shipped

### Package

`packages/intelligence_center/`

- `journey_engine.py`
- `roi_engine.py`
- `dataset_engine.py`
- `replay_engine.py`
- `discovery_engine.py`
- `analytics_engine.py`

### Database

Migration: **`20260726_0049`**

Tables (append-only):

| Table | Purpose |
| --- | --- |
| `discovery_events` | Live discovery feed |
| `company_journey_events` | Per-company stage timeline |
| `connector_roi_daily` | Daily connector ROI |
| `dataset_statistics_daily` | Daily dataset stats |
| `pipeline_replay_frames` | Hourly replay frames (rolling 24h reconstruction) |

### APIs

| Endpoint | Role |
| --- | --- |
| `GET /api/v1/discoveries/live` | Discovery feed + filters |
| `GET /api/v1/discoveries/company/{id}` | Company discovery stream |
| `GET /api/v1/connectors/roi` | Connector ROI + enrichment coverage |
| `GET /api/v1/dataset/statistics` | Dataset explorer + heatmap |
| `GET /api/v1/company/{id}/journey` | Full journey + pipeline health |
| `GET /api/v1/pipeline/replay` | Rolling 24h funnel replay from discovery events |
| `GET /api/v1/analytics/v2` | Analytics V2 (no placeholders) |
| `GET /api/v1/intelligence/search` | Operations search |
| `POST /api/v1/intelligence/sync` | Idempotent sync from live tables |

### Background

Celery beat: `intelligence_center.sync` every **60s**.

### UI

| Page | Path |
| --- | --- |
| Discoveries ⭐ | `/discoveries` (5s refresh) |
| Connectors ROI | `/connectors` |
| Dataset Explorer | `/dataset` (heatmap + replay) |
| Analytics V2 | `/analytics` |
| Company Journey | Company page Journey + Pipeline Health |

Sidebar updated:

Dashboard · Operations · Today · **Discoveries** · Outreach · Pipeline · Analytics · **Dataset** · **Connectors** · Conversations · Meetings · Integrations · Settings

## Acceptance

- Every company has a deterministic journey Signal → Won/Lost (13 stages; Lost is a real terminal)
- Discovery Feed auto-refreshes every 5s; cards open company; Duplicate Removed events emitted from collector runs
- Every connector exposes measurable ROI (meetings/wins attributed via company→signal source; quota is a real %)
- Dataset Explorer reports rates + daily trends + heatmap + clickable stats
- Pipeline Replay reconstructs the last 24h of funnel movement from append-only discovery events (hourly slider)
- Company pages include Journey with timestamps, duration, evidence, connector, worker, retries, and failures
- Analytics V2 populated from operational data only (including Enrichment + Services)
- No GPT / no new scoring models / no duplicate engines

## Audit fixes (post-ship)

- Emit `Duplicate Removed` discovery events from `CollectorRun.duplicates`
- Website Verified events now join `company_id` via `Company.primary_domain`
- Connector ROI: real meetings/wins attribution; quota_used_pct from payload daily_quota; win% never invents 100%
- Journey stages include **Lost**; OFC `status_history` used for stage timestamps; retries/failures from ingestion events
- Heatmap success % capped at 100
- Dataset UI: trend bars + table; 7/30 day ranges fetch correct window; stats clickable
- Discoveries: whole card clickable to company
- Analytics V2: Enrichment + Services sections rendered; empty shells hidden
- OpenAPI: fixed execution_readiness local `ServiceDep` ForwardRef crash

## Next

Pause feature work. Integrate external enrichment providers into this observable pipeline so Beacon proves which integrations generate the highest revenue.
