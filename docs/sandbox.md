# Sandbox Mode

Sandbox is mandatory for validating outreach workflows.

## What it simulates

- Email send / draft / delivery / bounce-style failure
- WhatsApp send / delivery / read / reply
- Calendar booking / meeting detection
- Campaign stop on reply or meeting
- Conversation Center timeline updates
- Outcome stages (`replied`, `meeting_scheduled`) when company/opportunity IDs are provided

## How to run

1. Keep `COMMUNICATION_MODE=sandbox` and `ALLOW_PRODUCTION_SEND=false`
2. Approve a campaign in Campaign Intelligence
3. `POST /api/v1/communication/sandbox/send` or use **Campaign Execution** / **Communication** in the dashboard
4. Optionally `POST /api/v1/communication/sandbox/meeting`
5. Or run `POST /api/v1/qa/e2e/sandbox` from **Test Center**

## Guarantee

No production provider credentials are required to validate the full Beacon outreach loop.
