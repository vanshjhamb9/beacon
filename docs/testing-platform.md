# Testing Platform / Production QA

`packages/testing_platform/` provides system health scoring, probe catalogs, and the sandbox end-to-end pipeline.

## Capabilities

- Component probes: API, workers, database, Redis, queues, LLM, campaigns, communication, collectors, pipeline, providers, webhooks, dashboard
- Overall system score + recommendations
- Sandbox E2E: sales package → campaign approve → sandbox send → simulated reply → meeting → conversation summary
- Persisted QA snapshots and sandbox scenario results

## APIs

- `GET /api/v1/qa/health`
- `GET /api/v1/qa/dashboard`
- `POST /api/v1/qa/e2e/sandbox`
- `GET /api/v1/system-health`

## Dashboard

- **QA** — component scores and recommendations
- **System Health** — live overall score
- **Test Center** — run sandbox E2E

## Success criterion

Beacon can execute a complete campaign in sandbox mode from lead package through simulated reply and meeting booking without any production provider credentials.
