# Sales Intelligence Engine — Sprint 19

Scoring version: `si-v1`

## Purpose

Understand buyers and maximize deal conversion by composing existing Beacon signals into a deterministic Sales Intelligence pack.

## Modules

1. Buying Intent Engine
2. Psychology Engine
3. Objection Prediction Engine
4. Offer Recommendation Engine
5. Trust Builder
6. Proposal Intelligence
7. Meeting Coach
8. Reply Intelligence
9. Sales Memory (append-only)
10. Sales Score

## Compose-only integrations

- Revenue Hunter dossiers
- Decision Discovery makers
- Opportunity Engine scores
- Communication Gateway replies/emails
- Founder OS / Campaign Intelligence outcomes
- Optional Sales Copilot (no redesign)

## API

- `GET /api/v1/sales-intelligence/company/{id}`
- `GET /api/v1/sales-intelligence/opportunity/{id}`
- `POST /api/v1/sales-intelligence/refresh/{id}`
- `GET /api/v1/sales-intelligence/dashboard`

## Workers

- `sales_intelligence.refresh_from_replies` @ 70s (after Gmail sync @ 60s)
- Enqueued after Communication Gateway Gmail sync

## Persistence

Append-only tables:

- `sales_intelligence_snapshots`
- `sales_memory_events`
- `sales_reply_intelligence`

## Dashboard

Company workspace → **Sales Intelligence** panel with tabs:
Buying Intent · Psychology · Objections · Offer · Proposal · Meeting · Relationship · Reply Intelligence · Score

## Constraints

- Deterministic reasoning
- No GPT dependency
- No redesign of existing packages
- 100 company evaluations under 3 seconds
