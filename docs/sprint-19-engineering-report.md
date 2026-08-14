# Sprint 19 Engineering Report — Sales Intelligence Engine

**Date:** 2026-07-23  
**Objective:** Understand buyers and maximize deal conversion via a compose-only Sales Intelligence Engine.

## Verdict

Sprint 19 delivers `packages/sales_intelligence/` with 10 deterministic engines, append-only persistence, API, post-Communication-Gateway workers, and a company-page Sales Intelligence panel. No existing packages were redesigned.

## Architecture

```text
Company signals
  ├─ Revenue Hunter dossier
  ├─ Decision makers
  ├─ Opportunity score
  ├─ Communication Gateway emails/replies
  └─ Outcomes (meetings / proposals)
        │
        ▼
 SalesIntelligencePipeline (si-v1)
  Intent → Psychology → Objections → Offer → Trust
  → Proposal → Meeting → Reply → Memory → Score
        │
        ▼
 Append-only snapshots + memory events + reply rows
        │
        ▼
 GET /sales-intelligence/company|{opportunity}
 POST /sales-intelligence/refresh
 GET /sales-intelligence/dashboard
```

## Deliverables

### Package (`packages/sales_intelligence/`)
- Intent, Psychology, Objections, Offers, Trust, Proposal, Meeting, Reply, Memory, Score engines
- Pipeline + `SalesIntelligenceService`
- Models: `SalesIntelligenceInput` / `SalesIntelligenceDecision` (`si-v1`)

### API
- Routes under `/api/v1/sales-intelligence/*`
- Repository builds inputs from existing Beacon tables
- Snapshots stored append-only

### Migration
- `20260723_0020_create_sales_intelligence_tables.py` (revises `0019`)
- Tables: `sales_intelligence_snapshots`, `sales_memory_events`, `sales_reply_intelligence`

### Workers
- `sales_intelligence.refresh_from_replies` beat @ 70s
- Gmail sync enqueues SI refresh after Communication Gateway

### Dashboard
- `SalesIntelligencePanel` on company workspace
- Tabs: Buying Intent, Psychology, Objections, Offer, Proposal, Meeting, Relationship, Reply Intelligence, Score
- Client methods in `beacon.ts`

### Tests
- `tests/sales_intelligence/` — components, pipeline, API, performance, migration, dashboard, regression, integration, coverage boost
- Target: 40+ tests; 100 evaluations &lt; 3s

## Performance

- Constraint: 100 company evaluations under 3 seconds
- Covered by `test_100_company_evaluations_under_3_seconds`

## Constraints honored

| Constraint | Status |
|---|---|
| Append-only DB | Snapshots + memory + reply rows; no company unique overwrite |
| Deterministic reasoning | Pure rule engines; same input → same scores |
| No redesign | Compose-only from existing packages |
| No GPT dependency | Package scanned in regression test |
| Optional Sales Copilot | Panel sits beside existing Sales Copilot card |

## Remaining work

1. Run Alembic upgrade `20260723_0020` in deployed environments
2. Backfill SI for existing high-intent Revenue Hunter A+/A accounts
3. Optional: surface Sales Intelligence dashboard page (API exists; company panel shipped)
4. Optional: wire Sales Copilot package fields from SI offer/proposal (compose, no redesign)
5. Measure live coverage vs 95% target after CI run with `--cov=packages/sales_intelligence`

## Example pack shape

| Field | Example |
|---|---|
| Intent Score | 96 |
| Urgency | High |
| Budget | Medium |
| Decision Window | 30 Days |
| Primary Offer | AI Automation |
| Close Probability | scored via Sales Score engine |
