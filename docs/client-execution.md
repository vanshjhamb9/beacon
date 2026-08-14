# Agency Execution Platform (AEP) — Client Execution

**Scoring version:** `aep-v1`  
**Migration:** `20260724_0026`

## Purpose

When a company becomes a client, Beacon transitions from **Sales Mode** to **Client Delivery Mode**. AEP composes existing sales/revenue signals into lifecycle, workspace, handoff, knowledge, health, upsell, and founder views — without redesigning prior packages.

## Modules

1. **Client Lifecycle** — Won → Contract Pending → … → Referral / Lost / Archive  
2. **Client Workspace** — executive summary, services, value, contacts, risks, invoices placeholder  
3. **Project Handoff** — dossier + sales/founder context for delivery  
4. **Knowledge Base** — append-only, searchable memory  
5. **Upsell Engine** — deterministic suggestions; **founder approval required**; never auto-applies  
6. **Client Health** — communication, delivery, risk, renewal/upsell probability  
7. **Delivery Dashboard** — today, milestones, blocked, at-risk, renewals, upsells  
8. **Founder Executive View** — closed/delivered revenue, risks, capacity placeholder  

## API

- `GET /api/v1/client-execution/dashboard`
- `GET /api/v1/client-execution/client/{id}`
- `GET /api/v1/client-execution/health`
- `GET /api/v1/client-execution/handoff`
- `GET /api/v1/client-execution/upsells`
- `POST /api/v1/client-execution/upsells/{id}/approve`
- `GET /api/v1/client-execution/projects`
- `POST /api/v1/client-execution/refresh`

## Workers

| Task | Interval |
|---|---|
| `client_execution.refresh_health` | 180s |
| `client_execution.detect_upsells` | 12h |
| `client_execution.refresh_dashboard` | 300s |

## Tables

`client_profiles`, `client_projects`, `client_health_snapshots`, `client_memory`, `client_handoffs`, `upsell_recommendations`, `renewal_predictions`, `delivery_snapshots`

## Constraints

Compose only · Append-only · Deterministic · No GPT · Founder approval for upsells

## Dashboard

`/client-execution` — Client Delivery workspace
