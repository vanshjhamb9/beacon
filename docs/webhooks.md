# Webhooks

## Meta WhatsApp

- Verify: `GET /api/v1/communication/webhooks/meta` (`hub.mode`, `hub.verify_token`, `hub.challenge`)
- Ingest: `POST /api/v1/communication/webhooks/meta`
- Signature: `X-Hub-Signature-256` validated with `META_WHATSAPP_APP_SECRET` (`sha256=` HMAC)
- Events: inbound replies, delivery/read statuses, conversation IDs

## Gmail Pub/Sub

- `POST /api/v1/communication/webhooks/gmail`
- History notifications are accepted; workers fetch message bodies with OAuth

## Calendly

- `POST /api/v1/communication/webhooks/calendly`
- `invitee.created` maps to meeting-booked inbound events and can stop campaigns

## Sandbox

Webhook simulator and sandbox providers generate the same inbound event shapes without external callbacks.
