# Sprint 18A — Communication Gateway Foundation

Extends Sprint 15A sandbox foundation with founder-approved Gmail send, reply sync, durable queue processing, and safety controls.

## Path

```text
Campaign approve → POST /communication/send or /campaigns/{id}/execute
  → Safety (approval, stop, quota, dedupe)
  → Sandbox provider (default) OR Gmail OAuth (double-gated production)
  → Persist CommunicationMessage + DeliveryEvent
  → Conversation thread / Inbox
  → Reply sync (webhook history → Gmail fetch → stop campaign)
```

## Safety double-gate

Production Gmail only when:
1. `COMMUNICATION_MODE=production`
2. `ALLOW_PRODUCTION_SEND=true`
3. Active Gmail OAuth connection
4. Campaign status `approved` or `scheduled`

## New APIs

| Method | Path |
|---|---|
| POST | `/communication/send` |
| POST | `/communication/campaigns/{id}/execute` |
| GET | `/communication/oauth/status` |
| POST | `/communication/oauth/refresh` |
| POST | `/communication/sync/gmail-replies` |
| POST | `/communication/e2e/approve-send-reply` |

## Workers

- `communication.process_queue` (20s) — durable + in-memory
- `communication.sync_gmail_replies` (60s)
- `communication.refresh_oauth` (600s)
