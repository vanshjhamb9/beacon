# Sprint 16 Engineering Report — Target Account Intelligence Engine

## Verdict

Beacon now ranks discovered companies against Ideal Customer Profiles before auto-advancing into Sales Copilot and Campaigns. Scoring is deterministic, explainable, versioned (`tai-v1`), and evidence-backed. Top-tier accounts (`revenue_opportunity_score ≥ 70`) proceed automatically; Hunter Mode deepens enrichment above 75.

## Files created

### Package `packages/target_account_engine/`
- models, matching, industry/defaults (4 ICPs)
- fit, intent, budget, urgency, buyer/accessibility, competition
- scoring (weights + combiner), recommendations (why-now + improvements)
- hunter mode, analytics, pipelines, services, repository protocol

### API / persistence
- Migration `20260720_0016_create_target_account_tables.py`
- ORM `apps/api/app/models/target_account.py`
- Repository / service / schemas / routes (`/targets`, `/icp`, `/hunter`)

### Worker
- `apps/worker/worker/target_account_tasks.py` (`targets.process_accounts`, beat 128s)

### Dashboard
- Sidebar **Target Accounts**
- Views: ICP Manager, Hunter Mode, Revenue Ranking, Why Now, Buying Signals, Heat Map, Industries, Countries, Pipeline

### Integration (non-breaking gates)
- Sales Copilot `process_pending` skips non-top-tier when gate enabled
- Campaign worker skips non-top-tier when gate enabled
- Config: `TARGET_ACCOUNT_GATE_ENABLED`, thresholds

## Database migrations

Additive tables:
- `icp_profiles`
- `target_accounts`
- `hunter_jobs`
- `tai_improvement_recommendations`

## APIs

| Method | Path |
|---|---|
| GET | `/api/v1/targets` |
| GET | `/api/v1/targets/{id}` |
| GET | `/api/v1/targets/dashboard` |
| GET/POST | `/api/v1/icp` |
| PUT/DELETE | `/api/v1/icp/{id}` |
| POST | `/api/v1/hunter/start` |
| GET | `/api/v1/hunter/status` |

## Workers

- `targets.process_accounts` @ 128s (before copilot @ 135s, campaigns @ 150s)

## Tests / coverage / performance

- **13 passed** (unit, pipeline, components, API registration, migration, performance, regression E2E)
- Package coverage **~92%**
- Performance: 100 pipeline evaluations &lt; 2.5s

## Architecture notes

- TAI is the **selection/ranking** layer; it does not replace Opportunity or Revenue engines
- Collectors still discover signals; TAI decides which companies deserve pipeline spend
- Weights live in `scoring/weights.py` and are versioned — never silent retrain
- Outcome feedback yields **recommendations only**

## Future improvements

1. Feed collector queries with active ICP keywords (true “search only for ICP matches”)
2. Persist Redis-backed hunter job orchestration across enrichment workers
3. Country/industry heat maps from live geo IP + firmographics providers
4. Operator UI for approving improvement recommendations into weight v2
5. A/B evaluate top-tier threshold against win-rate from Outcome Intelligence
