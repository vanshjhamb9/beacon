# Data Acquisition Platform

Maximizes Beacon opportunity coverage from compliant public sources without changing downstream intelligence engines.

## Collectors

| Source | Type | Notes |
|--------|------|-------|
| reddit | JSON API | new + hot listings, richer metadata |
| rss | RSS/Atom | TechCrunch, Verge, VentureBeat, SaaStr |
| hacker_news | RSS | frontpage + hiring/funding/launch query feed |
| product_hunt | RSS | public product feed |
| github_trending | GitHub Search API | public, rate-limited |
| indie_hackers | RSS | public feed |
| sec_edgar | Atom | SEC current filings |
| devto | RSS | public developer feed |

## Acquisition analytics

Package: `packages/data_acquisition/`

- Connector audit (coverage, failure, duplicates, yield)
- Benchmarking (high-value opportunity contribution)
- Alerting (down / degraded / zero yield)
- Daily reports (companies, opportunities, missing-data trends)

## API (additive; existing routes unchanged)

- `GET /api/v1/acquisition/dashboard`
- `GET /api/v1/acquisition/audit`
- `GET /api/v1/acquisition/benchmarks`
- `GET /api/v1/acquisition/alerts`
- `GET /api/v1/acquisition/reports/daily`
- `POST /api/v1/acquisition/reports/daily/generate`

## Workers

- `acquisition.monitor_connectors` every 120s
- `acquisition.generate_daily_report` daily
- Existing `collectors.collect_source` records `collector_runs` for metrics

## Migration

`20260719_0010` — `collector_runs`, `connector_alerts`, `acquisition_daily_reports`, `connector_benchmark_snapshots`
