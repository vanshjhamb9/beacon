# Beacon AI

Beacon AI is an AI Opportunity Intelligence Platform for discovering companies showing buying intent across public and enterprise signal sources.

## Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, Redis, Celery, Pydantic v2
- Frontend: Next.js 15, TypeScript, Tailwind, shadcn/ui conventions
- Infrastructure: Docker and Docker Compose

## Run

```bash
docker compose up --build
```

The API is available at `http://localhost:8000`.

- `GET /api/v1/version`
- `GET /api/v1/health`
- `GET /api/v1/sources/health`
- `GET /api/v1/quality/dashboard`
- `GET /api/v1/context/statistics`
- `GET /api/v1/opportunities`
- `GET /api/v1/revenue/opportunities`
- `GET /api/v1/improvement/overview`
- `GET /docs`

## Signal Collection Engine

The worker runs scheduled collectors for Reddit, RSS, Hacker News, and Product Hunt. Collectors normalize internet signals into this event contract:

```json
{
  "source": "reddit",
  "url": "https://example.com/signal",
  "title": "Company signal title",
  "content": "Observed public evidence",
  "published_at": "2026-07-10T09:00:00Z",
  "metadata": {}
}
```

Events are deduplicated by deterministic idempotency key, published into Redis Streams, and persisted by the worker into `raw_events`. Source health is recorded in `source_health`.

## Quality Engine

Every raw event must pass through the Quality Engine before Intelligence consumes it. The engine stores append-only quality reports, stage metrics, rules, audits, and reviewer feedback. It exposes internal quality APIs under `/api/v1/quality`.

## Context Intelligence Engine

Accepted, classified signals are converted into explainable business context and Company DNA. The context APIs live under `/api/v1/context`.

## Opportunity Engine

Validated business context is converted into explainable opportunities with score breakdowns, evidence, lifecycle state, recommendation, conflicts, and delta history. The opportunity APIs live under `/api/v1/opportunities`.

## Revenue Engine

Opportunity and context outputs are converted into deterministic service matches, buyer personas, deal ranges, and sales playbooks for internal revenue prioritization. The revenue APIs live under `/api/v1/revenue`.

## Lead Enrichment Engine

High-priority opportunities with revenue recommendations are enriched into sales-ready lead profiles (company, contacts, people, tech, team, social) for manual outreach review. The enrichment APIs live under `/api/v1/enrichment`.

## Data Verification & Coverage Platform

Enriched profiles are scored for completeness, coverage, freshness, and trust. Operators see Lead Readiness on the company page; dashboard metrics expose connector health and missing-field distribution. The verification APIs live under `/api/v1/verification`.

## Data Acquisition Platform

Compliant public collectors feed the existing pipeline. Acquisition analytics audit connector health, benchmark source yield, alert on failures, and publish daily coverage reports. The acquisition APIs live under `/api/v1/acquisition`.

## Intelligence Improvement Engine

Outcomes and feedback are converted into evaluation metrics, prediction error tracking, experiment history, and optimization recommendations. The improvement APIs live under `/api/v1/improvement`.

## Local Backend (Windows without Docker)

Docker Desktop is optional. On this machine you can run:

1. **Postgres** — local install (create DB/user `beacon` / `beacon_password`)
2. **Redis** — portable server under `.tools/redis` (or any Redis on `6379`)
3. **API**

```powershell
# from repo root
$env:POSTGRES_HOST="127.0.0.1"
$env:REDIS_HOST="127.0.0.1"
$env:PYTHONPATH="$PWD\apps\api;$PWD\apps\worker;$PWD\packages;$PWD"

# start redis if needed
Start-Process ".tools\redis\redis-server.exe" -ArgumentList "--port","6379" -WorkingDirectory ".tools\redis"

# migrate + run API
cd apps\api
python -m alembic -c alembic.ini upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Or use `scripts\start-api.bat`. Optional demo rows: `psql -h 127.0.0.1 -U beacon -d beacon -f scripts\seed_demo_data.sql`.

Verify: `http://localhost:8000/api/v1/health` and `http://localhost:8000/docs`.

## Local Dashboard

```bash
cp apps/dashboard/.env.local.example apps/dashboard/.env.local
npm install
npm run dashboard:dev
```

Operator workspace at `http://localhost:3000` — Home, Opportunities, Companies, Search, Quality, Improvement, Settings. Requires API at `http://localhost:8000`.

## Repository Layout

```text
apps/
  api/        FastAPI application, Alembic, backend Dockerfile
  dashboard/ Next.js dashboard
  worker/    Celery worker
packages/
  ai/         AI workflow foundation
  collectors/ Plugin collectors and event pipeline
  context_engine/ Explainable business context and Company DNA
  intelligence_improvement/ Outcome-driven learning and optimization recommendations
  collectors/ Public signal collectors and extraction quality
  data_acquisition/ Connector audit, benchmarking, alerts, daily reports
  data_verification/ Enrichment quality, coverage, freshness, and trust
  lead_enrichment/ Sales-ready lead enrichment from lawful public sources
  opportunity_engine/ Evidence-backed opportunity decisions
  quality_engine/ Trusted signal validation and scoring
  revenue_engine/ Deterministic service matching and sales playbooks
  scoring/
  shared/
infra/
docs/
tests/
```
