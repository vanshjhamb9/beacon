# OAuth

Communication Gateway uses official OAuth 2.0 authorization-code + refresh flows.

## Google (Gmail + Calendar)

1. Configure `GMAIL_CLIENT_ID` / `GMAIL_CLIENT_SECRET`
2. `POST /api/v1/communication/oauth/authorize` with `provider=gmail` (or `google_calendar`)
3. Complete consent; callback hits `GET /api/v1/communication/oauth/callback`
4. Access + refresh tokens are encrypted with `COMMUNICATION_ENCRYPTION_KEY` and stored in `oauth_connections`

Scopes include Gmail send/modify and Calendar events.

## Microsoft (Graph Mail + Outlook Calendar)

1. Configure `MICROSOFT_CLIENT_ID` / `MICROSOFT_CLIENT_SECRET` / `MICROSOFT_TENANT_ID`
2. Authorize with `provider=microsoft_graph` or `outlook_calendar`
3. Tokens stored encrypted; refresh uses the official token endpoint

## Rules

- Never bypass OAuth for production providers
- Never log raw tokens
- Reconnect by re-running the authorize flow (status can be marked inactive then replaced)
