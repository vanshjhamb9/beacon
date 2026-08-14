# Communication Gateway

Sandbox-first multi-provider outreach layer for Beacon Revenue OS.

## Package

`packages/communication_gateway/`

- Provider abstraction for email, WhatsApp, and calendar
- Outgoing / retry / delayed / priority / worker / dead-letter queues
- Delivery state machine and campaign stop rules
- OAuth flows for Google and Microsoft
- Official Meta WhatsApp Cloud API webhooks
- Fernet encryption for tokens and secrets

## Modes

| Setting | Default | Effect |
|---|---|---|
| `COMMUNICATION_MODE` | `sandbox` | Forces sandbox providers |
| `ALLOW_PRODUCTION_SEND` | `false` | Second gate; production providers only when both allow it |

Production messages never send unless **both** mode is `production` **and** `ALLOW_PRODUCTION_SEND=true`.

## Providers

- **Email:** Gmail API, Microsoft Graph (sandbox default)
- **WhatsApp:** Meta WhatsApp Business Cloud API (sandbox default)
- **Calendar:** Google Calendar, Outlook, Calendly hooks (sandbox default)

## Delivery states

`draft → approved → queued → sending → sent → delivered → read → clicked → replied → meeting → completed`  
Failure paths: `failed`, `cancelled`.

## Stop rules

Campaigns stop immediately on:

- reply received
- meeting booked
- campaign cancelled
- manual stop

## Key APIs

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
- `GET /api/v1/communication/metrics` (Prometheus text)

## Workers

- `communication.process_queue` (every 20s)
- `communication.snapshot_health` (every 180s)

## Related docs

- [sandbox.md](./sandbox.md)
- [oauth.md](./oauth.md)
- [webhooks.md](./webhooks.md)
- [security.md](./security.md)
