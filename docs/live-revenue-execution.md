# Live Revenue Execution (LRE v1) — Sprint 20

Scoring version: `lre-v1`

## Purpose

Convert Beacon from intelligence → **production revenue generation** for Inowix.

Founder loop:

```
Open Beacon → Approve outreach → Reply → Meeting → Proposal → Close
```

Beacon performs everything else by composing existing engines.

## Package

`packages/live_revenue_execution/`

Modules:

- Production Email Engine (HTML, tracking, unsubscribe, Calendly, attachments plan)
- WhatsApp Execution Engine (Meta templates/media/buttons — founder approval required)
- Approval Center Engine
- Campaign Lifecycle Engine (append-only LRE stages)
- Meeting Automation Engine
- Proposal Center Engine (versioned PDF payload)
- Revenue Analytics Engine
- Outcome Learning Composer (human approval required)

Reuses: Sales Intelligence reply classifier, Communication Gateway, Campaign Intelligence, Founder OS, Revenue Hunter, Outcome Intelligence.

## API

- `GET /api/v1/live-revenue/company/{id}`
- `POST /api/v1/live-revenue/refresh/{id}`
- `GET /api/v1/live-revenue/approval-center`
- `GET /api/v1/live-revenue/proposals`
- `GET /api/v1/live-revenue/dashboard`
- `GET /api/v1/live-revenue/command-center`
- `POST /api/v1/live-revenue/track`

Campaign extensions:

- `POST /api/v1/campaigns/reject/{id}`
- `POST /api/v1/campaigns/bulk-approve`
- `POST /api/v1/campaigns/bulk-reject`

## Communication Gateway extensions (no redesign)

- Gmail MIME attachments + List-Unsubscribe + tracking headers
- Hourly + daily quota in SafetyControls
- Email health / DKIM-SPF status helper
- Meta WhatsApp media + interactive buttons via metadata

## Workers

- `live_revenue.refresh_command_center` @ 90s
- Continues to compose after Communication Gateway + Sales Intelligence refresh

## Dashboard

- `/approval-center` — Founder Approval Center (bulk approve/reject)
- `/proposals` — Proposal Center
- Home quick links: Approvals · Replies · Proposals · Launch

## Migration

`20260723_0021` — append-only:

- `live_revenue_runs`
- `live_revenue_lifecycle_events`
- `live_revenue_tracking_events`
- `live_revenue_proposal_versions`

## Constraints

- No engine redesigns
- Deterministic
- No GPT dependency
- Every send remains founder-gated
- Learning hints never auto-apply production rules
