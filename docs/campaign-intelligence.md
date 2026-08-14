# Campaign Intelligence Engine (Sprint 14)

Transforms approved Sales Copilot packages into executable outreach **plans**.

## Boundaries

- Consumes: Sales Package, Decision Discovery, Revenue, Opportunity, Verification, Outcome Intelligence
- Does **not** send email, WhatsApp, LinkedIn, calendar, or phone messages
- Provider integrations belong to Sprint 15

## Package

`packages/campaign_intelligence/`

- Campaign planner (channels, sequence, follow-ups, delays, priority, confidence)
- Channel catalog with capabilities/constraints (`delivery_ready=false`)
- Message selection from Sales Copilot draft variants
- Approval workflow with immutable audit trail
- Provider-agnostic scheduling rules (business hours, timezone, rate limits, holidays)

## API

- `GET /api/v1/campaigns`
- `GET /api/v1/campaigns/{id}`
- `POST /api/v1/campaigns/create/{company_id}`
- `POST /api/v1/campaigns/approve/{id}`
- `POST /api/v1/campaigns/pause/{id}`
- `POST /api/v1/campaigns/cancel/{id}`
- `GET /api/v1/campaigns/dashboard`

## Database

Migration `20260720_0014`:

- `campaigns`, `campaign_steps`, `campaign_schedules`, `campaign_channels`
- `campaign_approvals`, `campaign_execution_logs`, `campaign_templates`, `campaign_audit`

## Dashboard

Sidebar **Campaigns** with Pipeline, Calendar, Approvals, Schedules, Analytics, Company Timeline.
