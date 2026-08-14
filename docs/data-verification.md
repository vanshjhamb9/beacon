# Data Verification & Coverage Platform

Beacon's self-awareness layer for enrichment quality: completeness, coverage, freshness, trust, conflict resolution, and connector health.

## Position

Collectors → … → Revenue → Lead Enrichment → **Data Verification**

Celery Beat task: `verification.process_enrichments` (every 105s)

Verification reads append-only `enrichment_reports` and writes its own tables. It does not modify Lead Enrichment, Revenue, or Opportunity engines.

## Completeness dimensions (0–100)

- Overall
- Company profile
- Contact
- Leadership
- Technology
- Revenue
- Hiring
- Social profile
- Evidence
- Timeline

## Automatic actions

| Condition | Action |
|-----------|--------|
| Completeness below threshold | `schedule_enrichment_refresh` (recorded in history) |
| Freshness expired | `queue_reenrichment` (triggers enrichment refresh) |
| Trust below threshold / conflicts | `flag_for_review` |

## API

- `GET /api/v1/verification/company/{id}`
- `GET /api/v1/verification/dashboard`
- `GET /api/v1/verification/connectors`
- `GET /api/v1/verification/profile/{id}`
- `POST /api/v1/verification/refresh/{id}`

## Tables (migration 0009)

`verification_reports`, `profile_completeness`, `field_verification`, `coverage_metrics`, `freshness_metrics`, `trust_scores`, `verification_history`, `connector_statistics`, `field_statistics`
