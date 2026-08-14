# Security

## Secrets at rest

`SecretBox` (`packages/communication_gateway/security/crypto.py`) derives a Fernet key from `COMMUNICATION_ENCRYPTION_KEY` and encrypts:

- OAuth access tokens
- OAuth refresh tokens
- Provider secrets (`provider_secrets`)

## Runtime rules

- No secrets in structured logs (use `SecretBox.redact`)
- Production send double-gated (`COMMUNICATION_MODE` + `ALLOW_PRODUCTION_SEND`)
- Meta webhook signatures verified with HMAC-SHA256
- Sandbox is the default for all environments until operators opt in

## Observability

- Correlation IDs via `X-Request-ID` (`RequestTracingMiddleware`)
- Prometheus metrics at `/api/v1/communication/metrics`
- Health snapshots persisted for QA dashboards
