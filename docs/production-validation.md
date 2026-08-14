# Production Validation (PRRV v1) — Sprint 21

Scoring version: `prrv-v1`  
Outreach gate: readiness score **≥ 90**

## Purpose

Make Beacon operationally trustworthy: observable campaigns, measurable revenue, detectable failures, recoverable workflows — without redesigning engines.

## Package

`packages/production_validation/`

- health · validators · metrics · alerts · audit · diagnostics · reporting · pipelines

## API

- `GET /api/v1/production-validation/report`
- `POST /api/v1/production-validation/refresh`
- `GET /api/v1/production-validation/health`
- `GET /api/v1/production-validation/revenue`
- `GET /api/v1/production-validation/alerts`
- `GET /api/v1/production-validation/playbooks`
- `GET /api/v1/production-validation/campaigns/monitoring`
- `GET /api/v1/production-validation/lead-readiness/{company_id}`

## Dashboard

- `/production-health`
- `/revenue-dashboard`

## Migration

`20260723_0022` — snapshots, alerts, lead readiness scores (append-only)

## Worker

`production_validation.refresh_report` @ 120s

## CI

`.github/workflows/ci.yml` + `Makefile` quality gates
