# Sprint 15A Engineering Report — Communication Gateway + Production QA

## Verdict

Beacon can execute a complete campaign in **Sandbox Mode** from sales package → campaign approval → sandbox send → simulated reply → meeting booking → conversation summary, with **no production providers required**. Production send remains double-gated (`COMMUNICATION_MODE=sandbox`, `ALLOW_PRODUCTION_SEND=false` by default).

## Packages created

| Package | Role |
|---|---|
| `packages/communication_gateway/` | Provider abstraction, OAuth, webhooks, queues, sandbox, security, tracking |
| `packages/conversation_center/` | Timeline, search, unread, pin, notes, AI summaries |
| `packages/testing_platform/` | System health, probes, Prometheus helper, sandbox E2E |

## APIs added

- `GET /api/v1/communication/mode`
- `GET /api/v1/communication/queues`
- `POST /api/v1/communication/queues/process`
- `POST /api/v1/communication/sandbox/send`
- `POST /api/v1/communication/sandbox/meeting`
- `POST /api/v1/communication/campaigns/{id}/stop`
- `POST /api/v1/communication/oauth/authorize`
- `GET /api/v1/communication/oauth/callback`
- `GET|POST /api/v1/communication/webhooks/meta`
- `POST /api/v1/communication/webhooks/calendly`
- `POST /api/v1/communication/webhooks/gmail`
- `GET /api/v1/communication/metrics`
- `GET /api/v1/inbox`
- `GET /api/v1/inbox/{conversation_id}`
- `GET /api/v1/qa/health`
- `GET /api/v1/qa/dashboard`
- `POST /api/v1/qa/e2e/sandbox`
- `GET /api/v1/system-health`

## Database migration

- `apps/api/alembic/versions/20260720_0015_create_communication_qa_tables.py`
- Additive tables: `oauth_connections`, `provider_secrets`, `communication_messages`, `delivery_events`, `webhook_events`, `communication_queue_items`, `conversation_threads`, `conversation_items`, `sandbox_scenarios`, `qa_health_snapshots`, `campaign_stop_events`

## Dashboard pages

- Inbox
- Campaign Execution
- Communication
- QA
- System Health
- Test Center

## Workers

- `communication.process_queue` (beat 20s)
- `communication.snapshot_health` (beat 180s)

## Tests & coverage

- Suites: unit, integration (API registration), webhook/OAuth/security, queue/chaos/recovery, performance, sandbox E2E
- Result: **25 passed**
- Package coverage (communication_gateway + conversation_center + testing_platform): **~84%**

## Documentation

- `docs/communication-gateway.md`
- `docs/testing-platform.md`
- `docs/oauth.md`
- `docs/webhooks.md`
- `docs/security.md`
- `docs/sandbox.md`

## Remaining production tasks

1. Complete OAuth reconnect UX and token refresh worker against live Google/Microsoft tenants
2. Persist queue items to Redis/Postgres for multi-worker durability (domain queue is in-memory; worker processes via gateway)
3. Wire Gmail Pub/Sub history fetch to pull full thread bodies after push notifications
4. Enable Meta WhatsApp template catalog sync and media upload paths in ops config
5. Flip production only after sandbox E2E + provider smoke tests: `COMMUNICATION_MODE=production` **and** `ALLOW_PRODUCTION_SEND=true`
6. Rotate `COMMUNICATION_ENCRYPTION_KEY` via secret manager (not `.env` in production)
7. Add load tests against staging Redis-backed queues at expected campaign volume

## Architectural recommendations

- Keep Campaign Intelligence delivery-disabled; gateway owns send + stop rules
- Treat sandbox as the CI gate for every outreach change
- Prefer provider factory injection for tests; never call Gmail/Graph/Meta SDKs from routes directly
- Store only encrypted tokens; never log token material
