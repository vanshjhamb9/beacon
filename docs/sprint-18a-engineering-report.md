# Sprint 18A Engineering Report — Communication Gateway Foundation

**Date:** 2026-07-23  
**Objective:** Founder-approved personalized email via Gmail OAuth, reply sync into Inbox/Conversation Center, audit trails, sandbox default, safety controls, E2E approve→send→reply.

## Verdict

Sprint 18A **extends** the Sprint 15A sandbox foundation — no engine redesigns. Beacon can now take a founder-approved campaign, send one personalized email (sandbox by default; Gmail when double-gated), sync replies into Inbox, stop campaigns on reply, and enforce quota/dedupe/stop rules with full delivery audit events.

## Architecture

```text
Campaign Intelligence (approve)
        │
        ▼
POST /communication/send | /campaigns/{id}/execute
        │
 SafetyControls (approval · stop · quota · idempotency)
        │
 ProviderFactory ──sandbox──► SandboxEmailProvider
              └──production──► GmailProvider (+ OAuth tokens from DB)
        │
 Persist: communication_messages · delivery_events · conversation_* · campaign_stop_events
        │
 Reply: Gmail webhook hint → sync_gmail_replies → Inbox + stop rules
```

Integrations (compose only):
- **Campaign Intelligence** — requires `approved`/`scheduled` before execute
- **Sales Copilot** — body/subject from campaign step previews (existing)
- **Revenue Hunter / Founder OS** — Campaign Execution UI + invalidate founder-os queries after send

## Files created / extended

### Package
- `packages/communication_gateway/safety/controls.py` *(new)*
- `packages/communication_gateway/foundation/idempotency.py` *(new)*
- `packages/communication_gateway/email/gmail.py` — history/list/get + `fetch_inbound_replies`
- `packages/communication_gateway/services/gateway.py` — preflight, `send_founder_approved`, `with_access_tokens`, `load_stopped_campaigns`
- `packages/communication_gateway/models/types.py` — `idempotency_key`, approval flags

### API
- `apps/api/app/services/communication.py` — founder send, OAuth load/refresh, durable queue, Gmail sync, webhook dedupe+handle
- `apps/api/app/api/routes/communication.py` — new endpoints
- `apps/api/app/schemas/communication.py` — request models
- `apps/api/app/models/communication.py` — queue `idempotency_key`
- `apps/api/alembic/versions/20260723_0019_communication_gateway_foundation.py`

### Worker / Dashboard
- `apps/worker/worker/communication_tasks.py` — sync + OAuth refresh tasks
- `apps/worker/worker/celery_app.py` — beat entries @60s / @600s
- `apps/dashboard/features/campaign-execution/...` — Approve & send
- `apps/dashboard/lib/api/beacon.ts` — client methods

### Tests / Docs
- `tests/communication_gateway/test_sprint18a_*.py`
- Updated API / migration / performance tests
- `docs/sprint-18a-communication-gateway.md`
- `docs/sprint-18a-engineering-report.md`

## Migration

- **Revision:** `20260723_0019`
- **Revises:** `20260723_0018`
- Indexes on `provider_message_id`, campaign/step; `idempotency_key` on queue items

```bash
cd apps/api
python -m alembic -c alembic.ini upgrade head
```

## APIs

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/communication/send` | Founder-approved personalized send |
| POST | `/api/v1/communication/campaigns/{id}/execute` | Approve-gated campaign execute |
| GET | `/api/v1/communication/oauth/status` | Gmail connection status |
| POST | `/api/v1/communication/oauth/refresh` | Refresh near-expiry tokens |
| POST | `/api/v1/communication/sync/gmail-replies` | History → Inbox sync |
| POST | `/api/v1/communication/e2e/approve-send-reply` | Sandbox E2E helper |

Existing sandbox/OAuth/webhook/inbox routes retained.

## Workers

| Task | Schedule |
|---|---|
| `communication.process_queue` | 20s (now drains durable queue) |
| `communication.sync_gmail_replies` | 60s |
| `communication.refresh_oauth` | 600s |
| `communication.snapshot_health` | 180s |

## Dashboard

Campaign Execution: **Approve & send** (auto-approves if needed) + recipient field + sandbox-only fallback. Invalidates inbox + founder-os queries.

## Tests

| Suite | Coverage |
|---|---|
| `test_sprint18a_safety_send` | Quota, dedupe, stop, approval gate |
| `test_sprint18a_gmail_sync` | Mocked Gmail history→InboundEvent |
| `test_sprint18a_e2e_approve_send_reply` | Approve→send→reply→stop |
| `test_gateway_api` | New route registration |
| `test_gateway_migration` | 0019 contract |
| `test_gateway_performance` | Send/queue/safety budgets |

## Coverage (capability)

| Capability | Status |
|---|---|
| Founder-approved personalized email | Done (sandbox default; Gmail when gated) |
| Gmail OAuth token injection | Done |
| Reply sync → Inbox / Conversation Center | Done (sync path + webhook trigger) |
| Audit trails (messages, delivery, stops, webhooks) | Done |
| Sandbox mode | Preserved |
| Rate limits / dedupe / stop rules | Done |
| Durable queue drain | Done |
| Provider-agnostic factory | Preserved |
| E2E approve→send→reply | Done (domain + API helper) |

## Performance

- 100 sandbox sends < 2.0s  
- 50 queue process < 2.0s  
- 5k safety checks < 1.5s  

## Remaining work

1. Live Gmail Pub/Sub push credentials in production env (sync works once OAuth+history id set).
2. Redis-backed daily quota shared across workers (today DB count + in-process safety).
3. Unique DB constraint on `metadata.idempotency_key` (currently app-level + index on queue).
4. Wire Founder OS task “Approve Campaign” one-click to `/communication/campaigns/{id}/execute`.
5. DB fixture integration test for full HTTP approve→send→inbox with TestClient + Postgres.

## Success check

Founder can approve a campaign, send one personalized email, see it in Inbox, receive a reply (sandbox simulated or Gmail sync), and have the campaign auto-stopped with a complete audit trail — without redesigning Campaign Intelligence, Sales Copilot, Revenue Hunter, or Founder OS engines.
