# Account Journey / Global Outreach Intelligence (GOI v1)

Compose-only autonomous BD layer for persistent account lifecycles.

**Scoring version:** `goi-v1`  
**Package:** `packages/account_journey/`  
**API:** `/api/v1/account-journey/*`

## Modules

1. Account Journey Engine  
2. Outreach Intelligence  
3. Multi-Touch Orchestration (adaptive timing)  
4. Engagement Scoring  
5. Account Health  
6. Buying Committee  
7. Automatic Follow-up Planner (founder approval mandatory)  
8. Global Campaign Analytics  
9. Reply Intelligence V2  
10. Account Timeline  

## Hard rules

- Compose only — no redesign of completed engines  
- Deterministic — no GPT  
- Append-only journey history  
- Founder approval required before external sends  

## API

- `GET /company/{id}`
- `GET /dashboard`
- `GET /followups`
- `GET /analytics`
- `GET /replies`
- `GET /health`
- `POST /refresh`

## Workers

| Task | Cadence |
|---|---|
| `journey.refresh_accounts` | 180s |
| `journey.calculate_engagement` | 90s |
| `journey.plan_followups` | 120s |
| `journey.analytics_daily` | 24h |

## Dashboard

`/account-journey` — Account Journey · Company Health · Buying Committee · Engagement · Reply Intelligence · Timeline · Follow-up Planner · Global Analytics

## Migration

`20260724_0025`
