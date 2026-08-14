# Global Opportunity Acquisition Platform (GOAP v1)

**Version:** `goap-v1`  
**Migration:** `20260724_0027` (0026 reserved for Client Execution / AEP)

## Purpose

Beacon stops being a lead collector and becomes an **Opportunity Intelligence Platform**: discover companies most likely to buy software *today*, with every connector scored and competing.

## Architecture

Compose-only package `packages/global_opportunity_acquisition/` with connectors, collector manager, normalizers, deduplication, company resolution, intent/technology/website/job/funding/procurement/community/review intelligence, opportunity graph, source scoring, freshness, benchmarking, analytics, pipeline, and services.

## Compliance

- Public information only  
- Respect robots.txt and platform ToS  
- Licensed connectors (e.g. Crunchbase) stay **pending credentials**  
- Interface-only adapters for sources that disallow unsupported crawling (G2, Clutch, etc.)  
- No GPT dependency · deterministic · append-only  

## API

Prefix: `/api/v1/opportunity-acquisition/`

dashboard · connectors · connectors/{id} · companies/{id}/graph · website · technology · funding · hiring · reviews · community · benchmarks · freshness · analytics · daily-report · refresh

## Workers

`collector.refresh_sources` · `score_sources` · `build_graph` · `update_benchmarks` · `detect_new_intent` · `refresh_websites` · `refresh_jobs` · `refresh_reviews` · `refresh_funding` · `daily_report`

## Dashboard

`/opportunity-acquisition` — Global Opportunity Acquisition workspace
