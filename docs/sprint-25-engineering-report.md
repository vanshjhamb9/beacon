# Sprint 25 Engineering Report — Global Opportunity Acquisition Platform (GOAP v1)

**Date:** 2026-07-24  
**Objective:** Transform Beacon from a lead collector into the world's best Opportunity Intelligence Platform.

## Verdict

Sprint 25 delivers compose-only **GOAP** (`goap-v1`): connector contracts for 40+ sources, opportunity intent detection, website/technology/hiring/funding/community/review/procurement intelligence, append-only opportunity graph, source benchmarking, freshness scoring, analytics + daily report, API, workers, and interactive dashboard.

**Migration note:** Spec listed `20260724_0026`, but that revision is already owned by Client Execution (AEP). GOAP ships as **`20260724_0027`** to keep the database append-compatible. AEP remains unchanged.

## Architecture

```text
Existing collectors / companies (compose signals)
        │
        ▼
GlobalOpportunityAcquisitionPipeline (goap-v1)
  Connectors · Normalize · Dedupe · Resolve
  Intent · Tech · Website · Jobs · Funding
  Community · Reviews · Procurement
  Graph · Freshness · Benchmarks · Analytics
        │
        ▼
Append-only GOAP tables + /opportunity-acquisition workspace
```

## Compliance

| Rule | Status |
|---|---|
| No redesign of existing packages | ✅ |
| Compose only / append-only / deterministic | ✅ |
| No GPT | ✅ |
| No private scraping / ToS-safe adapters | ✅ |
| Licensed connectors disabled until credentials | ✅ |

## Deliverables

| Area | Status |
|---|---|
| `packages/global_opportunity_acquisition/` | ✅ |
| API `/opportunity-acquisition/*` | ✅ |
| Migration `20260724_0027` | ✅ |
| Workers (10 collector.* tasks) | ✅ |
| Dashboard `/opportunity-acquisition` | ✅ |
| Source benchmarking + freshness | ✅ |
| Opportunity graph | ✅ |

## Tests

Suite: `tests/global_opportunity_acquisition/` — 120+ covering unit, pipeline, API, migration, dashboard, integration, determinism, graph, dedupe, benchmarks, coverage, performance (500 companies &lt; 5s, 500 graphs &lt; 5s, 1000 dedupes &lt; 3s).

## Follow-ups

1. Apply Alembic `20260724_0027`  
2. Supply licensed credentials for Crunchbase when available  
3. Wire compliant review providers for G2/Capterra when licensed  
