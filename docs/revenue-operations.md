# Revenue Operations Center (ROC v1)

Beacon's compose-only Revenue Operating System layer.

**Scoring version:** `roc-v1`  
**Package:** `packages/revenue_operations/`  
**API:** `/api/v1/revenue-operations/*`

## Mission

When the founder opens Beacon each morning, one workspace answers:

- What should I do?
- Who should I contact?
- Who replied?
- Which companies are hot?
- Which opportunities are at risk?
- What revenue can I close this week?

## Modules

1. Revenue Control Tower  
2. Revenue Radar  
3. Smart Alert Engine  
4. Multi-Agent Orchestrator  
5. Agency Memory  
6. Win / Loss Analytics  
7. Revenue Forecast Engine  
8. Founder Assistant V2  
9. Revenue Replay  
10. Learning Lab  
11. Command Center (Home)  
12. Operational Metrics  

## Hard rules

- Compose only — no redesign of completed engines  
- Deterministic — no GPT dependency  
- Append-only persistence  
- Learning recommendations never modify production without founder approval  
- Evidence-backed outputs  

## API

- `GET /dashboard`
- `POST /refresh`
- `GET /forecast`
- `GET /alerts`
- `POST /alerts/{id}/transition`
- `GET /memory?q=`
- `GET /replay/{id}`
- `GET /learning`
- `POST /learning/{recommendation_id}/approve`
- `GET /metrics`

## Workers

| Task | Cadence |
|---|---|
| `revenue_operations.refresh_dashboard` | 120s |
| `revenue_operations.refresh_forecast` | 300s |
| `revenue_operations.refresh_alerts` | 60s |
| `revenue_operations.daily_learning` | 24h |

## Migration

`20260724_0024`

| Logical table | Physical table |
|---|---|
| revenue_operation_snapshots | revenue_operation_snapshots |
| revenue_alerts | revenue_alerts |
| revenue_forecasts | revenue_forecasts |
| revenue_memory | revenue_memory |
| revenue_replays | revenue_replays |
| revenue_metrics | revenue_operation_metrics *(avoids collision with Revenue Engine)* |
| learning_recommendations | revenue_operation_learning |
| agency_statistics | agency_statistics |

## Dashboard

Home (`/`) is replaced by the ROC Command Center above-the-fold view.
