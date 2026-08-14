# Sprint M2 Engineering Report — Revenue Data Recovery & Intelligence (RDI v1)

**Date:** 2026-07-24  
**Objective:** Transform Beacon from 404 random companies into a recovery pipeline that produces sales-ready, evidence-attributed companies the founder can contact confidently.

## Verdict

RDI v1 (`rdi-v1`) delivers an evidence-first recovery loop: identity → website → fake elimination → contacts → opportunity validation → intent → concrete service recommendations → one-page dossier → quality gates → Revenue Hunter. No new AI. No redesign. Data quality only.

## North-star founder experience

> I open Beacon at 9:00 AM. I see ~40 companies. Each has a real identity, clear evidence, a business need, public contact paths, a recommended service, a believable deal size, and a reason to contact today.

If Beacon cannot answer those questions, the company never reaches the founder.

## Compliance

| Rule | Status |
|---|---|
| No new AI modules | ✅ |
| No new dashboards for founders (engineering QA only) | ✅ `/revenue-data-recovery` internal QA |
| No redesign | ✅ compose-only package |
| Never fabricate contacts / identity | ✅ `AttributedValue` + UNKNOWN |
| Everything attributed | ✅ source + evidence on every recovered field |
| Append-only DB | ✅ `20260724_0032` |
| Backward compatible with PH / SRE | ✅ regression contracts |

## Package

`packages/revenue_data_recovery/`

| Engine | Phase | Role |
|---|---|---|
| IdentityRecoveryEngine | 1 | Recover legal name, website, domain, country, industry, category, description, LinkedIn, employees |
| WebsiteRecoveryEngine | 2 | Canonical homepage; reject 404/parked/spam/GitHub repos/Medium/dev.to |
| FakeCompanyEliminationEngine | 3 | Reject repos, libraries, RSS titles, usernames, communities (composes PH admission) |
| ContactRecoveryEngine | 4 | Public Founder/CEO/CTO/… contacts only; never invent |
| OpportunityValidationEngine | 5 | Why collected + buying/tech/business/hiring/funding/growth/pain |
| IntentIntelligenceEngine | 6 | Deterministic scoring across hiring/AI/cloud/CRM/LLM corpus |
| RevenueRecommendationEngine | 7 | Concrete multi-service pitches (never bare “AI Automation”) |
| RevenueDossierBuilder | 8 | One-page sales dossier |
| RecoveryQueueEngine | 9 | NEW → … → SALES READY → REVENUE HUNTER |
| DailyRecoveryWorker | 10 | Batch recover old companies |
| QualityGateEngine | 11 | Identity + website + business + intent + trust + ≥1 contact path |
| RecoveryMetricsEngine | 12 | Internal QA KPIs |

Pipeline: `RevenueDataRecoveryPipeline.evaluate(payload) → RdiSnapshot`

## Migration

`20260724_0032` (revises `20260724_0031`)

Tables: `rdi_snapshots`, `rdi_recovery_queue`, `rdi_dossiers`, `rdi_metrics_snapshots`

## API

`/api/v1/revenue-data-recovery/*`

- `GET /company/{id}` — latest RDI snapshot
- `POST /company/{id}/evaluate` — recover + persist
- `GET /company/{id}/dossier` — one-page dossier
- `GET /queue` — recovery queue
- `GET /founder-queue` — sales-ready founder surface (40–60)
- `GET /dashboard` — rollup counts
- `GET /qa` — internal QA metrics
- `POST /process-pending` — batch recovery

## Worker

- `revenue_data_recovery.process_pending` @ 125s (before SRE @ 130s)
- `revenue_data_recovery.daily_report` @ 86400s

## UI

| Surface | Change |
|---|---|
| RDI QA | `/revenue-data-recovery` engineering metrics + queue + founder preview |
| Sidebar | “RDI Recovery” nav entry |

## Tests

`tests/revenue_data_recovery/` — **547 passed**

Coverage: identity, website, fake detection, contacts, opportunity validation, intent weights, recommendations, quality gates, dossier, queue, daily worker, metrics, performance (500 &lt; 5s), migration, API, worker, dashboard, PH/SRE regression.

## Success criteria (live targets)

| KPI | Current (pre-RDI) | Target | Engine support |
|---|---:|---:|---|
| Companies | 404 | 500+ | daily worker |
| Identity Complete | 1 | 450+ | identity recovery |
| Website Verified | 155 | 450+ | website recovery |
| Fake Companies | 43 | 0 | fake elimination |
| Verified Public Contacts | 0 | 250+ | contact recovery |
| Sales Ready | 0 | 150+ | quality gates + dossier |
| Founder Queue | 0 | 40–60 | founder-queue API |
| Duplicate Rate | 62% | &lt;10% | metrics tracking (compose PH dedupe) |

Live KPI movement requires applying migration `0032` and running `process_pending` / daily recovery against production data.

## Follow-ups

1. Apply Alembic `20260724_0032` in each environment
2. Run `POST /revenue-data-recovery/process-pending?limit=200` over existing companies
3. Wire enricher outputs into `collected_urls` / `public_page` / `goap` attribute bags for higher recovery yield
4. Optionally feed RDI-passed companies into Revenue Hunter automatically
5. Track duplicate % via PH merge engine into `rdi_metrics_snapshots.duplicate_percent`
